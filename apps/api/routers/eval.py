import os
import json
import time
from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from schemas.pipeline import EvaluationMetrics, RawMeetingInput
from services.pipeline_orchestrator import PipelineOrchestrator
from services.extractor import TaskExtractor
from database import get_connection
from config import settings

router = APIRouter(prefix="/api/eval", tags=["evaluation"])

@router.get("/metrics", response_model=EvaluationMetrics)
def get_evaluation_metrics(workspace_id: str = "ws_default"):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as total FROM task_candidates WHERE workspace_id = ?", (workspace_id,))
    total = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) as approved FROM task_candidates WHERE workspace_id = ? AND status IN ('approved', 'pushed')", (workspace_id,))
    approved = cursor.fetchone()["approved"]

    cursor.execute("SELECT COUNT(*) as rejected FROM task_candidates WHERE workspace_id = ? AND status = 'rejected'", (workspace_id,))
    rejected = cursor.fetchone()["rejected"]

    cursor.execute("SELECT COUNT(DISTINCT task_id) as edited FROM feedback_logs WHERE workspace_id = ? AND action LIKE 'edited_%'", (workspace_id,))
    edited = cursor.fetchone()["edited"]

    cursor.execute("SELECT AVG(confidence) as avg_conf FROM task_candidates WHERE workspace_id = ?", (workspace_id,))
    avg_conf_row = cursor.fetchone()["avg_conf"]
    avg_conf = round(float(avg_conf_row), 3) if avg_conf_row else 0.85

    conn.close()

    acceptance_rate = round(approved / total, 3) if total > 0 else 0.0
    reject_rate = round(rejected / total, 3) if total > 0 else 0.0
    edit_rate = round(edited / total, 3) if total > 0 else 0.0

    return EvaluationMetrics(
        total_candidates=total,
        approved_count=approved,
        rejected_count=rejected,
        edited_count=edited,
        acceptance_rate=acceptance_rate,
        edit_rate=reject_rate,
        avg_confidence=avg_conf
    )

def _evaluate_cases(cases, workspace_id="ws_default"):
    total_expected = 0
    total_extracted = 0
    true_positives = 0
    correct_owners = 0
    correct_dates = 0
    negative_phrases_tested = 0
    negative_phrases_correctly_rejected = 0

    for case in cases:
        processed = PipelineOrchestrator.process_meeting(
            RawMeetingInput(
                title=case["title"],
                transcript_or_notes=case["transcript"],
                meeting_date=case["meeting_date"],
                timezone="UTC",
                target_tool="mock",
                workspace_id=workspace_id
            )
        )

        expected_tasks = case["expected_tasks"]
        extracted_tasks = processed.candidates
        negative_phrases = case.get("negative_phrases", [])

        total_expected += len(expected_tasks)
        total_extracted += len(extracted_tasks)

        for neg in negative_phrases:
            negative_phrases_tested += 1
            hallucinated = any(neg.lower() in cand.title.lower() or neg.lower() in cand.description.lower() for cand in extracted_tasks)
            if not hallucinated:
                negative_phrases_correctly_rejected += 1

        matched_candidate_ids = set()
        for exp in expected_tasks:
            matched_cand = None
            for cand in extracted_tasks:
                if cand.id in matched_candidate_ids:
                    continue
                if any(kw.lower() in cand.title.lower() or kw.lower() in cand.supporting_quote.lower() for kw in exp["keywords"]):
                    matched_cand = cand
                    matched_candidate_ids.add(cand.id)
                    break

            if matched_cand:
                true_positives += 1
                
                # Check owner accuracy
                if exp.get("expected_owner"):
                    if matched_cand.resolved_owner_name and exp["expected_owner"].lower() in matched_cand.resolved_owner_name.lower():
                        correct_owners += 1
                elif exp.get("expected_owner") is None:
                    if matched_cand.resolved_owner_id is None or matched_cand.is_ambiguous:
                        correct_owners += 1

                # Check date accuracy
                if exp.get("expected_date"):
                    if matched_cand.resolved_due_date == exp["expected_date"]:
                        correct_dates += 1
                elif not exp.get("expected_date"):
                    correct_dates += 1

    precision = round(true_positives / total_extracted, 3) if total_extracted > 0 else 0.0
    recall = round(true_positives / total_expected, 3) if total_expected > 0 else 0.0
    f1 = round(2 * (precision * recall) / (precision + recall), 3) if (precision + recall) > 0 else 0.0
    owner_acc = round(correct_owners / true_positives, 3) if true_positives > 0 else 0.0
    date_acc = round(correct_dates / true_positives, 3) if true_positives > 0 else 0.0
    neg_rejection = round(negative_phrases_correctly_rejected / negative_phrases_tested, 3) if negative_phrases_tested > 0 else 1.0

    return {
        "cases_evaluated": len(cases),
        "total_expected_actions": total_expected,
        "total_extracted_candidates": total_extracted,
        "true_positives": true_positives,
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "owner_accuracy": owner_acc,
        "due_date_accuracy": date_acc,
        "negative_discussion_rejection_rate": neg_rejection
    }

@router.post("/run-golden-benchmark")
def run_golden_benchmark(
    dataset: str = "all",
    gemini_api_key: Optional[str] = None
):
    start_time = time.time()
    
    # Configure API key
    original_key = settings.gemini_api_key
    if isinstance(gemini_api_key, str) and gemini_api_key.strip():
        settings.gemini_api_key = gemini_api_key.strip()
    
    if not settings.gemini_api_key:
        raise HTTPException(
            status_code=400,
            detail="GEMINI_API_KEY is required to run model extraction benchmark. "
                   "Pass 'gemini_api_key' in request or set GEMINI_API_KEY environment variable."
        )

    effective_engine = f"{settings.gemini_model} (LLM structured outputs)"

    golden_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tests", "golden_transcripts")
    expanded_file = os.path.join(golden_dir, "expanded_benchmark.json")
    unseen_file = os.path.join(golden_dir, "unseen_evaluation_set.json")

    expanded_cases = []
    unseen_cases = []

    if os.path.exists(expanded_file):
        with open(expanded_file, "r", encoding="utf-8") as f:
            expanded_cases = json.load(f)

    if os.path.exists(unseen_file):
        with open(unseen_file, "r", encoding="utf-8") as f:
            unseen_cases = json.load(f)

    results = {
        "status": "completed",
        "engine_used": effective_engine,
        "dataset_requested": dataset,
    }

    if dataset == "expanded":
        results.update(_evaluate_cases(expanded_cases, "ws_default"))
    elif dataset == "unseen":
        results.update(_evaluate_cases(unseen_cases, "ws_default"))
    else: # all (40 cases)
        exp_res = _evaluate_cases(expanded_cases, "ws_default")
        uns_res = _evaluate_cases(unseen_cases, "ws_default")

        tot_exp = exp_res["total_expected_actions"] + uns_res["total_expected_actions"]
        tot_ext = exp_res["total_extracted_candidates"] + uns_res["total_extracted_candidates"]
        tot_tp = exp_res["true_positives"] + uns_res["true_positives"]
        cases_count = exp_res["cases_evaluated"] + uns_res["cases_evaluated"]

        prec = round(tot_tp / tot_ext, 3) if tot_ext > 0 else 0.0
        rec = round(tot_tp / tot_exp, 3) if tot_exp > 0 else 0.0
        f1 = round(2 * (prec * rec) / (prec + rec), 3) if (prec + rec) > 0 else 0.0
        owner_acc = round(
            (exp_res["owner_accuracy"] * exp_res["true_positives"] + uns_res["owner_accuracy"] * uns_res["true_positives"]) / (tot_tp or 1),
            3
        )
        date_acc = round(
            (exp_res["due_date_accuracy"] * exp_res["true_positives"] + uns_res["due_date_accuracy"] * uns_res["true_positives"]) / (tot_tp or 1),
            3
        )

        results.update({
            "cases_evaluated": cases_count,
            "total_expected_actions": tot_exp,
            "total_extracted_candidates": tot_ext,
            "true_positives": tot_tp,
            "precision": prec,
            "recall": rec,
            "f1_score": f1,
            "owner_accuracy": owner_acc,
            "due_date_accuracy": date_acc,
            "negative_discussion_rejection_rate": round(
                (exp_res["negative_discussion_rejection_rate"] + uns_res["negative_discussion_rejection_rate"]) / 2, 3
            ),
            "breakdown": {
                "expanded_set_30": exp_res,
                "unseen_set_10": uns_res
            }
        })

    results["execution_duration_seconds"] = round(time.time() - start_time, 2)

    # Restore settings
    if gemini_api_key:
        settings.gemini_api_key = original_key

    return results

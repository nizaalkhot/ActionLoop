import uuid
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional
from schemas.pipeline import RawMeetingInput, CandidateTask, MeetingResponse
from services.normalizer import TranscriptNormalizer
from services.extractor import TaskExtractor
from services.resolver import EntityResolver
from services.deduplicator import TaskDeduplicator
from services.integrations.mock_provider import MockLinearProvider
from services.integrations.linear import LinearProvider
from database import get_connection

class PipelineOrchestrator:
    @classmethod
    def process_meeting(cls, input_data: RawMeetingInput) -> MeetingResponse:
        ws_id = input_data.workspace_id or "ws_default"

        # 1. Normalize
        norm_result = TranscriptNormalizer.clean_and_parse(
            raw_text=input_data.transcript_or_notes,
            default_date=input_data.meeting_date,
            default_tz=input_data.timezone
        )
        clean_transcript = norm_result["clean_transcript"]
        detected_speakers = norm_result["detected_speakers"]
        anchor_date = norm_result["anchor_date"]
        tz = norm_result["timezone"]

        # 2. Extract Tasks
        raw_candidates = TaskExtractor.extract_tasks(
            clean_transcript=clean_transcript,
            meeting_title=input_data.title
        )

        # 3. Provider setup (get members & open tickets)
        provider = LinearProvider() if input_data.target_tool == "linear" else MockLinearProvider()
        try:
            workspace_users = provider.get_members()
        except Exception:
            workspace_users = MockLinearProvider().get_members()

        try:
            open_tickets = provider.get_open_tickets(input_data.project_id)
        except Exception:
            open_tickets = MockLinearProvider().get_open_tickets(input_data.project_id)

        # 4. Resolve & Deduplicate
        meeting_id = f"mtg_{uuid.uuid4().hex[:10]}"
        now_iso = datetime.now(timezone.utc).isoformat()

        candidate_tasks: List[CandidateTask] = []
        conn = get_connection()
        cursor = conn.cursor()

        # Save meeting row with workspace_id and retention
        cursor.execute(
            """
            INSERT INTO meetings (id, workspace_id, title, meeting_date, timezone, transcript_raw, transcript_clean, detected_speakers, retention_days, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                meeting_id,
                ws_id,
                input_data.title,
                anchor_date,
                tz,
                input_data.transcript_or_notes,
                clean_transcript,
                json.dumps(detected_speakers),
                input_data.retention_days,
                now_iso
            )
        )

        for item in raw_candidates:
            task_id = f"tsk_{uuid.uuid4().hex[:10]}"
            raw_owner = item.get("raw_owner")
            raw_date = item.get("raw_due_date")
            title = item.get("title", "Untitled task")
            description = item.get("description", "")
            quote = item.get("supporting_quote", "")
            base_confidence = float(item.get("confidence", 0.85))
            task_type = item.get("task_type", "feature")

            # Resolve owner with ambiguity detection
            owner_id, owner_name, owner_conf, is_ambiguous = EntityResolver.resolve_owner(
                raw_owner=raw_owner,
                workspace_users=workspace_users
            )

            # Resolve due date with timezone anchor
            resolved_date, date_conf = EntityResolver.resolve_due_date(
                raw_date_str=raw_date,
                anchor_date_str=anchor_date,
                timezone_str=tz
            )

            # Check duplicate against existing open tickets with contrast awareness
            dup_ticket, dup_score = TaskDeduplicator.check_duplicate(
                candidate_title=title,
                existing_tickets=open_tickets,
                threshold=0.60
            )

            cand = CandidateTask(
                id=task_id,
                workspace_id=ws_id,
                meeting_id=meeting_id,
                title=title,
                description=description,
                raw_owner=raw_owner,
                resolved_owner_id=owner_id,
                resolved_owner_name=owner_name,
                owner_confidence=owner_conf,
                raw_due_date=raw_date,
                resolved_due_date=resolved_date,
                date_confidence=date_conf,
                supporting_quote=quote,
                confidence=base_confidence,
                task_type=task_type,
                status="pending",
                possible_duplicate_of=dup_ticket,
                duplicate_score=dup_score,
                is_ambiguous=is_ambiguous
            )
            candidate_tasks.append(cand)

            # Insert into DB
            cursor.execute(
                """
                INSERT INTO task_candidates (
                    id, workspace_id, meeting_id, title, description, raw_owner, resolved_owner_id, resolved_owner_name,
                    owner_confidence, raw_due_date, resolved_due_date, date_confidence, supporting_quote,
                    confidence, task_type, status, possible_duplicate_of, duplicate_score, is_ambiguous, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    cand.id, cand.workspace_id, cand.meeting_id, cand.title, cand.description, cand.raw_owner,
                    cand.resolved_owner_id, cand.resolved_owner_name, cand.owner_confidence,
                    cand.raw_due_date, cand.resolved_due_date, cand.date_confidence,
                    cand.supporting_quote, cand.confidence, cand.task_type, cand.status,
                    cand.possible_duplicate_of, cand.duplicate_score, 1 if cand.is_ambiguous else 0, now_iso
                )
            )

        conn.commit()
        conn.close()

        return MeetingResponse(
            id=meeting_id,
            workspace_id=ws_id,
            title=input_data.title,
            meeting_date=anchor_date,
            timezone=tz,
            transcript_clean=clean_transcript,
            detected_speakers=detected_speakers,
            candidates=candidate_tasks,
            created_at=now_iso
        )

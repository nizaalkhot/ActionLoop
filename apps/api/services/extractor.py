import json
import requests
from typing import Dict, List, Optional
from config import settings

EXTRACTION_SYSTEM_PROMPT = """You are an expert project management intelligence engine.
Your task is to analyze meeting notes or transcripts and extract only real, actionable tasks with clear commitments.

CRITICAL RULES:
1. DISTINGUISH COMMITMENTS FROM DISCUSSION:
   - Valid Task: "I'll refactor the authentication middleware by Friday." -> Actionable commitment.
   - Valid Task: "Priya, please review the PR for the checkout flow today." -> Actionable request.
   - INVALID (Ignore): "We should probably think about AI search in Q3." -> Discussion / idea, NOT a task.
   - INVALID (Ignore): "Our onboarding UX isn't very intuitive." -> Observation, NOT a task.

2. GROUNDING (NO HALLUCINATIONS):
   - Every candidate MUST have an exact verbatim `supporting_quote` copied directly from the transcript.
   - If you cannot point to an exact quote where someone committed or was assigned, DO NOT invent the task.

3. STRUCTURE:
   - title: concise, imperative action title (e.g. "Refactor auth middleware to support refresh tokens")
   - description: brief context or details mentioned in the meeting
   - raw_owner: the person assigned or committing (as spoken, e.g. "Alex", "Priya", "I")
   - raw_due_date: temporal expression as spoken (e.g. "by Friday", "tomorrow EOD", "next sprint", or null)
   - supporting_quote: the exact sentence from the transcript
   - task_type: one of ["feature", "bug", "chore", "follow_up"]
   - confidence: float between 0.0 and 1.0 based on how clear and explicit the commitment was
"""

EXTRACTION_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "tasks": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "title": {"type": "STRING"},
                    "description": {"type": "STRING"},
                    "raw_owner": {"type": "STRING"},
                    "raw_due_date": {"type": "STRING"},
                    "supporting_quote": {"type": "STRING"},
                    "task_type": {"type": "STRING", "enum": ["feature", "bug", "chore", "follow_up"]},
                    "confidence": {"type": "NUMBER"}
                },
                "required": ["title", "supporting_quote", "task_type", "confidence"]
            }
        }
    },
    "required": ["tasks"]
}

class TaskExtractor:
    @classmethod
    def extract_tasks(cls, clean_transcript: str, meeting_title: str = "Meeting", api_key: Optional[str] = None) -> List[Dict]:
        """
        Extracts action items exclusively using Gemini Structured Outputs (JSON Schema).
        No heuristic fallback.
        """
        key = api_key or settings.gemini_api_key
        if not key:
            raise ValueError(
                "GEMINI_API_KEY is required for task extraction. "
                "Please configure GEMINI_API_KEY in your environment or settings."
            )

        model_name = settings.gemini_model or "gemini-flash-latest"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={key}"
        
        prompt = f"""Meeting Title: {meeting_title}

Transcript:
\"\"\"
{clean_transcript}
\"\"\"

Extract all concrete action items following the system guidelines strictly. Return JSON."""

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "systemInstruction": {"parts": [{"text": EXTRACTION_SYSTEM_PROMPT}]},
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseSchema": EXTRACTION_SCHEMA,
                "temperature": 0.1
            }
        }

        resp = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        raw_json_str = data["candidates"][0]["content"]["parts"][0]["text"]
        parsed = json.loads(raw_json_str)
        return parsed.get("tasks", [])

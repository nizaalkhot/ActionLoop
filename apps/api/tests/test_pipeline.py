import pytest
from services.normalizer import TranscriptNormalizer
from services.extractor import TaskExtractor
from services.pipeline_orchestrator import PipelineOrchestrator
from schemas.pipeline import RawMeetingInput
from database import init_db

def test_normalizer():
    raw_vtt = """WEBVTT

00:01.000 --> 00:04.000
<v Alex>Alex: I will write the unit tests today.

00:05.000 --> 00:08.000
Priya: I'll review them by tomorrow.
"""
    res = TranscriptNormalizer.clean_and_parse(raw_vtt, default_date="2026-11-04")
    assert "Alex" in res["detected_speakers"]
    assert "Priya" in res["detected_speakers"]
    assert "WEBVTT" not in res["clean_transcript"]
    assert "-->" not in res["clean_transcript"]

def test_full_pipeline_orchestration():
    init_db()
    transcript = """Marcus: Let's do standup.
Alex: I'll refactor the authentication middleware by Friday.
Priya: I will fix the mobile navigation drawer by tomorrow.
Sarah: Maybe we could migrate to Tailwind v4 someday.
Marcus: Okay thanks everyone."""

    input_data = RawMeetingInput(
        title="Engineering Standup",
        transcript_or_notes=transcript,
        meeting_date="2026-11-04",
        timezone="UTC",
        target_tool="mock"
    )

    result = PipelineOrchestrator.process_meeting(input_data)
    assert len(result.candidates) >= 2
    
    # Check that Alex's task resolved
    alex_task = next((t for t in result.candidates if "auth" in t.title.lower()), None)
    assert alex_task is not None
    assert alex_task.resolved_owner_name == "Alex Chen"
    assert alex_task.resolved_due_date == "2026-11-06" # Friday after Nov 4
    assert "I'll refactor the authentication middleware by Friday" in alex_task.supporting_quote

    # Notice LIN-101 is already in existing tickets with title "Refactor authentication middleware for JWT refresh tokens"
    # Deduplicator should have caught it!
    assert alex_task.possible_duplicate_of is not None
    assert "LIN-101" in alex_task.possible_duplicate_of


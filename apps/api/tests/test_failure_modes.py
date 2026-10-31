import pytest
from database import init_db, get_connection
from services.resolver import EntityResolver
from services.deduplicator import TaskDeduplicator
from services.crypto import encrypt_token, decrypt_token
from services.integrations.mock_provider import MockLinearProvider
from routers.tasks import batch_push_tasks
from schemas.pipeline import PushTasksRequest, RawMeetingInput
from services.pipeline_orchestrator import PipelineOrchestrator

@pytest.fixture(autouse=True)
def setup_db():
    init_db()

def test_same_first_name_collision_ambiguity():
    """
    When multiple attendees share a first name (Alex Chen vs Alex Miller)
    and the speaker context does not disambiguate, resolver MUST NOT guess.
    It should return is_ambiguous=True, owner=None, and confidence <= 0.40.
    """
    users = [
        {"id": "usr_alex_chen", "name": "Alex Chen", "email": "alex.chen@co.com"},
        {"id": "usr_alex_miller", "name": "Alex Miller", "email": "alex.miller@co.com"},
        {"id": "usr_priya", "name": "Priya Sharma", "email": "priya@co.com"},
    ]

    uid, uname, conf, is_ambiguous = EntityResolver.resolve_owner("Alex", users, speaker_context=None)
    assert is_ambiguous is True
    assert uid is None
    assert conf <= 0.40

    # If full name is spoken, it should match unambiguously
    uid, uname, conf, is_ambiguous = EntityResolver.resolve_owner("Alex Miller", users)
    assert is_ambiguous is False
    assert uid == "usr_alex_miller"
    assert conf >= 0.95

def test_timezone_boundary_resolution():
    """
    Meeting on Friday 11:30 PM (2026-11-06T23:30:00-05:00).
    'tomorrow' must anchor to Saturday (2026-11-07), not jump to the wrong day.
    'by next Monday' must resolve to 2026-11-09.
    """
    anchor_str = "2026-11-06T23:30:00-05:00"
    
    res_tomorrow, conf1 = EntityResolver.resolve_due_date("tomorrow", anchor_str)
    assert res_tomorrow == "2026-11-07"
    assert conf1 > 0.9

    res_monday, conf2 = EntityResolver.resolve_due_date("by next Monday", anchor_str)
    assert res_monday == "2026-11-09"

def test_double_push_strict_idempotency():
    """
    Double-clicking push or retrying must return 'already_pushed' and NEVER
    create duplicate tickets in Linear.
    """
    # Create a meeting with an approved task
    input_data = RawMeetingInput(
        title="Idempotency Test Meeting",
        transcript_or_notes="Marcus: Standup.\nPriya: I will update the checkout component today.\nMarcus: Done.",
        meeting_date="2026-11-04",
        timezone="UTC"
    )
    mtg = PipelineOrchestrator.process_meeting(input_data)
    task_id = mtg.candidates[0].id

    # Mark task as approved
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE task_candidates SET status = 'approved' WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

    # First push
    push_req = PushTasksRequest(meeting_id=mtg.id, task_ids=[task_id], target_tool="mock")
    res1 = batch_push_tasks(push_req)
    assert res1.pushed_count == 1
    assert res1.results[0].status == "created"
    ticket_id = res1.results[0].ticket_id

    # Second push (simulating accidental retry or double-click)
    res2 = batch_push_tasks(push_req)
    assert res2.pushed_count == 1
    assert res2.results[0].status == "already_pushed"
    assert res2.results[0].ticket_id == ticket_id

def test_deduplicator_contrast_penalty():
    """
    'Update pricing page' vs 'Update pricing doc' must NOT trigger a duplicate alert.
    'Revise pricing page tiers' vs 'Update pricing page' SHOULD trigger duplicate.
    """
    existing = [
        {"id": "LIN-105", "title": "Update pricing page layout and tiers"}
    ]

    # Different entity: doc vs page
    matched, score = TaskDeduplicator.check_duplicate("Update pricing doc for sales team", existing, threshold=0.60)
    assert matched is None
    assert score < 0.60

    # Paraphrased page update
    matched, score = TaskDeduplicator.check_duplicate("Revise the pricing page layout", existing, threshold=0.60)
    assert matched is not None
    assert "LIN-105" in matched
    assert score >= 0.60

def test_token_encryption():
    """
    Test AES-256 Fernet token encryption & decryption.
    """
    raw_token = "lin_oauth_token_secret_12345"
    encrypted = encrypt_token(raw_token)
    assert encrypted != raw_token
    assert "lin_oauth" not in encrypted
    decrypted = decrypt_token(encrypted)
    assert decrypted == raw_token


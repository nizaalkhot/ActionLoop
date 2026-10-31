import pytest
import hashlib
from database import init_db, get_connection
from schemas.pipeline import RawMeetingInput, PushTasksRequest
from services.pipeline_orchestrator import PipelineOrchestrator
from services.integrations.mock_provider import MockLinearProvider
from routers.tasks import batch_push_tasks

@pytest.fixture(autouse=True)
def setup_db():
    init_db()

def test_lookup_before_retry_prevents_duplicate_on_dropped_response():
    """
    Simulates: Issue was created in Linear/Mock, but client dropped connection
    before DB updated task status.
    Next push attempt MUST lookup by fingerprint and not create a 2nd ticket.
    """
    provider = MockLinearProvider(workspace_id="ws_default")
    
    # 1. Create a task in a meeting
    input_data = RawMeetingInput(
        title="Dropped Connection Test Meeting",
        transcript_or_notes="Sarah: I will upgrade the Redis cluster by Friday.",
        meeting_date="2026-11-04",
        timezone="UTC",
        workspace_id="ws_default"
    )
    mtg = PipelineOrchestrator.process_meeting(input_data)
    task = mtg.candidates[0]

    fingerprint = hashlib.sha256(f"{task.meeting_id}:{task.title}:{task.supporting_quote}".encode()).hexdigest()[:16]

    # 2. Simulate Linear having the issue already created out-of-band with the fingerprint
    created_pm = provider.create_task(
        title=task.title,
        description="Out-of-band created issue",
        task_fingerprint=fingerprint
    )
    original_ticket_id = created_pm["ticket_id"]

    # 3. Client calls batch_push_tasks for the candidate task
    push_req = PushTasksRequest(meeting_id=mtg.id, task_ids=[task.id], target_tool="mock")
    res = batch_push_tasks(push_req)

    # Must match original ticket, and NOT create a new one!
    assert res.pushed_count == 1
    assert res.results[0].ticket_id == original_ticket_id
    assert res.results[0].status == "already_pushed"

    # Verify no second ticket was inserted into existing_tickets for this task
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM existing_tickets WHERE fingerprint = ?", (fingerprint,))
    assert cursor.fetchone()["count"] == 1
    conn.close()

def test_db_level_idempotency_unique_constraint():
    """
    Directly tests that idempotency_keys table rejects duplicate (workspace_id, task_id).
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM idempotency_keys WHERE workspace_id = 'ws_test'")
    conn.commit()

    cursor.execute(
        "INSERT INTO idempotency_keys (id, workspace_id, task_id, ticket_id, ticket_url, fingerprint, created_at) VALUES ('idk_1', 'ws_test', 'tsk_100', 'LIN-999', 'url', 'fp1', 'now')"
    )
    conn.commit()

    # Re-inserting the same (workspace_id, task_id) with INSERT OR IGNORE should be ignored cleanly
    cursor.execute(
        "INSERT OR IGNORE INTO idempotency_keys (id, workspace_id, task_id, ticket_id, ticket_url, fingerprint, created_at) VALUES ('idk_2', 'ws_test', 'tsk_100', 'LIN-999', 'url', 'fp1', 'now')"
    )
    conn.commit()

    cursor.execute("SELECT COUNT(*) as count FROM idempotency_keys WHERE workspace_id = 'ws_test' AND task_id = 'tsk_100'")
    assert cursor.fetchone()["count"] == 1
    conn.close()

import pytest
from fastapi.testclient import TestClient
from main import app
from database import init_db, get_connection
from schemas.pipeline import RawMeetingInput
from services.pipeline_orchestrator import PipelineOrchestrator
from services.job_runner import BackgroundJobRunner

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    init_db()

def test_cross_tenant_isolation_404():
    """
    Verifies that tenant boundaries are strictly enforced.
    Workspace B must never be able to view or edit Workspace A's data.
    """
    # Create meeting and task in Workspace Alpha
    mtg_alpha = PipelineOrchestrator.process_meeting(
        RawMeetingInput(
            title="Alpha Confidential Roadmap",
            transcript_or_notes="Marcus: Secret project kickoff.\nAlex Chen: I will finish the secret prototype by Friday.",
            meeting_date="2026-11-04",
            timezone="UTC",
            workspace_id="ws_alpha"
        )
    )
    task_alpha_id = mtg_alpha.candidates[0].id

    # Create background job in Workspace Alpha
    job_alpha_id = BackgroundJobRunner.create_and_start_job(
        RawMeetingInput(
            title="Alpha Async Processing",
            transcript_or_notes="Priya: I'll test the payment gateway by tomorrow.",
            meeting_date="2026-11-04",
            workspace_id="ws_alpha"
        )
    )

    # 1. Workspace Beta attempts to access Workspace Alpha's meeting
    resp_mtg = client.get(f"/api/meetings/{mtg_alpha.id}", headers={"X-Workspace-ID": "ws_beta"})
    assert resp_mtg.status_code == 404
    assert "not found in workspace" in resp_mtg.json()["detail"].lower()

    # 2. Workspace Beta attempts to modify Workspace Alpha's task
    resp_task = client.patch(
        f"/api/tasks/{task_alpha_id}",
        json={"title": "Hacked Title"},
        headers={"X-Workspace-ID": "ws_beta"}
    )
    assert resp_task.status_code == 404

    # 3. Workspace Beta attempts to query Workspace Alpha's background job
    resp_job = client.get(f"/api/jobs/{job_alpha_id}", headers={"X-Workspace-ID": "ws_beta"})
    assert resp_job.status_code == 404

    # 4. Workspace Beta's pre-meeting recap must NEVER leak Workspace Alpha's tasks
    resp_recap_b = client.get("/api/recap/briefing", headers={"X-Workspace-ID": "ws_beta"})
    assert resp_recap_b.status_code == 200
    briefing_b = resp_recap_b.json()
    assert briefing_b["total_open"] == 0
    assert "secret prototype" not in briefing_b["markdown_briefing"].lower()

    # Workspace Alpha CAN access its own meeting
    resp_alpha_self = client.get(f"/api/meetings/{mtg_alpha.id}", headers={"X-Workspace-ID": "ws_alpha"})
    assert resp_alpha_self.status_code == 200
    assert resp_alpha_self.json()["id"] == mtg_alpha.id


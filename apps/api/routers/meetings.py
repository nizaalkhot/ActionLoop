import json
from fastapi import APIRouter, HTTPException, BackgroundTasks, Header
from typing import List, Optional
from schemas.pipeline import RawMeetingInput, MeetingResponse, CandidateTask, AsyncJobResponse
from services.pipeline_orchestrator import PipelineOrchestrator
from services.job_runner import BackgroundJobRunner
from services.retention import TranscriptRetentionService
from database import get_connection

router = APIRouter(prefix="/api", tags=["meetings"])

@router.post("/meetings/process", response_model=MeetingResponse)
def process_meeting(
    payload: RawMeetingInput,
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID")
):
    if not payload.transcript_or_notes.strip():
        raise HTTPException(status_code=400, detail="Transcript or notes cannot be empty")
    if isinstance(x_workspace_id, str) and x_workspace_id.strip():
        payload.workspace_id = x_workspace_id.strip()
    return PipelineOrchestrator.process_meeting(payload)

@router.post("/meetings/process-async", response_model=AsyncJobResponse)
def process_meeting_async(
    payload: RawMeetingInput,
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID")
):
    if not payload.transcript_or_notes.strip():
        raise HTTPException(status_code=400, detail="Transcript or notes cannot be empty")
    if isinstance(x_workspace_id, str) and x_workspace_id.strip():
        payload.workspace_id = x_workspace_id.strip()
    job_id = BackgroundJobRunner.create_and_start_job(payload)
    return AsyncJobResponse(
        job_id=job_id,
        workspace_id=payload.workspace_id or "ws_default",
        status="queued",
        stage="Initializing pipeline",
        progress=0.05
    )

@router.get("/jobs/{job_id}", response_model=AsyncJobResponse)
def get_job_status(
    job_id: str,
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID")
):
    ws_id = x_workspace_id if (isinstance(x_workspace_id, str) and x_workspace_id.strip()) else "ws_default"
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM background_jobs WHERE id = ? AND workspace_id = ?", (job_id, ws_id))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Background job not found in workspace")
    data = dict(row)
    return AsyncJobResponse(
        job_id=data["id"],
        workspace_id=data["workspace_id"],
        status=data["status"],
        stage=data["stage"],
        progress=data["progress"],
        result_meeting_id=data["result_meeting_id"],
        error_message=data["error_message"]
    )

@router.post("/meetings/purge-expired")
def purge_expired_transcripts(workspace_id: str = "ws_default"):
    return TranscriptRetentionService.purge_expired_transcripts(workspace_id)

@router.get("/meetings", response_model=List[dict])
def list_meetings(x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID")):
    ws_id = x_workspace_id if (isinstance(x_workspace_id, str) and x_workspace_id.strip()) else "ws_default"
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT m.id, m.workspace_id, m.title, m.meeting_date, m.timezone, m.created_at, m.purged_at,
               COUNT(t.id) as candidate_count,
               SUM(CASE WHEN t.status = 'approved' THEN 1 ELSE 0 END) as approved_count,
               SUM(CASE WHEN t.status = 'pushed' THEN 1 ELSE 0 END) as pushed_count
        FROM meetings m
        LEFT JOIN task_candidates t ON m.id = t.meeting_id
        WHERE m.workspace_id = ?
        GROUP BY m.id
        ORDER BY m.created_at DESC
    """, (ws_id,))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

@router.get("/meetings/{meeting_id}", response_model=MeetingResponse)
def get_meeting(
    meeting_id: str,
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID")
):
    ws_id = x_workspace_id if (isinstance(x_workspace_id, str) and x_workspace_id.strip()) else "ws_default"
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM meetings WHERE id = ? AND workspace_id = ?", (meeting_id, ws_id))
    mtg_row = cursor.fetchone()
    if not mtg_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Meeting not found in workspace")

    cursor.execute("SELECT * FROM task_candidates WHERE meeting_id = ? AND workspace_id = ? ORDER BY created_at ASC", (meeting_id, ws_id))
    cand_rows = [CandidateTask(**dict(r)) for r in cursor.fetchall()]
    conn.close()

    return MeetingResponse(
        id=mtg_row["id"],
        workspace_id=mtg_row["workspace_id"],
        title=mtg_row["title"],
        meeting_date=mtg_row["meeting_date"],
        timezone=mtg_row["timezone"],
        transcript_clean=mtg_row["transcript_clean"] or "[PURGED]",
        detected_speakers=json.loads(mtg_row["detected_speakers"]),
        candidates=cand_rows,
        created_at=mtg_row["created_at"]
    )

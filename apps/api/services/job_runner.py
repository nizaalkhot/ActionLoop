import uuid
import threading
from datetime import datetime, timezone
from schemas.pipeline import RawMeetingInput
from services.pipeline_orchestrator import PipelineOrchestrator
from database import get_connection

class BackgroundJobRunner:
    @classmethod
    def recover_interrupted_jobs(cls):
        """
        Called at server startup. Identifies any jobs that were in 'running' or 'queued'
        state when the server was shut down/restarted, and safely transitions them to 'interrupted'.
        """
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE background_jobs
            SET status = 'failed',
                error_message = 'Job was interrupted by server restart. Please re-trigger.',
                updated_at = ?
            WHERE status IN ('running', 'queued')
            """,
            (datetime.now(timezone.utc).isoformat(),)
        )
        conn.commit()
        conn.close()

    @classmethod
    def create_and_start_job(cls, payload: RawMeetingInput) -> str:
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        now_iso = datetime.now(timezone.utc).isoformat()
        ws_id = payload.workspace_id or "ws_default"

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO background_jobs (id, workspace_id, status, stage, progress, created_at, updated_at)
            VALUES (?, ?, 'queued', 'Initializing pipeline', 0.05, ?, ?)
            """,
            (job_id, ws_id, now_iso, now_iso)
        )
        conn.commit()
        conn.close()

        thread = threading.Thread(target=cls._run_worker, args=(job_id, payload))
        thread.daemon = True
        thread.start()

        return job_id

    @classmethod
    def _run_worker(cls, job_id: str, payload: RawMeetingInput):
        def update_job(status: str, stage: str, progress: float, result_id: str = None, error: str = None):
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE background_jobs
                SET status = ?, stage = ?, progress = ?, result_meeting_id = ?, error_message = ?, updated_at = ?
                WHERE id = ?
                """,
                (status, stage, progress, result_id, error, datetime.now(timezone.utc).isoformat(), job_id)
            )
            conn.commit()
            conn.close()

        try:
            update_job("running", "Normalizing transcript and speaker turns", 0.25)
            meeting_response = PipelineOrchestrator.process_meeting(payload)
            update_job("completed", "Pipeline finished successfully", 1.0, result_id=meeting_response.id)
        except Exception as e:
            update_job("failed", "Processing encountered an error", 0.0, error=str(e))

from datetime import datetime, timezone, timedelta
from database import get_connection

class TranscriptRetentionService:
    @staticmethod
    def purge_expired_transcripts(workspace_id: str = None) -> dict:
        """
        Purges raw and clean transcript texts that have exceeded their workspace retention period.
        Preserves candidate tasks, quotes, and audit logs.
        """
        conn = get_connection()
        cursor = conn.cursor()

        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()

        query = """
        SELECT id, created_at, retention_days
        FROM meetings
        WHERE purged_at IS NULL
        """
        params = []
        if workspace_id:
            query += " AND workspace_id = ?"
            params.append(workspace_id)

        cursor.execute(query, params)
        meetings = cursor.fetchall()
        purged_ids = []

        for m in meetings:
            try:
                created_dt = datetime.fromisoformat(m["created_at"])
            except Exception:
                continue

            retention_days = m["retention_days"] or 30
            expiration_date = created_dt + timedelta(days=retention_days)

            if now >= expiration_date:
                # Purge raw text, retain placeholder for data privacy
                cursor.execute(
                    """
                    UPDATE meetings
                    SET transcript_raw = '[PURGED_PER_DATA_RETENTION_POLICY]',
                        transcript_clean = '[PURGED_PER_DATA_RETENTION_POLICY]',
                        purged_at = ?
                    WHERE id = ?
                    """,
                    (now_iso, m["id"])
                )
                purged_ids.append(m["id"])

        conn.commit()
        conn.close()

        return {
            "purged_count": len(purged_ids),
            "purged_meeting_ids": purged_ids,
            "timestamp": now_iso
        }


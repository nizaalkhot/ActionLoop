import uuid
from typing import Dict, List, Optional
from services.integrations.base import BasePMIntegration
from database import get_connection

class MockLinearProvider(BasePMIntegration):
    def __init__(self, workspace_id: str = "ws_default"):
        self.workspace_id = workspace_id

    def get_members(self) -> List[Dict]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, email, avatar_url, role FROM workspace_users WHERE workspace_id = ?", (self.workspace_id,))
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows

    def get_open_tickets(self, project_id: Optional[str] = None) -> List[Dict]:
        conn = get_connection()
        cursor = conn.cursor()
        if project_id:
            cursor.execute("SELECT id, title, status, assignee_name, project_id FROM existing_tickets WHERE workspace_id = ? AND project_id = ?", (self.workspace_id, project_id))
        else:
            cursor.execute("SELECT id, title, status, assignee_name, project_id FROM existing_tickets WHERE workspace_id = ?", (self.workspace_id,))
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows

    def lookup_issue_by_fingerprint(self, task_fingerprint: str) -> Optional[Dict]:
        if not task_fingerprint:
            return None
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, title FROM existing_tickets WHERE workspace_id = ? AND fingerprint = ?",
            (self.workspace_id, task_fingerprint)
        )
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                "ticket_id": row["id"],
                "ticket_url": f"https://linear.app/demo-workspace/issue/{row['id']}",
                "status": "already_exists"
            }
        return None

    def create_task(self, title: str, description: str, assignee_id: Optional[str] = None, 
                    due_date: Optional[str] = None, project_id: Optional[str] = None,
                    supporting_quote: Optional[str] = None, meeting_title: Optional[str] = None,
                    task_fingerprint: Optional[str] = None) -> Dict:
        # Check lookup-before-retry first
        if task_fingerprint:
            existing = self.lookup_issue_by_fingerprint(task_fingerprint)
            if existing:
                return existing

        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as count FROM existing_tickets")
        count = cursor.fetchone()["count"]
        ticket_id = f"LIN-{100 + count + 1}"
        
        assignee_name = None
        if assignee_id:
            cursor.execute("SELECT name FROM workspace_users WHERE id = ? AND workspace_id = ?", (assignee_id, self.workspace_id))
            user_row = cursor.fetchone()
            if user_row:
                assignee_name = user_row["name"]

        cursor.execute(
            "INSERT INTO existing_tickets (id, workspace_id, title, status, assignee_name, project_id, fingerprint) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (ticket_id, self.workspace_id, title, "Todo", assignee_name, project_id or "proj_default", task_fingerprint)
        )
        conn.commit()
        conn.close()

        return {
            "ticket_id": ticket_id,
            "ticket_url": f"https://linear.app/demo-workspace/issue/{ticket_id}",
            "status": "created"
        }

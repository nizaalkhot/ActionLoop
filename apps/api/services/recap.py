from datetime import datetime, timezone
from typing import Dict, List, Optional
from database import get_connection

class PreMeetingRecapService:
    @classmethod
    def generate_briefing(
        cls,
        workspace_id: str = "ws_default",
        attendees: Optional[List[str]] = None,
        as_of_date: Optional[str] = None
    ) -> Dict:
        """
        Gathers open, overdue, and completed action items from prior meetings
        for the given attendees to 'close the loop' before the next meeting.
        """
        conn = get_connection()
        cursor = conn.cursor()

        today_str = as_of_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # Fetch candidate tasks across previous meetings in this workspace
        query = """
        SELECT t.id, t.meeting_id, m.title as meeting_title, t.title as task_title,
               t.resolved_owner_name, t.resolved_due_date, t.status, t.pushed_ticket_id, t.pushed_ticket_url
        FROM task_candidates t
        JOIN meetings m ON t.meeting_id = m.id
        WHERE t.workspace_id = ?
        ORDER BY t.created_at DESC
        """
        cursor.execute(query, (workspace_id,))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()

        # Group by owner
        member_summaries = {}
        total_open = 0
        total_overdue = 0
        total_completed = 0

        for r in rows:
            owner = r.get("resolved_owner_name") or "Unassigned"
            
            # Filter by attendees if specified
            if attendees and owner != "Unassigned":
                if not any(att.lower() in owner.lower() for att in attendees):
                    continue

            if owner not in member_summaries:
                member_summaries[owner] = {
                    "owner_name": owner,
                    "open_tasks": [],
                    "overdue_tasks": [],
                    "completed_tasks": []
                }

            status = r.get("status", "pending")
            due_date = r.get("resolved_due_date")
            is_overdue = bool(due_date and due_date < today_str and status not in ["done", "completed"])

            item = {
                "task_id": r["id"],
                "title": r["task_title"],
                "meeting_title": r["meeting_title"],
                "due_date": due_date,
                "status": status,
                "ticket_id": r["pushed_ticket_id"],
                "ticket_url": r["pushed_ticket_url"],
                "is_overdue": is_overdue
            }

            if is_overdue:
                member_summaries[owner]["overdue_tasks"].append(item)
                total_overdue += 1
            elif status in ["pushed", "done", "approved"]:
                member_summaries[owner]["open_tasks"].append(item)
                total_open += 1
            elif status == "completed":
                member_summaries[owner]["completed_tasks"].append(item)
                total_completed += 1

        # Format markdown briefing
        lines = [f"### 📋 Pre-Meeting Accountability Briefing (As of {today_str})\n"]
        if total_overdue > 0:
            lines.append(f"⚠️ **{total_overdue} item(s) slipped past deadline** across attendees.\n")

        for owner, data in member_summaries.items():
            if not data["open_tasks"] and not data["overdue_tasks"]:
                continue
            lines.append(f"**{owner}**:")
            for od in data["overdue_tasks"]:
                lines.append(f"  - 🔴 **SLIPPED**: {od['title']} (Due {od['due_date']} from *{od['meeting_title']}*)")
            for op in data["open_tasks"]:
                due_info = f" (Due {op['due_date']})" if op.get("due_date") else ""
                lines.append(f"  - ⏳ {op['title']}{due_info}")
            lines.append("")

        markdown_briefing = "\n".join(lines).strip()

        return {
            "as_of_date": today_str,
            "total_open": total_open,
            "total_overdue": total_overdue,
            "members": list(member_summaries.values()),
            "markdown_briefing": markdown_briefing
        }


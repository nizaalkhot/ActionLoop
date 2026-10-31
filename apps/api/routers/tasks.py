import datetime
import hashlib
import uuid
from fastapi import APIRouter, HTTPException, Header, Query
from typing import List, Optional
from schemas.pipeline import TaskUpdatePayload, CandidateTask, PushTasksRequest, PushTasksResponse, PushResultItem
from services.integrations.mock_provider import MockLinearProvider
from services.integrations.linear import LinearProvider
from database import get_connection

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

@router.patch("/{task_id}", response_model=CandidateTask)
def update_task_candidate(
    task_id: str,
    payload: TaskUpdatePayload,
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID")
):
    ws_id = x_workspace_id if (isinstance(x_workspace_id, str) and x_workspace_id.strip()) else "ws_default"
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM task_candidates WHERE id = ? AND workspace_id = ?", (task_id, ws_id))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Task candidate not found in workspace")

    existing = dict(row)
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # Track learning signal / feedback logs
    if payload.status and payload.status != existing.get("status"):
        cursor.execute(
            """
            INSERT INTO feedback_logs (workspace_id, meeting_id, task_id, action, original_value, corrected_value, reason, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (ws_id, existing["meeting_id"], task_id, f"status_{payload.status}", existing.get("status"), payload.status, "User review action", now_iso)
        )

    if payload.resolved_owner_id and payload.resolved_owner_id != existing.get("resolved_owner_id"):
        cursor.execute(
            """
            INSERT INTO feedback_logs (workspace_id, meeting_id, task_id, action, original_value, corrected_value, reason, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (ws_id, existing["meeting_id"], task_id, "edited_owner", existing.get("resolved_owner_name"), payload.resolved_owner_name, "User assigned different member", now_iso)
        )

    if payload.resolved_due_date and payload.resolved_due_date != existing.get("resolved_due_date"):
        cursor.execute(
            """
            INSERT INTO feedback_logs (workspace_id, meeting_id, task_id, action, original_value, corrected_value, reason, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (ws_id, existing["meeting_id"], task_id, "edited_date", existing.get("resolved_due_date"), payload.resolved_due_date, "User adjusted due date", now_iso)
        )

    # Dynamic updates
    updates = []
    values = []
    for field, val in payload.model_dump(exclude_unset=True).items():
        updates.append(f"{field} = ?")
        values.append(val)

    if updates:
        values.append(task_id)
        values.append(ws_id)
        cursor.execute(f"UPDATE task_candidates SET {', '.join(updates)} WHERE id = ? AND workspace_id = ?", values)
        conn.commit()

    cursor.execute("SELECT * FROM task_candidates WHERE id = ? AND workspace_id = ?", (task_id, ws_id))
    updated_row = dict(cursor.fetchone())
    conn.close()

    return CandidateTask(**updated_row)

@router.post("/batch-push", response_model=PushTasksResponse)
def batch_push_tasks(
    req: PushTasksRequest,
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID")
):
    ws_id = x_workspace_id if (isinstance(x_workspace_id, str) and x_workspace_id.strip()) else "ws_default"
    conn = get_connection()
    cursor = conn.cursor()

    # Tenant check on meeting
    cursor.execute("SELECT title, workspace_id FROM meetings WHERE id = ? AND workspace_id = ?", (req.meeting_id, ws_id))
    mtg = cursor.fetchone()
    if not mtg:
        conn.close()
        raise HTTPException(status_code=404, detail="Meeting not found in workspace")
    meeting_title = mtg["title"]

    # Select candidates to push
    if req.task_ids:
        placeholders = ",".join(["?"] * len(req.task_ids))
        cursor.execute(
            f"SELECT * FROM task_candidates WHERE id IN ({placeholders}) AND meeting_id = ? AND workspace_id = ?",
            (*req.task_ids, req.meeting_id, ws_id)
        )
    else:
        cursor.execute(
            "SELECT * FROM task_candidates WHERE meeting_id = ? AND workspace_id = ? AND status = 'approved'",
            (req.meeting_id, ws_id)
        )

    candidates = [dict(r) for r in cursor.fetchall()]
    if not candidates:
        conn.close()
        return PushTasksResponse(pushed_count=0, results=[])

    provider = LinearProvider() if req.target_tool == "linear" else MockLinearProvider(workspace_id=ws_id)
    results: List[PushResultItem] = []
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    for cand in candidates:
        task_id = cand["id"]
        fingerprint = hashlib.sha256(f"{cand['meeting_id']}:{cand['title']}:{cand.get('supporting_quote','')}".encode()).hexdigest()[:16]

        # 1. Check idempotency table first
        cursor.execute("SELECT ticket_id, ticket_url FROM idempotency_keys WHERE workspace_id = ? AND task_id = ?", (ws_id, task_id))
        idemp_row = cursor.fetchone()
        if idemp_row or cand.get("pushed_ticket_id"):
            ticket_id = idemp_row["ticket_id"] if idemp_row else cand["pushed_ticket_id"]
            ticket_url = idemp_row["ticket_url"] if idemp_row else (cand["pushed_ticket_url"] or "#")
            results.append(PushResultItem(
                task_id=task_id,
                ticket_id=ticket_id,
                ticket_url=ticket_url,
                status="already_pushed"
            ))
            continue

        # 2. Lookup-before-retry in PM tool using task fingerprint
        existing_pm = provider.lookup_issue_by_fingerprint(fingerprint)
        if existing_pm:
            ticket_id = existing_pm["ticket_id"]
            ticket_url = existing_pm["ticket_url"]
            # Record in idempotency and task_candidates
            cursor.execute(
                "INSERT OR IGNORE INTO idempotency_keys (id, workspace_id, task_id, ticket_id, ticket_url, fingerprint, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (f"idk_{uuid.uuid4().hex[:10]}", ws_id, task_id, ticket_id, ticket_url, fingerprint, now_iso)
            )
            cursor.execute(
                "UPDATE task_candidates SET status = 'pushed', pushed_ticket_id = ?, pushed_ticket_url = ?, task_fingerprint = ? WHERE id = ?",
                (ticket_id, ticket_url, fingerprint, task_id)
            )
            conn.commit()
            results.append(PushResultItem(
                task_id=task_id,
                ticket_id=ticket_id,
                ticket_url=ticket_url,
                status="already_pushed"
            ))
            continue

        # 3. Create issue in PM tool
        try:
            res = provider.create_task(
                title=cand["title"],
                description=cand.get("description", ""),
                assignee_id=cand.get("resolved_owner_id"),
                due_date=cand.get("resolved_due_date"),
                project_id=req.target_project_id,
                supporting_quote=cand.get("supporting_quote"),
                meeting_title=meeting_title,
                task_fingerprint=fingerprint
            )

            ticket_id = res["ticket_id"]
            ticket_url = res["ticket_url"]

            # Atomic database insert into idempotency_keys
            cursor.execute(
                "INSERT OR IGNORE INTO idempotency_keys (id, workspace_id, task_id, ticket_id, ticket_url, fingerprint, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (f"idk_{uuid.uuid4().hex[:10]}", ws_id, task_id, ticket_id, ticket_url, fingerprint, now_iso)
            )

            cursor.execute(
                "UPDATE task_candidates SET status = 'pushed', pushed_ticket_id = ?, pushed_ticket_url = ?, task_fingerprint = ? WHERE id = ?",
                (ticket_id, ticket_url, fingerprint, task_id)
            )
            conn.commit()

            results.append(PushResultItem(
                task_id=task_id,
                ticket_id=ticket_id,
                ticket_url=ticket_url,
                status="created"
            ))
        except Exception as e:
            results.append(PushResultItem(
                task_id=task_id,
                ticket_id="",
                ticket_url="",
                status=f"error: {str(e)}"
            ))

    conn.close()

    pushed_success = len([r for r in results if r.status in ["created", "already_pushed"]])
    return PushTasksResponse(pushed_count=pushed_success, results=results)

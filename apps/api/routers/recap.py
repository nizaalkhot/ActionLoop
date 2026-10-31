from fastapi import APIRouter, Query, Header
from typing import Optional, List
from services.recap import PreMeetingRecapService

router = APIRouter(prefix="/api/recap", tags=["recap"])

@router.get("/briefing")
def get_pre_meeting_briefing(
    attendees: Optional[str] = Query(None, description="Comma-separated attendee names"),
    as_of_date: Optional[str] = Query(None, description="ISO Date string YYYY-MM-DD"),
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID")
):
    ws_id = x_workspace_id or "ws_default"
    att_list = [a.strip() for a in attendees.split(",")] if attendees else None
    return PreMeetingRecapService.generate_briefing(
        workspace_id=ws_id,
        attendees=att_list,
        as_of_date=as_of_date
    )

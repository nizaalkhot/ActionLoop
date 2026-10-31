from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class RawMeetingInput(BaseModel):
    title: str = Field(default="Untitled Meeting", description="Meeting title or subject")
    transcript_or_notes: str = Field(..., description="Raw text notes or transcript with speaker timestamps")
    meeting_date: Optional[str] = Field(default=None, description="ISO Date string or YYYY-MM-DD")
    timezone: str = Field(default="UTC", description="Timezone identifier e.g. America/New_York or UTC")
    attendees: Optional[List[str]] = Field(default=[], description="Explicit list of attendees if known")
    target_tool: str = Field(default="mock", description="Target PM tool ('linear' or 'mock')")
    project_id: Optional[str] = Field(default=None, description="Target project or team identifier")
    workspace_id: str = Field(default="ws_default", description="Workspace tenant identifier")
    retention_days: int = Field(default=30, description="Transcript retention days before auto-scrubbing")

class CandidateTask(BaseModel):
    id: str
    meeting_id: str
    workspace_id: str = "ws_default"
    title: str
    description: str = ""
    raw_owner: Optional[str] = None
    resolved_owner_id: Optional[str] = None
    resolved_owner_name: Optional[str] = None
    owner_confidence: float = 0.0
    raw_due_date: Optional[str] = None
    resolved_due_date: Optional[str] = None
    date_confidence: float = 0.0
    supporting_quote: str
    confidence: float = 0.85
    task_type: str = "feature" # feature, bug, chore, follow_up
    status: str = "pending" # pending, approved, rejected, pushed
    possible_duplicate_of: Optional[str] = None
    duplicate_score: float = 0.0
    pushed_ticket_id: Optional[str] = None
    pushed_ticket_url: Optional[str] = None
    is_ambiguous: bool = False

class MeetingResponse(BaseModel):
    id: str
    workspace_id: str = "ws_default"
    title: str
    meeting_date: str
    timezone: str
    transcript_clean: str
    detected_speakers: List[str]
    candidates: List[CandidateTask]
    created_at: str

class TaskUpdatePayload(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    resolved_owner_id: Optional[str] = None
    resolved_owner_name: Optional[str] = None
    resolved_due_date: Optional[str] = None
    status: Optional[str] = None
    task_type: Optional[str] = None

class PushTasksRequest(BaseModel):
    meeting_id: str
    task_ids: Optional[List[str]] = None
    target_tool: str = "mock"
    target_project_id: Optional[str] = None

class PushResultItem(BaseModel):
    task_id: str
    ticket_id: str
    ticket_url: str
    status: str

class PushTasksResponse(BaseModel):
    pushed_count: int
    results: List[PushResultItem]

class FeedbackLogEntry(BaseModel):
    meeting_id: str
    task_id: str
    action: str
    original_value: Optional[str] = None
    corrected_value: Optional[str] = None
    reason: Optional[str] = None
    timestamp: Optional[str] = None

class EvaluationMetrics(BaseModel):
    total_candidates: int
    approved_count: int
    rejected_count: int
    edited_count: int
    acceptance_rate: float
    edit_rate: float
    avg_confidence: float

class AsyncJobResponse(BaseModel):
    job_id: str
    workspace_id: str
    status: str # queued, running, completed, failed
    stage: str
    progress: float
    result_meeting_id: Optional[str] = None
    error_message: Optional[str] = None

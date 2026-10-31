const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface CandidateTask {
  id: string;
  workspace_id?: string;
  meeting_id: string;
  title: string;
  description: string;
  raw_owner?: string | null;
  resolved_owner_id?: string | null;
  resolved_owner_name?: string | null;
  owner_confidence: number;
  raw_due_date?: string | null;
  resolved_due_date?: string | null;
  date_confidence: number;
  supporting_quote: string;
  confidence: number;
  task_type: string;
  status: "pending" | "approved" | "rejected" | "pushed";
  possible_duplicate_of?: string | null;
  duplicate_score: number;
  pushed_ticket_id?: string | null;
  pushed_ticket_url?: string | null;
  is_ambiguous?: boolean;
}

export interface MeetingData {
  id: string;
  workspace_id?: string;
  title: string;
  meeting_date: string;
  timezone: string;
  transcript_clean: string;
  detected_speakers: string[];
  candidates: CandidateTask[];
  created_at: string;
}

export interface WorkspaceUser {
  id: string;
  name: string;
  email: string;
  avatar_url?: string;
  role?: string;
}

export interface EvaluationMetrics {
  total_candidates: number;
  approved_count: number;
  rejected_count: number;
  edited_count: number;
  acceptance_rate: number;
  edit_rate: number;
  avg_confidence: number;
}

export async function processMeeting(payload: {
  title: string;
  transcript_or_notes: string;
  meeting_date?: string;
  timezone?: string;
  target_tool?: string;
  workspace_id?: string;
}): Promise<MeetingData> {
  const res = await fetch(`${API_BASE}/api/meetings/process`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to process meeting transcript");
  return res.json();
}

export async function processMeetingAsync(payload: any): Promise<{ job_id: string }> {
  const res = await fetch(`${API_BASE}/api/meetings/process-async`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to start async processing job");
  return res.json();
}

export async function getJobStatus(jobId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/api/jobs/${jobId}`);
  if (!res.ok) throw new Error("Failed to get job status");
  return res.json();
}

export async function getMeeting(id: string): Promise<MeetingData> {
  const res = await fetch(`${API_BASE}/api/meetings/${id}`);
  if (!res.ok) throw new Error("Failed to fetch meeting");
  return res.json();
}

export async function listMeetings(): Promise<any[]> {
  const res = await fetch(`${API_BASE}/api/meetings`);
  if (!res.ok) throw new Error("Failed to fetch meetings list");
  return res.json();
}

export async function updateTask(taskId: string, payload: Partial<CandidateTask>): Promise<CandidateTask> {
  const res = await fetch(`${API_BASE}/api/tasks/${taskId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to update task");
  return res.json();
}

export async function batchPushTasks(req: {
  meeting_id: string;
  task_ids?: string[];
  target_tool: string;
}): Promise<{ pushed_count: number; results: any[] }> {
  const res = await fetch(`${API_BASE}/api/tasks/batch-push`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) throw new Error("Failed to push tasks");
  return res.json();
}

export async function getWorkspaceMembers(): Promise<WorkspaceUser[]> {
  const res = await fetch(`${API_BASE}/api/workspace/members`);
  if (!res.ok) return [];
  return res.json();
}

export async function getEvaluationMetrics(): Promise<EvaluationMetrics> {
  const res = await fetch(`${API_BASE}/api/eval/metrics`);
  if (!res.ok) throw new Error("Failed to load evaluation metrics");
  return res.json();
}

export async function runGoldenBenchmark(geminiApiKey?: string): Promise<any> {
  const url = geminiApiKey
    ? `${API_BASE}/api/eval/run-golden-benchmark?gemini_api_key=${encodeURIComponent(geminiApiKey)}`
    : `${API_BASE}/api/eval/run-golden-benchmark`;
  const res = await fetch(url, {
    method: "POST",
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Failed to run benchmark" }));
    throw new Error(err.detail || "Failed to run benchmark");
  }
  return res.json();
}

export async function getPreMeetingBriefing(attendees?: string): Promise<any> {
  const url = attendees
    ? `${API_BASE}/api/recap/briefing?attendees=${encodeURIComponent(attendees)}`
    : `${API_BASE}/api/recap/briefing`;
  const res = await fetch(url);
  if (!res.ok) return null;
  return res.json();
}

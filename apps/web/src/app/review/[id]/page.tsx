"use client";

import React, { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  getMeeting,
  updateTask,
  batchPushTasks,
  getWorkspaceMembers,
  CandidateTask,
  MeetingData,
  WorkspaceUser,
} from "@/lib/api";
import TaskCard from "@/components/TaskCard";
import TranscriptDrawer from "@/components/TranscriptDrawer";
import PushSuccessModal from "@/components/PushSuccessModal";
import {
  ArrowLeft,
  CheckCircle2,
  FileText,
  Send,
  Loader2,
  Sparkles,
  Calendar,
  Users,
} from "lucide-react";

export default function ReviewPage() {
  const params = useParams();
  const router = useRouter();
  const meetingId = params.id as string;

  const [meeting, setMeeting] = useState<MeetingData | null>(null);
  const [members, setMembers] = useState<WorkspaceUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [isPushing, setIsPushing] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [highlightQuote, setHighlightQuote] = useState<string | null>(null);
  const [pushResults, setPushResults] = useState<any[] | null>(null);

  useEffect(() => {
    loadData();
  }, [meetingId]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [mtg, mems] = await Promise.all([
        getMeeting(meetingId),
        getWorkspaceMembers(),
      ]);
      setMeeting(mtg);
      setMembers(mems);
    } catch (err: any) {
      alert("Error loading review: " + (err.message || "Unknown"));
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateTask = async (taskId: string, patch: Partial<CandidateTask>) => {
    if (!meeting) return;

    // Optimistic UI update
    setMeeting((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        candidates: prev.candidates.map((c) => (c.id === taskId ? { ...c, ...patch } : c)),
      };
    });

    try {
      await updateTask(taskId, patch);
    } catch (e) {
      console.error("Failed to sync task update", e);
    }
  };

  const handleHighlightQuote = (quote: string) => {
    setHighlightQuote(quote);
    setDrawerOpen(true);
  };

  const handleApproveAllHighConfidence = async () => {
    if (!meeting) return;
    const highConf = meeting.candidates.filter(
      (c) => c.status === "pending" && c.confidence >= 0.8
    );
    for (const task of highConf) {
      await handleUpdateTask(task.id, { status: "approved" });
    }
  };

  const handlePushApproved = async () => {
    if (!meeting) return;
    const approvedTasks = meeting.candidates.filter((c) => c.status === "approved");
    if (approvedTasks.length === 0) {
      alert("Please approve at least one task before pushing to Linear.");
      return;
    }

    setIsPushing(true);
    try {
      const res = await batchPushTasks({
        meeting_id: meeting.id,
        task_ids: approvedTasks.map((t) => t.id),
        target_tool: "mock",
      });
      setPushResults(res.results);
      // Reload updated status
      await loadData();
    } catch (e: any) {
      alert("Push failed: " + (e.message || "Unknown error"));
    } finally {
      setIsPushing(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] space-y-3">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
        <p className="text-xs text-slate-500 font-medium">Loading 30-Second Review Screen...</p>
      </div>
    );
  }

  if (!meeting) {
    return (
      <div className="text-center py-12">
        <p className="text-slate-600 text-sm">Meeting not found.</p>
        <button
          onClick={() => router.push("/")}
          className="mt-4 text-xs font-semibold text-indigo-600 underline"
        >
          Return to Dashboard
        </button>
      </div>
    );
  }

  const approvedCount = meeting.candidates.filter((c) => c.status === "approved").length;
  const reviewedCount = meeting.candidates.filter((c) => c.status !== "pending").length;
  const totalCount = meeting.candidates.length;

  return (
    <div className="space-y-6">
      {/* Sticky Top Review Bar */}
      <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm sticky top-20 z-20">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => router.push("/")}
                className="p-1 rounded-md text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
                title="Back to Dashboard"
              >
                <ArrowLeft className="w-4 h-4" />
              </button>
              <h2 className="text-xl font-bold text-slate-900 tracking-tight">{meeting.title}</h2>
            </div>

            <div className="flex items-center space-x-4 text-xs text-slate-500 mt-1 pl-6">
              <span className="flex items-center space-x-1">
                <Calendar className="w-3.5 h-3.5 text-slate-400" />
                <span>Anchor Date: {meeting.meeting_date}</span>
              </span>
              <span>&bull;</span>
              <span className="flex items-center space-x-1">
                <Users className="w-3.5 h-3.5 text-slate-400" />
                <span>Speakers: {meeting.detected_speakers.join(", ") || "None detected"}</span>
              </span>
            </div>
          </div>

          {/* Quick Review Progress & Push Actions */}
          <div className="flex flex-wrap items-center gap-3">
            <div className="text-right hidden sm:block">
              <div className="text-xs font-semibold text-slate-700">
                {reviewedCount} of {totalCount} Reviewed
              </div>
              <div className="w-28 h-1.5 bg-slate-100 rounded-full overflow-hidden mt-1">
                <div
                  className="h-full bg-indigo-600 transition-all duration-300"
                  style={{ width: `${totalCount ? (reviewedCount / totalCount) * 100 : 0}%` }}
                />
              </div>
            </div>

            <button
              onClick={() => {
                setHighlightQuote(null);
                setDrawerOpen(true);
              }}
              className="flex items-center space-x-1.5 px-3 py-2 text-xs font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors"
            >
              <FileText className="w-3.5 h-3.5 text-slate-500" />
              <span>Inspect Transcript</span>
            </button>

            <button
              onClick={handleApproveAllHighConfidence}
              className="flex items-center space-x-1.5 px-3 py-2 text-xs font-medium text-indigo-700 bg-indigo-50 hover:bg-indigo-100 rounded-lg transition-colors"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>Approve High Conf (&gt;80%)</span>
            </button>

            <button
              onClick={handlePushApproved}
              disabled={isPushing || approvedCount === 0}
              className="flex items-center space-x-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs rounded-lg shadow-sm transition-all disabled:opacity-50"
            >
              {isPushing ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Pushing to Linear...</span>
                </>
              ) : (
                <>
                  <Send className="w-3.5 h-3.5" />
                  <span>Push {approvedCount} to Linear</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Task Candidates List */}
      <div className="space-y-4">
        {meeting.candidates.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-2xl border border-slate-200 p-8">
            <CheckCircle2 className="w-8 h-8 text-slate-400 mx-auto mb-2" />
            <p className="text-slate-600 text-sm font-medium">No actionable tasks detected.</p>
            <p className="text-xs text-slate-400 mt-1">
              General discussion, status updates, or passive observations without commitments are filtered out.
            </p>
          </div>
        ) : (
          meeting.candidates.map((task) => (
            <TaskCard
              key={task.id}
              task={task}
              members={members}
              onUpdate={handleUpdateTask}
              onHighlightQuote={handleHighlightQuote}
            />
          ))
        )}
      </div>

      {/* Slide-over Transcript Drawer */}
      <TranscriptDrawer
        isOpen={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        cleanTranscript={meeting.transcript_clean}
        highlightQuote={highlightQuote}
      />

      {/* Push Success Modal */}
      {pushResults && (
        <PushSuccessModal
          isOpen={true}
          onClose={() => setPushResults(null)}
          pushedResults={pushResults}
        />
      )}
    </div>
  );
}


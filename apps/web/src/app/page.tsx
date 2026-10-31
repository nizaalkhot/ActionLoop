"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { processMeetingAsync, getJobStatus, listMeetings } from "@/lib/api";
import PreMeetingRecap from "@/components/PreMeetingRecap";
import EvaluationDashboard from "@/components/EvaluationDashboard";
import { Sparkles, ArrowRight, Clock, CheckCircle2, History, Copy, Loader2, Calendar } from "lucide-react";

const SAMPLE_TRANSCRIPTS = {
  sprint: {
    title: "Sprint 14 Engineering Kickoff",
    date: "2026-11-04",
    text: `Marcus: Welcome everyone to the sprint 14 kickoff. Quick note, coffee machine is fixed on the 3rd floor.
Priya: Great to hear! Regarding the mobile nav bug, I will fix the navigation drawer overlap on iOS by Friday.
Marcus: Awesome, thank you Priya.
Alex Chen: I'll optimize the Postgres database connection pooling and deploy it to staging tomorrow.
Sarah: We should probably look into upgrading our Kubernetes clusters next quarter.
Marcus: Yeah, let's keep that in mind for Q4 roadmap, no action for now.
Alex Chen: Also, Priya, can you send the updated Figma component tokens to Sarah by Wednesday?
Priya: Yes, I'll send the tokens over.
Marcus: Perfect, let's wrap up.`,
  },
  client: {
    title: "Acme Corp Client Sync",
    date: "2026-11-04",
    text: `Marcus: Thanks for joining Acme Corp sync.
Client Rep: We noticed our invoice exports are missing the VAT tax breakdown.
Alex Chen: I'll update the PDF generator to include the VAT tax breakdown line by next Monday.
Client Rep: That would be fantastic. Also, do you think AI autofill is something we could do later this year?
Marcus: It is definitely on our radar, but nothing committed yet.
Sarah: I will set up the automated Datadog alerts for client invoice failures today.
Marcus: Sounds good everyone.`,
  },
  incident: {
    title: "Incident INC-492 Postmortem",
    date: "2026-11-04",
    text: `Marcus: Postmortem for incident INC-492 database saturation.
Sarah: I will increase the RDS read replica provisioned IOPS by tomorrow.
Alex Chen: I'll add rate limiting on the public API search endpoint by Friday.
Priya: Maybe we could refactor the entire frontend search component someday.
Marcus: Let's focus on the P0 stability items first.
Sarah: Understood. I'll document the failover playbook in Notion by end of week.`,
  },
};

export default function HomePage() {
  const router = useRouter();
  const [title, setTitle] = useState("Sprint 14 Engineering Kickoff");
  const [meetingDate, setMeetingDate] = useState("2026-11-04");
  const [timezone, setTimezone] = useState("UTC");
  const [transcript, setTranscript] = useState(SAMPLE_TRANSCRIPTS.sprint.text);
  const [targetTool, setTargetTool] = useState("mock");
  const [isProcessing, setIsProcessing] = useState(false);
  const [jobStage, setJobStage] = useState<string | null>(null);
  const [recentMeetings, setRecentMeetings] = useState<any[]>([]);

  useEffect(() => {
    loadRecentMeetings();
  }, []);

  const loadRecentMeetings = async () => {
    try {
      const meetings = await listMeetings();
      setRecentMeetings(meetings);
    } catch (e) {
      console.error(e);
    }
  };

  const handleApplySample = (sampleKey: "sprint" | "client" | "incident") => {
    const s = SAMPLE_TRANSCRIPTS[sampleKey];
    setTitle(s.title);
    setMeetingDate(s.date);
    setTranscript(s.text);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!transcript.trim()) return;

    setIsProcessing(true);
    setJobStage("Queuing background pipeline...");

    try {
      // Async processing to prevent HTTP timeouts
      const { job_id } = await processMeetingAsync({
        title,
        transcript_or_notes: transcript,
        meeting_date: meetingDate,
        timezone,
        target_tool: targetTool,
      });

      // Poll job progress
      const pollInterval = setInterval(async () => {
        try {
          const statusData = await getJobStatus(job_id);
          setJobStage(statusData.stage || "Processing...");

          if (statusData.status === "completed" && statusData.result_meeting_id) {
            clearInterval(pollInterval);
            router.push(`/review/${statusData.result_meeting_id}`);
          } else if (statusData.status === "failed") {
            clearInterval(pollInterval);
            setIsProcessing(false);
            alert("Processing failed: " + (statusData.error_message || "Unknown"));
          }
        } catch (pollErr) {
          clearInterval(pollInterval);
          setIsProcessing(false);
          alert("Error polling job status");
        }
      }, 700);
    } catch (err: any) {
      alert("Error starting pipeline: " + (err.message || "Unknown error"));
      setIsProcessing(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Hero Header */}
      <div className="text-center max-w-3xl mx-auto space-y-3">
        <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">
          Turn Messy Meeting Notes into <span className="text-indigo-600">Actionable PM Tasks</span>
        </h1>
        <p className="text-slate-600 text-sm sm:text-base">
          Deterministic 6-stage extraction pipeline: resolves spoken owners to real workspace users,
          anchors temporal dates, flags open-ticket duplicates, and lets you review in under 30 seconds.
        </p>
      </div>

      {/* Differentiator: Pre-Meeting Accountability Briefing */}
      <PreMeetingRecap />

      {/* Main Input Card */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 sm:p-8">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-6 pb-4 border-b border-slate-100">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Quick Load Sample Transcript:
          </span>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => handleApplySample("sprint")}
              className="text-xs px-3 py-1.5 rounded-lg bg-indigo-50 text-indigo-700 font-medium hover:bg-indigo-100 transition-colors"
            >
              Sprint Planning
            </button>
            <button
              type="button"
              onClick={() => handleApplySample("client")}
              className="text-xs px-3 py-1.5 rounded-lg bg-slate-100 text-slate-700 font-medium hover:bg-slate-200 transition-colors"
            >
              Client Sync
            </button>
            <button
              type="button"
              onClick={() => handleApplySample("incident")}
              className="text-xs px-3 py-1.5 rounded-lg bg-rose-50 text-rose-700 font-medium hover:bg-rose-100 transition-colors"
            >
              Incident Postmortem
            </button>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="sm:col-span-2">
              <label className="block text-xs font-semibold text-slate-700 mb-1">Meeting Title</label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
                className="w-full px-3.5 py-2 text-sm bg-white border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Anchor Meeting Date</label>
              <input
                type="date"
                value={meetingDate}
                onChange={(e) => setMeetingDate(e.target.value)}
                required
                className="w-full px-3.5 py-2 text-sm bg-white border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="block text-xs font-semibold text-slate-700">
                Raw Transcript or Notes (SRT, VTT, or Speaker Turns)
              </label>
              <span className="text-[11px] text-slate-400">
                Paste raw text, speaker logs, or action items
              </span>
            </div>
            <textarea
              rows={8}
              value={transcript}
              onChange={(e) => setTranscript(e.target.value)}
              required
              placeholder="Paste meeting transcript or notes here..."
              className="w-full px-3.5 py-2.5 text-xs font-mono bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 leading-relaxed text-slate-800"
            />
          </div>

          <div className="flex flex-col sm:flex-row items-center justify-between pt-4 border-t border-slate-100 gap-4">
            <div className="flex items-center space-x-3 text-xs text-slate-600">
              <span className="font-medium">Target PM Tool:</span>
              <label className="flex items-center space-x-1.5 cursor-pointer">
                <input
                  type="radio"
                  name="targetTool"
                  value="mock"
                  checked={targetTool === "mock"}
                  onChange={() => setTargetTool("mock")}
                  className="text-indigo-600"
                />
                <span>Linear Workspace (Sandbox)</span>
              </label>
              <label className="flex items-center space-x-1.5 cursor-pointer">
                <input
                  type="radio"
                  name="targetTool"
                  value="linear"
                  checked={targetTool === "linear"}
                  onChange={() => setTargetTool("linear")}
                  className="text-indigo-600"
                />
                <span>Linear Cloud OAuth</span>
              </label>
            </div>

            <button
              type="submit"
              disabled={isProcessing}
              className="w-full sm:w-auto px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm rounded-xl shadow-md flex items-center justify-center space-x-2 transition-all disabled:opacity-50"
            >
              {isProcessing ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>{jobStage || "Processing..."}</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  <span>Process into Review (30s)</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Past Processed Meetings */}
      {recentMeetings.length > 0 && (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
          <div className="flex items-center space-x-2 mb-4 pb-3 border-b border-slate-100">
            <History className="w-4 h-4 text-slate-500" />
            <h3 className="font-bold text-sm text-slate-900">Recent Meetings</h3>
          </div>

          <div className="divide-y divide-slate-100">
            {recentMeetings.map((m) => (
              <div
                key={m.id}
                onClick={() => router.push(`/review/${m.id}`)}
                className="py-3 px-2 flex items-center justify-between hover:bg-slate-50 rounded-lg cursor-pointer transition-colors"
              >
                <div>
                  <h4 className="font-semibold text-sm text-slate-900">{m.title}</h4>
                  <div className="flex items-center space-x-3 text-xs text-slate-500 mt-0.5">
                    <span className="flex items-center space-x-1">
                      <Calendar className="w-3.5 h-3.5 text-slate-400" />
                      <span>{m.meeting_date}</span>
                    </span>
                    <span>&bull;</span>
                    <span>{m.candidate_count || 0} candidate tasks</span>
                  </div>
                </div>

                <div className="flex items-center space-x-3">
                  {m.pushed_count > 0 ? (
                    <span className="px-2.5 py-1 rounded-full text-[11px] font-semibold bg-emerald-100 text-emerald-800">
                      {m.pushed_count} Pushed
                    </span>
                  ) : m.approved_count > 0 ? (
                    <span className="px-2.5 py-1 rounded-full text-[11px] font-semibold bg-indigo-100 text-indigo-800">
                      {m.approved_count} Approved
                    </span>
                  ) : (
                    <span className="px-2.5 py-1 rounded-full text-[11px] font-semibold bg-slate-100 text-slate-600">
                      Needs Review
                    </span>
                  )}
                  <ArrowRight className="w-4 h-4 text-slate-400" />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Evaluation & Continuous Learning Component */}
      <EvaluationDashboard />
    </div>
  );
}

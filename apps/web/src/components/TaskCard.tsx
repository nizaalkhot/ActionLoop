"use client";

import React, { useState } from "react";
import { CandidateTask, WorkspaceUser } from "@/lib/api";
import { Check, X, AlertTriangle, Quote, User, Calendar, ExternalLink, Sparkles } from "lucide-react";

interface TaskCardProps {
  task: CandidateTask;
  members: WorkspaceUser[];
  onUpdate: (taskId: string, patch: Partial<CandidateTask>) => void;
  onHighlightQuote: (quote: string) => void;
}

export default function TaskCard({ task, members, onUpdate, onHighlightQuote }: TaskCardProps) {
  const [isEditingTitle, setIsEditingTitle] = useState(false);
  const [title, setTitle] = useState(task.title);

  const handleTitleBlur = () => {
    setIsEditingTitle(false);
    if (title !== task.title) {
      onUpdate(task.id, { title });
    }
  };

  const isApproved = task.status === "approved";
  const isRejected = task.status === "rejected";
  const isPushed = task.status === "pushed";

  return (
    <div
      className={`rounded-xl border p-5 transition-all shadow-sm ${
        isApproved
          ? "border-emerald-300 bg-emerald-50/40 ring-1 ring-emerald-300"
          : isRejected
          ? "border-slate-200 bg-slate-100/60 opacity-60"
          : isPushed
          ? "border-indigo-300 bg-indigo-50/40"
          : "border-slate-200 bg-white hover:border-slate-300"
      }`}
    >
      {/* Duplicate Alert Banner */}
      {task.possible_duplicate_of && !isRejected && (
        <div className="mb-4 flex items-center justify-between rounded-lg bg-amber-50 border border-amber-200 px-3 py-2 text-xs text-amber-800">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0" />
            <span>
              <strong>Possible Duplicate:</strong> {task.possible_duplicate_of}
            </span>
          </div>
          <span className="font-semibold text-amber-700 bg-amber-100/80 px-2 py-0.5 rounded text-[11px]">
            {Math.round(task.duplicate_score * 100)}% Match
          </span>
        </div>
      )}

      {/* Ambiguous Name Warning Banner */}
      {task.is_ambiguous && !isRejected && (
        <div className="mb-4 flex items-center justify-between rounded-lg bg-orange-50 border border-orange-200 px-3 py-2 text-xs text-orange-800">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 text-orange-600 flex-shrink-0" />
            <span>
              <strong>Ambiguous Name:</strong> Multiple attendees match "{task.raw_owner}". Left unassigned for your confirmation.
            </span>
          </div>
          <span className="font-semibold text-orange-700 bg-orange-100/80 px-2 py-0.5 rounded text-[11px]">
            Needs Owner
          </span>
        </div>
      )}

      {/* Top Header & Actions */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            {/* Task Type Badge */}
            <span
              className={`text-[11px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded ${
                task.task_type === "bug"
                  ? "bg-rose-100 text-rose-700"
                  : task.task_type === "chore"
                  ? "bg-purple-100 text-purple-700"
                  : task.task_type === "follow_up"
                  ? "bg-blue-100 text-blue-700"
                  : "bg-emerald-100 text-emerald-700"
              }`}
            >
              {task.task_type}
            </span>

            {/* Confidence Badge */}
            <span className="flex items-center text-[11px] font-medium text-slate-500 bg-slate-100 px-2 py-0.5 rounded">
              <Sparkles className="w-3 h-3 mr-1 text-indigo-500" />
              {Math.round(task.confidence * 100)}% confidence
            </span>

            {isPushed && (
              <a
                href={task.pushed_ticket_url || "#"}
                target="_blank"
                rel="noreferrer"
                className="flex items-center text-xs font-semibold text-indigo-600 hover:text-indigo-800 bg-indigo-50 px-2 py-0.5 rounded border border-indigo-200"
              >
                <span>{task.pushed_ticket_id || "Ticket Pushed"}</span>
                <ExternalLink className="w-3 h-3 ml-1" />
              </a>
            )}
          </div>

          {/* Editable Title */}
          {isEditingTitle ? (
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              onBlur={handleTitleBlur}
              onKeyDown={(e) => e.key === "Enter" && handleTitleBlur()}
              autoFocus
              className="w-full text-base font-semibold text-slate-900 border-b border-indigo-500 bg-transparent focus:outline-none"
            />
          ) : (
            <h4
              onClick={() => !isPushed && setIsEditingTitle(true)}
              className={`text-base font-semibold text-slate-900 cursor-pointer hover:text-indigo-600 ${
                isRejected ? "line-through text-slate-500" : ""
              }`}
              title="Click to edit title"
            >
              {task.title}
            </h4>
          )}
        </div>

        {/* 30-Second Confirmation Buttons */}
        {!isPushed && (
          <div className="flex items-center space-x-1.5 flex-shrink-0">
            <button
              onClick={() => onUpdate(task.id, { status: isApproved ? "pending" : "approved" })}
              className={`p-2 rounded-lg transition-all flex items-center justify-center text-xs font-medium ${
                isApproved
                  ? "bg-emerald-600 text-white shadow-sm"
                  : "bg-slate-100 text-slate-600 hover:bg-emerald-100 hover:text-emerald-700"
              }`}
              title="Approve task"
            >
              <Check className="w-4 h-4" />
            </button>
            <button
              onClick={() => onUpdate(task.id, { status: isRejected ? "pending" : "rejected" })}
              className={`p-2 rounded-lg transition-all flex items-center justify-center text-xs font-medium ${
                isRejected
                  ? "bg-rose-600 text-white shadow-sm"
                  : "bg-slate-100 text-slate-600 hover:bg-rose-100 hover:text-rose-700"
              }`}
              title="Reject task"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>

      {/* Supporting Quote Context */}
      <div className="mt-3.5 flex items-start gap-2 bg-slate-50 border border-slate-100 rounded-lg p-2.5 text-xs text-slate-600">
        <Quote className="w-4 h-4 text-indigo-500 flex-shrink-0 mt-0.5" />
        <div className="flex-1">
          <p className="italic font-serif">"{task.supporting_quote}"</p>
        </div>
        <button
          onClick={() => onHighlightQuote(task.supporting_quote)}
          className="text-indigo-600 hover:text-indigo-800 text-[11px] font-medium underline flex-shrink-0"
        >
          View in transcript
        </button>
      </div>

      {/* Metadata Fields: Assignee & Due Date */}
      <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-3 pt-3 border-t border-slate-100 text-xs">
        {/* Assignee Resolver */}
        <div className="flex items-center space-x-2">
          <User className="w-4 h-4 text-slate-400" />
          <div className="flex-1">
            <select
              value={task.resolved_owner_id || ""}
              onChange={(e) => {
                const selected = members.find((m) => m.id === e.target.value);
                onUpdate(task.id, {
                  resolved_owner_id: e.target.value || null,
                  resolved_owner_name: selected?.name || null,
                });
              }}
              disabled={isPushed}
              className="w-full bg-white border border-slate-200 rounded px-2 py-1 text-xs text-slate-700 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            >
              <option value="">Unassigned</option>
              {members.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.name} ({m.role || "Team"})
                </option>
              ))}
            </select>
          </div>
          {task.raw_owner && (
            <span className="text-[10px] text-slate-400" title={`Resolved from spoken phrase: "${task.raw_owner}"`}>
              ({task.raw_owner})
            </span>
          )}
        </div>

        {/* Due Date Resolver */}
        <div className="flex items-center space-x-2">
          <Calendar className="w-4 h-4 text-slate-400" />
          <div className="flex-1">
            <input
              type="date"
              value={task.resolved_due_date || ""}
              onChange={(e) => onUpdate(task.id, { resolved_due_date: e.target.value || null })}
              disabled={isPushed}
              className="w-full bg-white border border-slate-200 rounded px-2 py-1 text-xs text-slate-700 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
          </div>
          {task.raw_due_date && (
            <span className="text-[10px] text-slate-400" title={`Resolved from: "${task.raw_due_date}"`}>
              ({task.raw_due_date})
            </span>
          )}
        </div>
      </div>
    </div>
  );
}


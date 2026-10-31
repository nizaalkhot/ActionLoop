"use client";

import React from "react";
import { CheckCircle2, ExternalLink, X } from "lucide-react";

interface PushSuccessModalProps {
  isOpen: boolean;
  onClose: () => void;
  pushedResults: Array<{
    task_id: string;
    ticket_id: string;
    ticket_url: string;
    status: string;
  }>;
}

export default function PushSuccessModal({
  isOpen,
  onClose,
  pushedResults,
}: PushSuccessModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-100">
        <div className="flex items-start justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-emerald-100 text-emerald-600 rounded-full">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-slate-900">Tasks Successfully Pushed!</h3>
              <p className="text-xs text-slate-500">
                Created {pushedResults.length} issues in Linear with quotes and metadata.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 p-1 rounded-lg"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="mt-5 space-y-2 max-h-60 overflow-y-auto">
          {pushedResults.map((r, i) => (
            <div
              key={i}
              className="flex items-center justify-between p-3 rounded-lg border border-slate-100 bg-slate-50 text-xs"
            >
              <div className="font-semibold text-slate-800">{r.ticket_id || "Created"}</div>
              <a
                href={r.ticket_url}
                target="_blank"
                rel="noreferrer"
                className="flex items-center space-x-1 text-indigo-600 font-medium hover:text-indigo-800"
              >
                <span>View Ticket</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
            </div>
          ))}
        </div>

        <div className="mt-6 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-indigo-600 text-white font-medium text-xs rounded-lg hover:bg-indigo-700 shadow-sm"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
}


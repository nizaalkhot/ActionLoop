"use client";

import React from "react";
import { X, FileText } from "lucide-react";

interface TranscriptDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  cleanTranscript: string;
  highlightQuote?: string | null;
}

export default function TranscriptDrawer({
  isOpen,
  onClose,
  cleanTranscript,
  highlightQuote,
}: TranscriptDrawerProps) {
  if (!isOpen) return null;

  const lines = cleanTranscript.split("\n");

  return (
    <div className="fixed inset-y-0 right-0 w-full sm:w-[480px] bg-white border-l border-slate-200 shadow-2xl z-50 flex flex-col transition-all">
      <div className="p-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
        <div className="flex items-center space-x-2">
          <FileText className="w-5 h-5 text-indigo-600" />
          <h3 className="font-semibold text-slate-800 text-sm">Transcript Source Inspector</h3>
        </div>
        <button
          onClick={onClose}
          className="p-1 rounded-md text-slate-400 hover:text-slate-600 hover:bg-slate-200 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-5 text-xs font-mono leading-relaxed space-y-2 bg-slate-50/50">
        {lines.map((line, idx) => {
          const isHighlighted = highlightQuote && line.includes(highlightQuote.trim());

          return (
            <div
              key={idx}
              className={`p-2 rounded transition-colors ${
                isHighlighted
                  ? "bg-amber-100 text-amber-900 border-l-4 border-amber-500 font-medium shadow-sm"
                  : "text-slate-700 hover:bg-slate-100"
              }`}
            >
              {line}
            </div>
          );
        })}
      </div>
    </div>
  );
}


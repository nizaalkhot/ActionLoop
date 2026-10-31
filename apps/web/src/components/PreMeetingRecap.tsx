"use client";

import React, { useState, useEffect } from "react";
import { getPreMeetingBriefing } from "@/lib/api";
import { Clock, AlertCircle, CheckCircle, Copy, Check, ChevronDown, ChevronUp, UserCheck, Flame } from "lucide-react";

export default function PreMeetingRecap() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);
  const [isOpen, setIsOpen] = useState(true);

  useEffect(() => {
    loadBriefing();
  }, []);

  const loadBriefing = async () => {
    try {
      const res = await getPreMeetingBriefing();
      setData(res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = () => {
    if (!data?.markdown_briefing) return;
    navigator.clipboard.writeText(data.markdown_briefing);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (loading) return null;
  if (!data || (data.total_open === 0 && data.total_overdue === 0)) return null;

  return (
    <div className="bg-gradient-to-r from-amber-500/10 via-indigo-500/5 to-slate-50 border border-amber-200/80 rounded-2xl p-5 shadow-sm">
      <div className="flex items-center justify-between pb-3 border-b border-amber-100">
        <div className="flex items-center space-x-2.5">
          <div className="p-1.5 bg-amber-500 text-white rounded-lg shadow-sm">
            <Flame className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="text-sm font-bold text-slate-900">
                Pre-Meeting Accountability Briefing
              </h3>
              <span className="text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 border border-amber-300">
                Closing the Loop
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Open and overdue tasks from previous meetings for attendees before today's sync.
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={handleCopy}
            className="flex items-center space-x-1.5 px-3 py-1.5 bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 rounded-lg text-xs font-medium transition-colors shadow-sm"
            title="Copy Slack/Email Briefing"
          >
            {copied ? (
              <>
                <Check className="w-3.5 h-3.5 text-emerald-600" />
                <span className="text-emerald-600 font-semibold">Copied!</span>
              </>
            ) : (
              <>
                <Copy className="w-3.5 h-3.5 text-slate-500" />
                <span>Copy for Slack</span>
              </>
            )}
          </button>

          <button
            onClick={() => setIsOpen(!isOpen)}
            className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg"
          >
            {isOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {isOpen && (
        <div className="mt-4 space-y-3">
          {data.total_overdue > 0 && (
            <div className="flex items-center space-x-2 text-xs font-semibold text-rose-700 bg-rose-50 border border-rose-200 px-3 py-2 rounded-lg">
              <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0" />
              <span>
                {data.total_overdue} item(s) slipped past deadline across team members. Surface these first in standup!
              </span>
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {data.members.map((m: any, idx: number) => {
              if (m.open_tasks.length === 0 && m.overdue_tasks.length === 0) return null;
              return (
                <div key={idx} className="bg-white border border-slate-200 rounded-xl p-3 shadow-xs">
                  <div className="flex items-center justify-between pb-2 border-b border-slate-100">
                    <span className="text-xs font-bold text-slate-800">{m.owner_name}</span>
                    <span className="text-[10px] text-slate-400">
                      {m.overdue_tasks.length > 0 ? (
                        <span className="text-rose-600 font-semibold">{m.overdue_tasks.length} overdue</span>
                      ) : (
                        <span>{m.open_tasks.length} open</span>
                      )}
                    </span>
                  </div>

                  <div className="mt-2 space-y-1.5 text-xs">
                    {m.overdue_tasks.map((t: any, i: number) => (
                      <div key={i} className="text-rose-700 bg-rose-50/50 p-1.5 rounded flex items-start space-x-1.5">
                        <AlertCircle className="w-3.5 h-3.5 text-rose-500 mt-0.5 flex-shrink-0" />
                        <span className="font-medium truncate">{t.title}</span>
                      </div>
                    ))}
                    {m.open_tasks.map((t: any, i: number) => (
                      <div key={i} className="text-slate-700 p-1 rounded flex items-start space-x-1.5">
                        <Clock className="w-3.5 h-3.5 text-slate-400 mt-0.5 flex-shrink-0" />
                        <span className="truncate">{t.title}</span>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}


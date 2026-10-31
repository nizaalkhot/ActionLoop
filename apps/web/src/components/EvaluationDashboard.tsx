"use client";

import React, { useState, useEffect } from "react";
import { getEvaluationMetrics, runGoldenBenchmark, EvaluationMetrics } from "@/lib/api";
import { BarChart3, TrendingUp, CheckCircle, AlertOctagon, Edit3, Play, Loader2, ShieldCheck, Sparkles, Key } from "lucide-react";

export default function EvaluationDashboard() {
  const [metrics, setMetrics] = useState<EvaluationMetrics | null>(null);
  const [benchmarkResult, setBenchmarkResult] = useState<any | null>(null);
  const [isRunningBenchmark, setIsRunningBenchmark] = useState(false);
  const [geminiApiKey, setGeminiApiKey] = useState("");
  const [loading, setLoading] = useState(true);

  const loadMetrics = async () => {
    try {
      const data = await getEvaluationMetrics();
      setMetrics(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMetrics();
  }, []);

  const handleBenchmark = async () => {
    setIsRunningBenchmark(true);
    try {
      const res = await runGoldenBenchmark(geminiApiKey || undefined);
      setBenchmarkResult(res);
      await loadMetrics();
    } catch (e: any) {
      alert("Benchmark failed: " + (e.message || "Ensure GEMINI_API_KEY is configured."));
    } finally {
      setIsRunningBenchmark(false);
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-xs text-slate-400">Loading evaluation metrics...</div>;
  }

  return (
    <section id="eval-metrics" className="mt-12 bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-6 border-b border-slate-100 gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <BarChart3 className="w-5 h-5 text-indigo-600" />
            <h2 className="text-lg font-bold text-slate-900">Gemini LLM Evaluation Benchmark</h2>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Pure model evaluation across 40 real-world transcripts using Gemini Flash structured outputs.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center space-x-1.5 bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5">
            <Key className="w-3.5 h-3.5 text-slate-400" />
            <input
              type="password"
              placeholder="Gemini API Key (optional)"
              value={geminiApiKey}
              onChange={(e) => setGeminiApiKey(e.target.value)}
              className="text-xs bg-transparent focus:outline-none w-36 text-slate-700"
            />
          </div>

          <div className="flex items-center space-x-1 text-[11px] font-semibold text-indigo-700 bg-indigo-50 border border-indigo-200 px-2.5 py-1.5 rounded-lg">
            <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
            <span>Gemini Flash Only</span>
          </div>

          <button
            onClick={handleBenchmark}
            disabled={isRunningBenchmark}
            className="flex items-center space-x-2 px-3.5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold shadow-sm transition-all disabled:opacity-50"
          >
            {isRunningBenchmark ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                <span>Running Model Eval...</span>
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5" />
                <span>Run Model Benchmark</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
        <div className="p-4 rounded-xl bg-slate-50 border border-slate-100">
          <div className="flex items-center justify-between text-slate-500 text-xs">
            <span>Acceptance Rate</span>
            <CheckCircle className="w-4 h-4 text-emerald-500" />
          </div>
          <div className="text-2xl font-bold text-slate-900 mt-2">
            {metrics ? `${Math.round(metrics.acceptance_rate * 100)}%` : "0%"}
          </div>
          <p className="text-[11px] text-slate-400 mt-1">Approved by human</p>
        </div>

        <div className="p-4 rounded-xl bg-slate-50 border border-slate-100">
          <div className="flex items-center justify-between text-slate-500 text-xs">
            <span>Rejection Rate</span>
            <AlertOctagon className="w-4 h-4 text-rose-500" />
          </div>
          <div className="text-2xl font-bold text-slate-900 mt-2">
            {metrics ? `${Math.round((metrics.rejected_count / (metrics.total_candidates || 1)) * 100)}%` : "0%"}
          </div>
          <p className="text-[11px] text-slate-400 mt-1">Goal: minimize over time</p>
        </div>

        <div className="p-4 rounded-xl bg-slate-50 border border-slate-100">
          <div className="flex items-center justify-between text-slate-500 text-xs">
            <span>Edit / Adjust Rate</span>
            <Edit3 className="w-4 h-4 text-amber-500" />
          </div>
          <div className="text-2xl font-bold text-slate-900 mt-2">
            {metrics ? `${Math.round(metrics.edit_rate * 100)}%` : "0%"}
          </div>
          <p className="text-[11px] text-slate-400 mt-1">Owner or date adjusted</p>
        </div>

        <div className="p-4 rounded-xl bg-slate-50 border border-slate-100">
          <div className="flex items-center justify-between text-slate-500 text-xs">
            <span>Avg Confidence</span>
            <TrendingUp className="w-4 h-4 text-indigo-500" />
          </div>
          <div className="text-2xl font-bold text-slate-900 mt-2">
            {metrics ? `${Math.round(metrics.avg_confidence * 100)}%` : "0%"}
          </div>
          <p className="text-[11px] text-slate-400 mt-1">Model certainty</p>
        </div>
      </div>

      {/* Benchmark Results Display */}
      {benchmarkResult && (
        <div className="mt-6 p-5 rounded-xl bg-indigo-50/60 border border-indigo-100">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-indigo-900">
              Gemini Benchmark Results ({benchmarkResult.cases_evaluated} transcripts &bull; {benchmarkResult.total_expected_actions} actions)
            </h4>
            <div className="flex items-center space-x-2 text-[11px] text-indigo-700 bg-indigo-100 px-2 py-0.5 rounded">
              <Sparkles className="w-3 h-3 text-indigo-600" />
              <span>Engine: {benchmarkResult.engine_used} ({benchmarkResult.execution_duration_seconds}s)</span>
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-6 gap-3 text-center text-xs">
            <div className="p-2.5 bg-white rounded-lg border border-indigo-100 shadow-2xs">
              <span className="text-slate-500 block text-[11px]">Precision</span>
              <strong className="text-base text-slate-900 font-bold">
                {Math.round(benchmarkResult.precision * 100)}%
              </strong>
            </div>
            <div className="p-2.5 bg-white rounded-lg border border-indigo-100 shadow-2xs">
              <span className="text-slate-500 block text-[11px]">Recall</span>
              <strong className="text-base text-slate-900 font-bold">
                {Math.round(benchmarkResult.recall * 100)}%
              </strong>
            </div>
            <div className="p-2.5 bg-white rounded-lg border border-indigo-100 shadow-2xs">
              <span className="text-slate-500 block text-[11px]">F1 Score</span>
              <strong className="text-base text-slate-900 font-bold">
                {Math.round(benchmarkResult.f1_score * 100)}%
              </strong>
            </div>
            <div className="p-2.5 bg-white rounded-lg border border-indigo-100 shadow-2xs">
              <span className="text-slate-500 block text-[11px]">Owner Acc</span>
              <strong className="text-base text-slate-900 font-bold">
                {Math.round(benchmarkResult.owner_accuracy * 100)}%
              </strong>
            </div>
            <div className="p-2.5 bg-white rounded-lg border border-indigo-100 shadow-2xs">
              <span className="text-slate-500 block text-[11px]">Date Acc</span>
              <strong className="text-base text-slate-900 font-bold">
                {Math.round(benchmarkResult.due_date_accuracy * 100)}%
              </strong>
            </div>
            <div className="p-2.5 bg-white rounded-lg border border-indigo-100 shadow-2xs">
              <span className="text-slate-500 block text-[11px] flex items-center justify-center">
                <ShieldCheck className="w-3 h-3 text-emerald-500 mr-0.5" />
                Anti-Slop Filter
              </span>
              <strong className="text-base text-emerald-700 font-bold">
                {Math.round(benchmarkResult.negative_discussion_rejection_rate * 100)}%
              </strong>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}

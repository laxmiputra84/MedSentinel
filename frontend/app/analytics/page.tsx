'use client';

import React, { useState } from 'react';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { AgenticAPI } from '@/lib/api';
import {
  BarChart3,
  Sparkles,
  Play,
  Database,
  Table,
  ShieldCheck,
  AlertCircle,
  Clock,
  Terminal,
  Layers,
  CheckCircle2,
} from 'lucide-react';

export default function AnalyticsPage() {
  return (
    <ProtectedRoute>
      <AnalyticsStudioContent />
    </ProtectedRoute>
  );
}

function AnalyticsStudioContent() {
  const [queryInput, setQueryInput] = useState('Analyze average lab turnaround time and abnormal test rates');
  const [chartType, setChartType] = useState('bar');
  const [executing, setExecuting] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const sampleQueries = [
    'Analyze average lab turnaround time and abnormal test rates',
    'Calculate distribution of claims by status and total value',
    'Summarize patient health score risk stratification count',
  ];

  const handleRun = async () => {
    if (!queryInput.trim()) return;
    setExecuting(true);
    setError(null);
    try {
      const data = await AgenticAPI.queryAnalytics(queryInput, chartType);
      setResult(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to execute healthcare analytical query.');
    } finally {
      setExecuting(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8 border-b border-slate-800 pb-6">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-indigo-500/10 border border-indigo-500/30 rounded-xl text-indigo-400">
              <BarChart3 className="w-7 h-7" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
                AI Healthcare Data Analyst
                <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 font-mono">
                  DuckDB OLAP Engine
                </span>
              </h1>
              <p className="text-sm text-slate-400">
                Natural-language to SQL compiler with deterministic AST validation protecting against unauthorized DDL/DML.
              </p>
            </div>
          </div>
        </div>

        {/* Query Input Studio */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 mb-8 shadow-xl">
          <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
            Ask Analytical Query (Natural Language or SQL)
          </label>
          <div className="flex gap-3">
            <input
              type="text"
              value={queryInput}
              onChange={(e) => setQueryInput(e.target.value)}
              placeholder="e.g., Show me monthly high risk patient counts and reimbursement totals..."
              className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
            />
            <button
              onClick={handleRun}
              disabled={executing}
              className="flex items-center gap-2 px-6 py-3 bg-indigo-600 hover:bg-indigo-500 text-white font-bold rounded-xl text-sm transition shadow-lg shadow-indigo-900/30 disabled:opacity-50"
            >
              {executing ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 fill-white" /> Run Query
                </>
              )}
            </button>
          </div>

          {/* Quick suggestions */}
          <div className="flex items-center gap-2 mt-4 text-xs">
            <span className="text-slate-500">Preset Queries:</span>
            {sampleQueries.map((q, idx) => (
              <button
                key={idx}
                onClick={() => setQueryInput(q)}
                className="px-2.5 py-1 bg-slate-950 hover:bg-slate-800 border border-slate-800 text-slate-300 rounded-lg transition"
              >
                {q.substring(0, 32)}...
              </button>
            ))}
          </div>
        </div>

        {error && (
          <div className="mb-8 p-4 rounded-xl border bg-rose-500/10 border-rose-500/30 text-rose-300 flex items-center gap-3">
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            <span className="text-sm font-medium">{error}</span>
          </div>
        )}

        {/* Results Studio */}
        {result && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Insights & SQL Validation */}
            <div className="lg:col-span-4 space-y-6">
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3 flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-indigo-400" /> Executive Insights
                </h3>
                <p className="text-sm text-slate-300 leading-relaxed font-medium">
                  {result.summary || 'Analytical query completed successfully with validated DuckDB results.'}
                </p>
                <div className="mt-4 pt-3 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
                  <span>Execution: <strong className="text-white">{result.execution_time_ms} ms</strong></span>
                  <span>Rows: <strong className="text-white">{result.row_count}</strong></span>
                </div>
              </div>

              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3 flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" /> Validated SQL AST
                </h3>
                <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 font-mono text-xs text-emerald-400 overflow-x-auto">
                  {result.sql}
                </div>
                <div className="flex items-center gap-1.5 mt-3 text-[11px] text-emerald-400">
                  <CheckCircle2 className="w-3.5 h-3.5" /> AST verified read-only SELECT
                </div>
              </div>
            </div>

            {/* Data Table */}
            <div className="lg:col-span-8 bg-slate-900 border border-slate-800 rounded-2xl p-6">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-4 flex items-center gap-2">
                <Table className="w-4 h-4 text-indigo-400" /> Result Dataset ({result.row_count} records)
              </h3>
              <div className="overflow-x-auto max-h-[500px] border border-slate-800 rounded-xl">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-950 text-slate-400 uppercase font-bold sticky top-0 border-b border-slate-800">
                    <tr>
                      {result.columns?.map((col: string, idx: number) => (
                        <th key={idx} className="p-3">{col}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800 text-slate-300">
                    {result.data?.map((row: any, rIdx: number) => (
                      <tr key={rIdx} className="hover:bg-slate-950/50">
                        {result.columns?.map((col: string, cIdx: number) => (
                          <td key={cIdx} className="p-3 font-mono">{String(row[col] ?? '')}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

'use client';

import React, { useState, useEffect } from 'react';
import api from '@/lib/api';
import { useAuth } from '@/lib/authContext';
import { AdminHeader } from '@/components/admin/AdminHeader';
import { StatCard } from '@/components/admin/StatCard';

interface AIInsightsResponse {
  summary: string;
  aggregated_metrics: {
    total_users: number;
    total_hospitals: number;
    total_claims: number;
    approved_claims: number;
    rejected_claims: number;
    pending_claims: number;
    total_appointments: number;
    pending_documents: number;
  };
  generated_at: string;
  badge: string;
}

export default function AdminAIInsightsPage() {
  const { user } = useAuth();
  const [insights, setInsights] = useState<AIInsightsResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchInsights = async () => {
    setIsLoading(true);
    try {
      const res = await api.get<AIInsightsResponse>('/admin/ai-insights');
      setInsights(res.data);
    } catch (err) {
      console.error('Error fetching AI insights:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchInsights();
  }, []);

  const metrics = insights?.aggregated_metrics;

  return (
    <div className="space-y-6">
      <AdminHeader
        title="AI Operational Intelligence & Insights"
        subtitle="Executive AI-synthesized summaries of aggregated healthcare data, bottleneck analysis, settlement efficiency, and network recommendations."
        actions={
          <button
            onClick={fetchInsights}
            disabled={isLoading}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-semibold text-white bg-gradient-to-r from-blue-600 to-purple-600 hover:shadow-lg hover:shadow-purple-500/20 transition-all disabled:opacity-50"
          >
            <span className={`material-symbols-outlined text-sm ${isLoading ? 'animate-spin' : ''}`}>
              neurology
            </span>
            <span>Re-Generate AI Analysis</span>
          </button>
        }
      />

      {/* Aggregate Metric Highlights */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-gray-900/60 border border-white/10 rounded-2xl p-4">
          <span className="text-[10px] font-bold uppercase text-gray-400">Total Patient Network</span>
          <div className="text-xl font-extrabold text-white mt-1">{(metrics?.total_users ?? 0).toLocaleString()}</div>
          <span className="text-[10px] text-blue-400 font-semibold">Across Platform</span>
        </div>
        <div className="bg-gray-900/60 border border-white/10 rounded-2xl p-4">
          <span className="text-[10px] font-bold uppercase text-gray-400">Claims Approval Rate</span>
          <div className="text-xl font-extrabold text-emerald-400 mt-1">
            {metrics?.total_claims
              ? `${Math.round(((metrics.approved_claims || 0) / metrics.total_claims) * 100)}%`
              : '100%'}
          </div>
          <span className="text-[10px] text-gray-400">Adjudicated Settlements</span>
        </div>
        <div className="bg-gray-900/60 border border-white/10 rounded-2xl p-4">
          <span className="text-[10px] font-bold uppercase text-gray-400">Claims in Queue</span>
          <div className="text-xl font-extrabold text-amber-400 mt-1">{metrics?.pending_claims ?? 0}</div>
          <span className="text-[10px] text-amber-300">Pending Review</span>
        </div>
        <div className="bg-gray-900/60 border border-white/10 rounded-2xl p-4">
          <span className="text-[10px] font-bold uppercase text-gray-400">Document Bottlenecks</span>
          <div className="text-xl font-extrabold text-purple-400 mt-1">{metrics?.pending_documents ?? 0}</div>
          <span className="text-[10px] text-gray-400">Awaiting Verification</span>
        </div>
      </div>

      {/* AI Synthesis Card */}
      <div className="bg-gradient-to-br from-blue-900/20 via-purple-900/20 to-black border border-purple-500/30 rounded-3xl p-6 sm:p-8 shadow-2xl space-y-6 relative overflow-hidden">
        {/* Decorative Glow */}
        <div className="absolute top-0 right-0 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-white/10 relative z-10">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-lg">
              <span className="material-symbols-outlined text-white text-xl">psychology</span>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-bold text-white font-['Manrope']">Gemini AI Executive Operational Brief</h2>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-extrabold bg-purple-500/30 text-purple-300 border border-purple-400/40">
                  {insights?.badge || 'AI-Generated Operational Summary'}
                </span>
              </div>
              <p className="text-xs text-gray-400 mt-0.5">
                Evaluated from authorized aggregated platform telemetry. Strictly excludes raw patient PII.
              </p>
            </div>
          </div>

          <div className="text-[11px] text-gray-400 font-medium">
            Updated: <span className="text-gray-200">{insights?.generated_at || 'Just now'}</span>
          </div>
        </div>

        {isLoading ? (
          <div className="py-16 flex flex-col items-center justify-center gap-3">
            <div className="w-12 h-12 rounded-full border-2 border-purple-500/30 border-t-purple-400 animate-spin" />
            <span className="text-sm font-semibold text-gray-300">Synthesizing platform operational data...</span>
            <span className="text-xs text-gray-500">Evaluating settlement rates, capacity, and resource queues</span>
          </div>
        ) : (
          <div className="relative z-10 text-xs sm:text-sm text-gray-200 leading-relaxed font-normal whitespace-pre-line space-y-4 bg-black/40 border border-white/10 rounded-2xl p-6 shadow-inner">
            {insights?.summary || 'No operational summary available.'}
          </div>
        )}

        <div className="pt-4 border-t border-white/10 flex flex-col sm:flex-row items-center justify-between text-xs text-gray-400 gap-2">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-sm text-emerald-400">lock</span>
            <span>Compliance Notice: Telemetry is anonymized and adheres to healthcare privacy standards.</span>
          </div>
          <span className="text-[11px] text-purple-400 font-semibold">Gemini Flash Intelligence Engine</span>
        </div>
      </div>
    </div>
  );
}

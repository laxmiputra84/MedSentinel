'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { HealthDashboardData, LabTestItem, Recommendation } from '@/lib/types';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import api from '@/lib/api';

export default function HealthDashboardPage() {
  return (
    <ProtectedRoute>
      <HealthDashboardContent />
    </ProtectedRoute>
  );
}

function HealthDashboardContent() {
  const [data, setData] = useState<HealthDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedTest, setSelectedTest] = useState<string>('WBC');
  const [dateFilter, setDateFilter] = useState<'ALL' | '1M' | '6M' | '1Y'>('ALL');

  // FEATURE 21: Recommendation System State
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loadingRecs, setLoadingRecs] = useState(true);
  const [generatingRecs, setGeneratingRecs] = useState(false);
  const [recFilter, setRecFilter] = useState<'ALL' | 'DOCUMENTS' | 'TRENDS' | 'CLAIMS' | 'QUALITY'>('ALL');
  const [expandedRecId, setExpandedRecId] = useState<number | null>(null);

  const fetchDashboardData = async () => {
    try {
      const res = await api.get<HealthDashboardData>('/health/dashboard');
      setData(res.data);
      const testKeys = Object.keys(res.data.trends || {});
      if (testKeys.length > 0 && !testKeys.includes(selectedTest)) {
        setSelectedTest(testKeys[0]);
      }
    } catch (err) {
      console.error('Error fetching health dashboard:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchRecommendations = async () => {
    try {
      const res = await api.get<Recommendation[]>('/recommendations');
      setRecommendations(res.data);
    } catch (err) {
      console.error('Error fetching recommendations:', err);
    } finally {
      setLoadingRecs(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
    fetchRecommendations();
  }, []);

  // Update status (VIEWED, COMPLETED, DISMISSED)
  const handleUpdateStatus = async (recId: number, status: 'VIEWED' | 'DISMISSED' | 'COMPLETED') => {
    try {
      await api.patch(`/recommendations/${recId}/status`, { status });
      setRecommendations((prev) =>
        prev.map((r) => (r.id === recId ? { ...r, status } : r))
      );
    } catch (err) {
      console.error('Error updating recommendation status:', err);
    }
  };

  // Generate on-demand hybrid recommendations
  const handleGenerateRecommendations = async () => {
    setGeneratingRecs(true);
    try {
      const res = await api.post<Recommendation[]>('/recommendations/generate/me');
      setRecommendations(res.data);
    } catch (err) {
      console.error('Error generating recommendations:', err);
    } finally {
      setGeneratingRecs(false);
    }
  };

  const filteredRecommendations = recommendations.filter((rec) => {
    if (recFilter === 'ALL') return true;
    if (recFilter === 'DOCUMENTS')
      return ['MISSING_RECORD', 'RELATED_RECORD', 'DOCUMENT_FOLLOW_UP'].includes(rec.recommendation_type);
    if (recFilter === 'TRENDS') return rec.recommendation_type === 'TREND_REVIEW';
    if (recFilter === 'CLAIMS') return rec.recommendation_type === 'CLAIM_SUPPORT';
    if (recFilter === 'QUALITY') return rec.recommendation_type === 'DATA_QUALITY';
    return true;
  });

  const trends = data?.trends || {};
  const availableTests = Object.keys(trends);
  const currentTestPoints = trends[selectedTest] || [];

  const filteredPoints = currentTestPoints.filter((pt) => {
    if (dateFilter === 'ALL') return true;
    const ptDate = new Date(pt.date);
    const now = new Date();
    if (dateFilter === '1M') {
      const oneMonthAgo = new Date();
      oneMonthAgo.setMonth(now.getMonth() - 1);
      return ptDate >= oneMonthAgo;
    }
    if (dateFilter === '6M') {
      const sixMonthsAgo = new Date();
      sixMonthsAgo.setMonth(now.getMonth() - 6);
      return ptDate >= sixMonthsAgo;
    }
    if (dateFilter === '1Y') {
      const oneYearAgo = new Date();
      oneYearAgo.setFullYear(now.getFullYear() - 1);
      return ptDate >= oneYearAgo;
    }
    return true;
  });

  const renderChart = () => {
    if (filteredPoints.length === 0) {
      return (
        <div className="h-64 flex flex-col items-center justify-center text-gray-500 text-xs">
          <span className="material-symbols-outlined text-4xl mb-2">show_chart</span>
          No historical records recorded for {selectedTest} yet.
        </div>
      );
    }

    const values = filteredPoints.map((p) => p.value);
    const minVal = Math.min(...values) * 0.85;
    const maxVal = Math.max(...values) * 1.15;
    const valRange = maxVal - minVal || 1;

    const width = 600;
    const height = 200;
    const padding = 30;

    const pointsCoordinates = filteredPoints.map((p, idx) => {
      const x = padding + (idx / Math.max(filteredPoints.length - 1, 1)) * (width - 2 * padding);
      const y = height - padding - ((p.value - minVal) / valRange) * (height - 2 * padding);
      return { x, y, point: p };
    });

    const pathD = pointsCoordinates
      .map((pt, i) => `${i === 0 ? 'M' : 'L'} ${pt.x.toFixed(1)} ${pt.y.toFixed(1)}`)
      .join(' ');

    const refMin = filteredPoints[0]?.reference_min;
    const refMax = filteredPoints[0]?.reference_max;

    const refMinY = refMin !== undefined && refMin !== null
      ? height - padding - ((refMin - minVal) / valRange) * (height - 2 * padding)
      : null;
    const refMaxY = refMax !== undefined && refMax !== null
      ? height - padding - ((refMax - minVal) / valRange) * (height - 2 * padding)
      : null;

    return (
      <div className="w-full overflow-x-auto">
        <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-64 overflow-visible">
          <defs>
            <linearGradient id="lineGrad" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor="#3b82f6" />
              <stop offset="100%" stopColor="#8b5cf6" />
            </linearGradient>
          </defs>

          {/* Grid lines */}
          <line x1={padding} y1={padding} x2={width - padding} y2={padding} stroke="#374151" strokeDasharray="3 3" />
          <line x1={padding} y1={height / 2} x2={width - padding} y2={height / 2} stroke="#374151" strokeDasharray="3 3" />
          <line x1={padding} y1={height - padding} x2={width - padding} y2={height - padding} stroke="#4b5563" />

          {/* Reference Max Line */}
          {refMaxY !== null && refMaxY >= padding && refMaxY <= height - padding && (
            <g>
              <line
                x1={padding}
                y1={refMaxY}
                x2={width - padding}
                y2={refMaxY}
                stroke="#10b981"
                strokeWidth="1"
                strokeDasharray="4 4"
              />
              <text x={width - padding + 5} y={refMaxY + 3} fill="#10b981" fontSize="9">
                Max ({refMax})
              </text>
            </g>
          )}

          {/* Reference Min Line */}
          {refMinY !== null && refMinY >= padding && refMinY <= height - padding && (
            <g>
              <line
                x1={padding}
                y1={refMinY}
                x2={width - padding}
                y2={refMinY}
                stroke="#10b981"
                strokeWidth="1"
                strokeDasharray="4 4"
              />
              <text x={width - padding + 5} y={refMinY + 3} fill="#10b981" fontSize="9">
                Min ({refMin})
              </text>
            </g>
          )}

          {/* Data Path */}
          <path d={pathD} fill="none" stroke="url(#lineGrad)" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />

          {/* Data Dots */}
          {pointsCoordinates.map((pt, i) => (
            <g key={i} className="group cursor-pointer">
              <circle
                cx={pt.x}
                cy={pt.y}
                r="5"
                className={
                  pt.point.status === 'CRITICAL'
                    ? 'fill-red-500 stroke-white'
                    : pt.point.status === 'HIGH' || pt.point.status === 'LOW'
                    ? 'fill-amber-400 stroke-white'
                    : 'fill-blue-500 stroke-white'
                }
                strokeWidth="2"
              />
              <text
                x={pt.x}
                y={pt.y - 10}
                textAnchor="middle"
                fill="#ffffff"
                fontSize="10"
                fontWeight="bold"
              >
                {pt.point.value}
              </text>
              <text
                x={pt.x}
                y={height - padding + 15}
                textAnchor="middle"
                fill="#9ca3af"
                fontSize="9"
              >
                {pt.point.date}
              </text>
            </g>
          ))}
        </svg>
      </div>
    );
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-10">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-blue-950 backdrop-blur-2xl rounded-3xl p-8 sm:p-12 border border-blue-500/20 shadow-2xl flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
        <div>
          <span className="px-3 py-1 rounded-full bg-blue-500/20 text-blue-300 text-xs font-bold uppercase tracking-wider border border-blue-400/30">
            Real-Time Clinical Telemetry
          </span>
          <h1 className="text-3xl sm:text-5xl font-extrabold text-white font-['Manrope'] mt-2 mb-2 tracking-tight">
            Medical Health Dashboard
          </h1>
          <p className="text-blue-100/80 text-sm max-w-2xl leading-relaxed">
            Monitor patient health scores, evaluate physiological risk levels, review explainable AI recommendations, and track laboratory trends over time.
          </p>
        </div>

        <div className="flex gap-3">
          <Link
            href="/medical-vault"
            className="px-5 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold rounded-xl text-xs shadow-lg transition-all flex items-center gap-2"
          >
            <span className="material-symbols-outlined text-sm">upload_file</span>
            Upload Lab Record →
          </Link>
        </div>
      </div>

      {/* FEATURE 11: CRITICAL VALUE ALERTS BANNER */}
      {data && data.critical_alerts && data.critical_alerts.length > 0 && (
        <div className="bg-gradient-to-r from-red-950 via-red-900 to-rose-950 border-2 border-red-500/70 rounded-3xl p-6 sm:p-8 shadow-2xl space-y-4 animate-pulse">
          <div className="flex items-center gap-3">
            <span className="p-3 bg-red-600 rounded-2xl text-white material-symbols-outlined text-3xl">
              warning
            </span>
            <div>
              <span className="text-red-300 uppercase tracking-widest text-xs font-bold">Priority Escalation Notice</span>
              <h2 className="text-xl sm:text-2xl font-black text-white font-['Manrope']">
                CRITICAL LAB VALUE DETECTED
              </h2>
            </div>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 pt-2">
            {data.critical_alerts.map((alert, idx) => (
              <div key={idx} className="bg-black/40 border border-red-500/40 rounded-2xl p-4 space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-white text-sm">{alert.name}</span>
                  <span className="px-2 py-0.5 bg-red-600 text-white text-[10px] font-black rounded-md">
                    CRITICAL
                  </span>
                </div>
                <div className="text-xl font-extrabold text-red-300 font-mono">
                  {alert.value} <span className="text-xs text-gray-300">{alert.unit}</span>
                </div>
                <div className="text-[11px] text-gray-400">
                  Standard Interval: {alert.reference_min} - {alert.reference_max} {alert.unit}
                </div>
              </div>
            ))}
          </div>

          <div className="p-4 bg-black/50 border border-white/10 rounded-2xl text-xs text-red-200 leading-relaxed">
            <strong>Emergency Clinical Advisory:</strong> Please contact a qualified healthcare professional or emergency service immediately if instructed by your healthcare provider or if severe symptoms are present. MedSentinel does not provide an emergency response or medical diagnosis.
          </div>
        </div>
      )}

      {/* FEATURE 10: KPI CARDS */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
        {/* Total Documents */}
        <div className="bg-gray-900/80 border border-white/10 rounded-2xl p-5 backdrop-blur-xl space-y-2">
          <span className="text-gray-400 text-xs font-semibold">Total Documents</span>
          <div className="text-2xl sm:text-3xl font-black text-white font-['Manrope']">
            {loading ? '...' : data?.total_documents ?? 0}
          </div>
          <span className="text-[11px] text-blue-400 flex items-center gap-1">
            <span className="material-symbols-outlined text-xs">folder</span> Private Vault
          </span>
        </div>

        {/* Latest Lab Reports */}
        <div className="bg-gray-900/80 border border-white/10 rounded-2xl p-5 backdrop-blur-xl space-y-2">
          <span className="text-gray-400 text-xs font-semibold">Lab Reports</span>
          <div className="text-2xl sm:text-3xl font-black text-purple-300 font-['Manrope']">
            {loading ? '...' : data?.latest_lab_reports_count ?? 0}
          </div>
          <span className="text-[11px] text-purple-400 flex items-center gap-1">
            <span className="material-symbols-outlined text-xs">biochemistry</span> OCR Extracted
          </span>
        </div>

        {/* 🟢 Normal Results */}
        <div className="bg-gray-900/80 border border-white/10 rounded-2xl p-5 backdrop-blur-xl space-y-2">
          <span className="text-gray-400 text-xs font-semibold">Normal Results</span>
          <div className="text-2xl sm:text-3xl font-black text-emerald-400 font-['Manrope']">
            {loading ? '...' : data?.normal_results_count ?? 0}
          </div>
          <span className="text-[11px] text-emerald-400 flex items-center gap-1">
            <span className="material-symbols-outlined text-xs">check_circle</span> In Reference Range
          </span>
        </div>

        {/* 🟡 Abnormal Results */}
        <div className="bg-gray-900/80 border border-white/10 rounded-2xl p-5 backdrop-blur-xl space-y-2">
          <span className="text-gray-400 text-xs font-semibold">Abnormal Results</span>
          <div className="text-2xl sm:text-3xl font-black text-amber-400 font-['Manrope']">
            {loading ? '...' : data?.abnormal_results_count ?? 0}
          </div>
          <span className="text-[11px] text-amber-400 flex items-center gap-1">
            <span className="material-symbols-outlined text-xs">error</span> Mild Fluctuation
          </span>
        </div>

        {/* 🔴 Critical Results */}
        <div className="bg-gray-900/80 border border-white/10 rounded-2xl p-5 backdrop-blur-xl space-y-2">
          <span className="text-gray-400 text-xs font-semibold">Critical Values</span>
          <div className="text-2xl sm:text-3xl font-black text-red-400 font-['Manrope']">
            {loading ? '...' : data?.critical_results_count ?? 0}
          </div>
          <span className="text-[11px] text-red-400 flex items-center gap-1">
            <span className="material-symbols-outlined text-xs">emergency</span> Escalation Alert
          </span>
        </div>
      </div>

      {/* FEATURE 4 & 5: HEALTH & RISK SCORE SECTION */}
      <div className="grid lg:grid-cols-3 gap-8">
        {/* Score Meters */}
        <div className="lg:col-span-1 bg-gray-900/80 border border-white/10 rounded-3xl p-6 sm:p-8 backdrop-blur-xl space-y-6">
          <h2 className="text-lg font-bold text-white font-['Manrope'] flex items-center gap-2">
            <span className="material-symbols-outlined text-blue-400">vital_signs</span>
            Clinical Risk Metrics
          </h2>

          {/* Health Score Card */}
          <div className="p-5 bg-black/40 border border-white/10 rounded-2xl space-y-3">
            <div className="flex justify-between items-center text-xs">
              <span className="text-gray-400 font-semibold">Health Score</span>
              <span className="text-emerald-400 font-bold">Optimal Target: 80-100</span>
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-4xl font-extrabold text-white font-['Manrope']">
                {loading ? '--' : data?.health_score ?? 85}
              </span>
              <span className="text-xs text-gray-500">/ 100</span>
            </div>
            {/* Progress Bar */}
            <div className="w-full h-2.5 bg-gray-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-blue-500 to-emerald-400 transition-all duration-700"
                style={{ width: `${data?.health_score ?? 85}%` }}
              ></div>
            </div>
          </div>

          {/* Risk Level Card */}
          <div className="p-5 bg-black/40 border border-white/10 rounded-2xl space-y-3">
            <div className="flex justify-between items-center text-xs">
              <span className="text-gray-400 font-semibold">Physiological Risk Level</span>
              <span
                className={`px-2.5 py-0.5 rounded text-[11px] font-bold ${
                  data?.risk_level === 'LOW'
                    ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                    : data?.risk_level === 'MODERATE'
                    ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                    : 'bg-red-500/20 text-red-300 border border-red-500/30'
                }`}
              >
                {loading ? '...' : data?.risk_level ?? 'LOW'}
              </span>
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-4xl font-extrabold text-white font-['Manrope']">
                {loading ? '--' : data?.risk_score ?? 15}
              </span>
              <span className="text-xs text-gray-500">Risk Points (0-100)</span>
            </div>
            <p className="text-[11px] text-gray-400 leading-relaxed">
              0–20: LOW • 21–50: MODERATE • 51–75: HIGH • 76–100: CRITICAL
            </p>
          </div>
        </div>

        {/* AI Health Summary Card */}
        <div className="lg:col-span-2 bg-gray-900/80 border border-white/10 rounded-3xl p-6 sm:p-8 backdrop-blur-xl flex flex-col justify-between space-y-6">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-bold text-white font-['Manrope'] flex items-center gap-2">
                <span className="material-symbols-outlined text-indigo-400">neurology</span>
                AI-Powered Clinical Health Summary
              </h2>
              <span className="px-2.5 py-0.5 bg-indigo-500/20 text-indigo-300 text-[10px] font-bold rounded uppercase">
                Decision Support
              </span>
            </div>

            <div className="p-6 bg-black/40 border border-white/5 rounded-2xl text-xs sm:text-sm text-gray-200 leading-relaxed whitespace-pre-line font-mono font-light">
              {loading
                ? 'Synthesizing clinical findings and calculating parameters...'
                : data?.ai_summary || 'No diagnostic records available.'}
            </div>
          </div>

          <div className="p-3.5 bg-blue-500/10 border border-blue-500/20 rounded-xl text-[11px] text-blue-200/90 leading-relaxed flex items-start gap-2">
            <span className="material-symbols-outlined text-sm text-blue-400 shrink-0 mt-0.5">verified_user</span>
            <span>
              <strong>Clinical Guardrail:</strong> MedSentinel summaries are generated for informational assistance and must never replace diagnostic judgment by a certified physician.
            </span>
          </div>
        </div>
      </div>

      {/* FEATURE 21: AI HYBRID RECOMMENDATION SYSTEM */}
      <div className="bg-gray-900/80 border border-white/10 rounded-3xl p-6 sm:p-8 backdrop-blur-xl space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full bg-purple-500/20 text-purple-300 text-[10px] font-bold uppercase tracking-wider border border-purple-400/30">
                Hybrid AI Intelligence
              </span>
              <span className="text-[11px] text-gray-400">Multi-Signal Evaluation</span>
            </div>
            <h2 className="text-xl sm:text-2xl font-bold text-white font-['Manrope'] mt-1 flex items-center gap-2">
              <span className="material-symbols-outlined text-purple-400">psychology</span>
              Explainable Clinical & Record Recommendations
            </h2>
            <p className="text-xs text-gray-400 mt-0.5">
              Personalized suggestions to complete records, review longitudinal trajectories, and optimize insurance claim documentation.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleGenerateRecommendations}
              disabled={generatingRecs}
              className="px-4 py-2 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-bold rounded-xl text-xs shadow-lg transition-all flex items-center gap-1.5 disabled:opacity-50"
            >
              <span className={`material-symbols-outlined text-sm ${generatingRecs ? 'animate-spin' : ''}`}>
                sync
              </span>
              {generatingRecs ? 'Analyzing Records...' : 'Refresh AI Recommendations'}
            </button>
          </div>
        </div>

        {/* Category Filters */}
        <div className="flex items-center gap-1 overflow-x-auto pb-1 text-xs">
          {[
            { id: 'ALL', label: 'All Recommendations' },
            { id: 'DOCUMENTS', label: 'Documents & Missing' },
            { id: 'TRENDS', label: 'Laboratory Trends' },
            { id: 'CLAIMS', label: 'Insurance Claims' },
            { id: 'QUALITY', label: 'Data Quality' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setRecFilter(tab.id as any)}
              className={`px-3.5 py-2 rounded-xl font-semibold transition-all whitespace-nowrap ${
                recFilter === tab.id
                  ? 'bg-purple-600 text-white shadow'
                  : 'bg-black/30 text-gray-400 hover:text-white border border-white/5'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Recommendations Cards Grid */}
        {loadingRecs ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-28 bg-gray-800/40 rounded-2xl animate-pulse"></div>
            ))}
          </div>
        ) : filteredRecommendations.length === 0 ? (
          <div className="p-8 text-center bg-black/30 rounded-2xl border border-white/5 space-y-2">
            <span className="material-symbols-outlined text-gray-500 text-4xl">task_alt</span>
            <p className="text-gray-300 font-bold text-sm">No Pending Recommendations</p>
            <p className="text-gray-500 text-xs max-w-sm mx-auto">
              Your medical vault and claims records are aligned. New suggestions will appear as additional records or lab results are uploaded.
            </p>
          </div>
        ) : (
          <div className="grid md:grid-cols-2 gap-4">
            {filteredRecommendations.map((rec) => {
              const isExpanded = expandedRecId === rec.id;
              const isHigh = rec.priority === 'HIGH';
              const isMedium = rec.priority === 'MEDIUM';

              return (
                <div
                  key={rec.id}
                  className={`bg-black/40 rounded-2xl p-5 border transition-all flex flex-col justify-between space-y-4 ${
                    rec.status === 'COMPLETED'
                      ? 'border-emerald-500/20 opacity-70'
                      : rec.status === 'DISMISSED'
                      ? 'border-gray-700/30 opacity-50'
                      : isHigh
                      ? 'border-red-500/50 shadow-lg shadow-red-950/30 ring-1 ring-red-500/30'
                      : isMedium
                      ? 'border-amber-500/40'
                      : 'border-white/10'
                  }`}
                >
                  <div className="space-y-2">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-2 flex-wrap">
                        {/* Priority Pill */}
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-black uppercase ${
                            isHigh
                              ? 'bg-red-500/20 text-red-300 border border-red-500/40'
                              : isMedium
                              ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                              : 'bg-blue-500/20 text-blue-300 border border-blue-500/40'
                          }`}
                        >
                          {rec.priority}
                        </span>

                        {/* Recommendation Type */}
                        <span className="px-2 py-0.5 rounded bg-white/10 text-gray-300 font-mono text-[10px]">
                          {rec.recommendation_type.replace('_', ' ')}
                        </span>

                        {/* Status badge */}
                        {rec.status !== 'ACTIVE' && (
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                              rec.status === 'COMPLETED'
                                ? 'bg-emerald-500/20 text-emerald-300'
                                : 'bg-gray-700/40 text-gray-400'
                            }`}
                          >
                            {rec.status}
                          </span>
                        )}
                      </div>

                      {/* Confidence Score */}
                      <span className="px-2 py-0.5 bg-purple-500/15 text-purple-300 text-[11px] font-bold rounded-lg border border-purple-500/20">
                        {Math.round(rec.confidence * 100)}% Confidence
                      </span>
                    </div>

                    <h3 className="text-white font-bold text-sm font-['Manrope']">{rec.title}</h3>

                    <p className="text-xs text-gray-300 leading-relaxed">{rec.description}</p>

                    {/* Explainable Reason Box */}
                    {rec.reason && (
                      <div className="p-3 bg-gray-900/60 rounded-xl border border-white/5 text-[11px] text-gray-300 space-y-1">
                        <span className="text-gray-400 font-semibold block text-[10px] uppercase tracking-wider">
                          Why MedSentinel Recommends This:
                        </span>
                        <p className="leading-relaxed">{rec.reason}</p>
                      </div>
                    )}

                    {/* Expandable Details & Sources */}
                    {isExpanded && (
                      <div className="pt-2 border-t border-white/5 space-y-2 text-[11px]">
                        {rec.sources && rec.sources.length > 0 && (
                          <div className="flex items-center gap-1.5 flex-wrap">
                            <span className="text-gray-400">Signals:</span>
                            {rec.sources.map((src, sIdx) => (
                              <span
                                key={sIdx}
                                className="px-1.5 py-0.5 bg-white/5 text-gray-300 text-[10px] font-mono rounded"
                              >
                                {src}
                              </span>
                            ))}
                          </div>
                        )}
                        <p className="text-gray-400 text-[10px] leading-relaxed italic">
                          Non-diagnostic advisory: Consult with a medical provider for treatment guidance.
                        </p>
                      </div>
                    )}
                  </div>

                  {/* Actions Footer */}
                  <div className="flex items-center justify-between pt-3 border-t border-white/5 gap-2 flex-wrap">
                    <button
                      onClick={() => setExpandedRecId(isExpanded ? null : rec.id)}
                      className="text-[11px] text-purple-400 hover:text-purple-300 font-semibold flex items-center gap-1"
                    >
                      <span className="material-symbols-outlined text-xs">
                        {isExpanded ? 'expand_less' : 'expand_more'}
                      </span>
                      {isExpanded ? 'Hide Details' : 'View Details'}
                    </button>

                    <div className="flex items-center gap-1.5">
                      {rec.status === 'ACTIVE' && (
                        <button
                          onClick={() => handleUpdateStatus(rec.id, 'VIEWED')}
                          className="px-2.5 py-1 bg-white/5 hover:bg-white/10 text-gray-300 rounded-lg text-[11px] font-semibold transition-colors"
                        >
                          Mark Viewed
                        </button>
                      )}

                      {rec.status !== 'COMPLETED' && (
                        <button
                          onClick={() => handleUpdateStatus(rec.id, 'COMPLETED')}
                          className="px-2.5 py-1 bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 border border-emerald-500/30 rounded-lg text-[11px] font-semibold transition-colors"
                        >
                          Complete
                        </button>
                      )}

                      {rec.status !== 'DISMISSED' && (
                        <button
                          onClick={() => handleUpdateStatus(rec.id, 'DISMISSED')}
                          className="p-1 text-gray-500 hover:text-red-400 rounded-lg transition-colors"
                          title="Dismiss recommendation"
                        >
                          <span className="material-symbols-outlined text-base">close</span>
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* FEATURE 6: HISTORICAL LABORATORY TRENDS SECTION */}
      <div className="bg-gray-900/80 border border-white/10 rounded-3xl p-6 sm:p-8 backdrop-blur-xl space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold text-white font-['Manrope'] flex items-center gap-2">
              <span className="material-symbols-outlined text-blue-400">trending_up</span>
              Laboratory History & Longitudinal Trends
            </h2>
            <p className="text-xs text-gray-400 mt-0.5">
              Select physiological markers to evaluate trajectories and reference intervals over time.
            </p>
          </div>

          {/* Date Filter Buttons */}
          <div className="flex items-center gap-1 bg-black/40 border border-white/10 p-1 rounded-xl text-xs">
            {(['ALL', '1M', '6M', '1Y'] as const).map((filter) => (
              <button
                key={filter}
                onClick={() => setDateFilter(filter)}
                className={`px-3 py-1.5 rounded-lg font-semibold transition-all ${
                  dateFilter === filter
                    ? 'bg-blue-600 text-white shadow'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                {filter === 'ALL' ? 'All Time' : filter}
              </button>
            ))}
          </div>
        </div>

        {/* Test Selector Tabs */}
        {availableTests.length > 0 ? (
          <div className="flex items-center gap-2 overflow-x-auto pb-2">
            {availableTests.map((tName) => (
              <button
                key={tName}
                onClick={() => setSelectedTest(tName)}
                className={`px-4 py-2 rounded-xl text-xs font-bold transition-all whitespace-nowrap ${
                  selectedTest === tName
                    ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg border border-blue-400/30'
                    : 'bg-black/30 text-gray-400 hover:text-white border border-white/5'
                }`}
              >
                {tName}
              </button>
            ))}
          </div>
        ) : (
          <div className="text-xs text-gray-400 p-4 bg-black/30 rounded-xl">
            No lab tests found. Upload a laboratory report in your Medical Vault to start tracking trends.
          </div>
        )}

        {/* Trend Chart */}
        <div className="p-6 bg-black/40 border border-white/10 rounded-2xl">
          <div className="flex justify-between items-center mb-4">
            <span className="text-xs font-bold text-gray-300">
              {selectedTest} Longitudinal Plot ({filteredPoints[0]?.unit || ''})
            </span>
            <span className="text-[11px] text-emerald-400 flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-emerald-400"></span> Normal Threshold Range
            </span>
          </div>
          {renderChart()}
        </div>
      </div>
    </div>
  );
}

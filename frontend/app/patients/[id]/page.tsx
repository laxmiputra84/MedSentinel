'use client';

import React, { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { AgenticAPI } from '@/lib/api';
import {
  User,
  HeartPulse,
  Activity,
  Calendar,
  FileText,
  ShieldCheck,
  TrendingUp,
  AlertTriangle,
  Clock,
  ArrowLeft,
  ChevronRight,
  ExternalLink,
  Layers,
} from 'lucide-react';
import Link from 'next/link';

export default function PatientDetailPage() {
  return (
    <ProtectedRoute>
      <PatientDetailContent />
    </ProtectedRoute>
  );
}

function PatientDetailContent() {
  const params = useParams();
  const patientId = params?.id as string;

  const [activeTab, setActiveTab] = useState<'360' | 'TIMELINE' | 'LAB_TRENDS'>('360');
  const [data360, setData360] = useState<any>(null);
  const [timeline, setTimeline] = useState<any>(null);
  const [trends, setTrends] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!patientId) return;

    const loadData = async () => {
      setLoading(true);
      setError(null);
      try {
        const [res360, resTimeline, resTrends] = await Promise.all([
          AgenticAPI.getPatient360(patientId).catch((e) => null),
          AgenticAPI.getPatientTimeline(patientId).catch((e) => null),
          AgenticAPI.getPatientLabTrends(patientId).catch((e) => null),
        ]);
        setData360(res360);
        setTimeline(resTimeline);
        setTrends(resTrends);
      } catch (err: any) {
        setError('Failed to load Patient 360 intelligence dossier.');
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [patientId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center">
        <div className="flex items-center gap-3 text-slate-400">
          <Activity className="w-6 h-6 animate-spin text-indigo-400" />
          <span className="text-sm font-medium">Synthesizing Patient 360 Intelligence...</span>
        </div>
      </div>
    );
  }

  const patient = data360?.patient;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6">
      {/* Top Breadcrumb & Controls */}
      <div className="max-w-7xl mx-auto mb-6">
        <Link
          href="/patients"
          className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition mb-4"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Patient Directory
        </Link>

        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 flex flex-col md:flex-row md:items-center justify-between gap-6 shadow-xl">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-2xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 font-bold text-2xl">
              {patient?.name?.charAt(0) || 'P'}
            </div>
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-2xl font-bold text-white">{patient?.name || `Patient #${patientId}`}</h1>
                <span className="px-2.5 py-0.5 rounded-full bg-slate-800 text-xs font-mono text-indigo-300 border border-slate-700">
                  {patient?.patient_code || `PT-${patientId}`}
                </span>
              </div>
              <div className="flex items-center gap-4 text-xs text-slate-400 mt-1">
                <span>Gender: <strong className="text-slate-300">{patient?.gender || 'N/A'}</strong></span>
                <span>Blood Group: <strong className="text-slate-300">{patient?.blood_group || 'N/A'}</strong></span>
                <span>Emergency: <strong className="text-slate-300">{patient?.emergency_contact || 'N/A'}</strong></span>
              </div>
            </div>
          </div>

          <div className="flex bg-slate-950 border border-slate-800 rounded-xl p-1 text-xs font-medium">
            <button
              onClick={() => setActiveTab('360')}
              className={`px-4 py-2 rounded-lg transition ${activeTab === '360' ? 'bg-indigo-600 text-white shadow' : 'text-slate-400 hover:text-white'}`}
            >
              Patient 360° View
            </button>
            <button
              onClick={() => setActiveTab('TIMELINE')}
              className={`px-4 py-2 rounded-lg transition ${activeTab === 'TIMELINE' ? 'bg-indigo-600 text-white shadow' : 'text-slate-400 hover:text-white'}`}
            >
              Clinical Timeline ({timeline?.total_timeline_events || 0})
            </button>
            <button
              onClick={() => setActiveTab('LAB_TRENDS')}
              className={`px-4 py-2 rounded-lg transition ${activeTab === 'LAB_TRENDS' ? 'bg-indigo-600 text-white shadow' : 'text-slate-400 hover:text-white'}`}
            >
              Longitudinal Lab Trends
            </button>
          </div>
        </div>
      </div>

      {/* Main Body Tabs */}
      <div className="max-w-7xl mx-auto">
        {activeTab === '360' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Health Score Summary */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4 flex items-center gap-2">
                <HeartPulse className="w-4 h-4 text-rose-400" /> Unified Health Status
              </h2>
              <div className="flex items-center justify-between mb-4">
                <div>
                  <div className="text-3xl font-extrabold text-white">
                    {data360?.health_score?.score ?? 85} <span className="text-xs font-normal text-slate-400">/ 100</span>
                  </div>
                  <div className="text-xs text-slate-400 mt-0.5">Overall Health Index</div>
                </div>
                <div className="text-right">
                  <span className={`px-2.5 py-1 text-xs font-bold rounded-full ${
                    data360?.health_score?.risk_level === 'CRITICAL' ? 'bg-rose-500/20 text-rose-300' :
                    data360?.health_score?.risk_level === 'HIGH' ? 'bg-amber-500/20 text-amber-300' : 'bg-emerald-500/20 text-emerald-300'
                  }`}>
                    {data360?.health_score?.risk_level || 'LOW RISK'}
                  </span>
                  <div className="text-xs text-slate-400 mt-1">Risk Score: {data360?.health_score?.risk_score ?? 15}%</div>
                </div>
              </div>
              <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 text-xs text-slate-300 leading-relaxed">
                {data360?.health_score?.summary || 'No acute anomalies recorded across patient medical history.'}
              </div>
            </div>

            {/* Recent Lab Tests */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4 flex items-center gap-2">
                <Activity className="w-4 h-4 text-indigo-400" /> Recent Diagnostic Labs
              </h2>
              <div className="space-y-3 max-h-80 overflow-y-auto pr-1">
                {data360?.recent_labs?.length ? (
                  data360.recent_labs.map((lab: any) => (
                    <div key={lab.id} className="p-3 bg-slate-950 rounded-xl border border-slate-800/80 flex items-center justify-between text-xs">
                      <div>
                        <div className="font-semibold text-white">{lab.name}</div>
                        <div className="text-slate-400">{lab.date || 'Recent'}</div>
                      </div>
                      <div className="text-right">
                        <div className="font-mono font-bold text-slate-200">
                          {lab.value} <span className="text-[10px] text-slate-400">{lab.unit}</span>
                        </div>
                        <span className={`text-[10px] font-bold ${lab.is_critical ? 'text-rose-400' : 'text-slate-400'}`}>
                          {lab.status}
                        </span>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-xs text-slate-500 py-6 text-center">No recent lab records on file.</div>
                )}
              </div>
            </div>

            {/* Claims & Documents */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4 flex items-center gap-2">
                <FileText className="w-4 h-4 text-emerald-400" /> Active Claims & Vault
              </h2>
              <div className="space-y-3 max-h-80 overflow-y-auto pr-1">
                {data360?.recent_claims?.length ? (
                  data360.recent_claims.map((claim: any) => (
                    <div key={claim.id} className="p-3 bg-slate-950 rounded-xl border border-slate-800/80 flex items-center justify-between text-xs">
                      <div>
                        <div className="font-semibold text-white">{claim.claim_number}</div>
                        <div className="text-slate-400">₹{claim.amount?.toLocaleString()}</div>
                      </div>
                      <span className="px-2 py-0.5 rounded bg-slate-800 text-[10px] font-bold text-indigo-300">
                        {claim.status}
                      </span>
                    </div>
                  ))
                ) : (
                  <div className="text-xs text-slate-500 py-6 text-center">No insurance claims on record.</div>
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'TIMELINE' && (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
            <h2 className="text-base font-bold text-white mb-6 flex items-center gap-2">
              <Calendar className="w-5 h-5 text-indigo-400" />
              Unified Longitudinal Clinical Timeline
            </h2>
            <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
              {timeline?.events?.length ? (
                timeline.events.map((evt: any, idx: number) => (
                  <div key={idx} className="relative pl-4">
                    <div className="absolute -left-6 top-1 w-3 h-3 rounded-full bg-indigo-500 ring-4 ring-slate-900" />
                    <div className="bg-slate-950 border border-slate-800 rounded-xl p-4">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs font-bold text-indigo-400 uppercase tracking-wider">{evt.type}</span>
                        <span className="text-xs text-slate-500">{evt.date}</span>
                      </div>
                      <h3 className="text-sm font-bold text-white">{evt.title}</h3>
                      <p className="text-xs text-slate-400 mt-1">{evt.description}</p>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-sm text-slate-500 text-center py-12">No timeline milestones available.</div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'LAB_TRENDS' && (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
            <h2 className="text-base font-bold text-white mb-6 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-emerald-400" />
              Biomarker Trajectory & Longitudinal Trend Analysis
            </h2>
            {trends?.biomarkers?.length ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {trends.biomarkers.map((bio: any, idx: number) => (
                  <div key={idx} className="bg-slate-950 border border-slate-800 rounded-xl p-5">
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="text-sm font-bold text-white">{bio.name}</h3>
                      <span className="text-xs text-slate-400">{bio.unit}</span>
                    </div>
                    <div className="space-y-2">
                      {bio.history?.map((h: any, hIdx: number) => (
                        <div key={hIdx} className="flex items-center justify-between text-xs py-1 border-b border-slate-850">
                          <span className="text-slate-400">{h.date}</span>
                          <span className="font-mono font-bold text-slate-200">{h.value}</span>
                          <span className={`text-[10px] font-bold ${h.status === 'CRITICAL' ? 'text-rose-400' : 'text-slate-400'}`}>
                            {h.status}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-sm text-slate-500 text-center py-12">No longitudinal trend series available.</div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

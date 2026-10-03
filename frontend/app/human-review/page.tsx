'use client';

import React, { useState, useEffect } from 'react';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { useAuth } from '@/lib/authContext';
import { AgenticAPI } from '@/lib/api';
import {
  ShieldAlert,
  CheckCircle,
  XCircle,
  AlertTriangle,
  UserCheck,
  Clock,
  RefreshCw,
  FileText,
  Activity,
  ArrowUpRight,
  Send,
  Search,
  Filter,
} from 'lucide-react';

export default function HumanReviewPage() {
  return (
    <ProtectedRoute>
      <HumanReviewDashboard />
    </ProtectedRoute>
  );
}

interface ReviewRecord {
  id: number;
  workflow_id: string;
  patient_id?: number;
  risk_level: string;
  trigger_reason: string;
  status: string;
  reviewer_comments?: string;
  created_at?: string;
  reviewed_at?: string;
  evidence?: any;
}

function HumanReviewDashboard() {
  const { user } = useAuth();
  const [reviews, setReviews] = useState<ReviewRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeFilter, setActiveFilter] = useState<'PENDING' | 'ESCALATED' | 'ALL'>('PENDING');
  const [selectedReview, setSelectedReview] = useState<ReviewRecord | null>(null);
  const [actionComments, setActionComments] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [feedbackMsg, setFeedbackMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const fetchReviews = async () => {
    setLoading(true);
    try {
      const data = await AgenticAPI.getHumanReviews(activeFilter === 'ALL' ? undefined : activeFilter);
      setReviews(data);
      if (data.length > 0 && !selectedReview) {
        setSelectedReview(data[0]);
      } else if (selectedReview) {
        const found = data.find((r: ReviewRecord) => r.id === selectedReview.id);
        setSelectedReview(found || (data.length > 0 ? data[0] : null));
      }
    } catch (err) {
      console.error('Error fetching human reviews:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReviews();
  }, [activeFilter]);

  const handleDecision = async (decision: 'APPROVE' | 'REJECT' | 'ESCALATE') => {
    if (!selectedReview) return;
    if (!actionComments.trim()) {
      setFeedbackMsg({ type: 'error', text: 'Clinical reviewer remarks are mandatory for audit compliance.' });
      return;
    }

    setSubmitting(true);
    setFeedbackMsg(null);
    try {
      if (decision === 'APPROVE') {
        await AgenticAPI.approveHumanReview(selectedReview.id, actionComments);
      } else if (decision === 'REJECT') {
        await AgenticAPI.rejectHumanReview(selectedReview.id, actionComments);
      } else {
        await AgenticAPI.escalateHumanReview(selectedReview.id, actionComments);
      }

      setFeedbackMsg({ type: 'success', text: `Review #${selectedReview.id} successfully recorded (${decision}).` });
      setActionComments('');
      await fetchReviews();
    } catch (err: any) {
      setFeedbackMsg({ type: 'error', text: err.response?.data?.detail || 'Failed to submit clinical decision.' });
    } finally {
      setSubmitting(false);
    }
  };

  const getRiskBadge = (level: string) => {
    switch (level?.toUpperCase()) {
      case 'CRITICAL':
        return <span className="px-2.5 py-1 text-xs font-bold rounded-full bg-rose-500/20 text-rose-400 border border-rose-500/30">CRITICAL</span>;
      case 'HIGH':
        return <span className="px-2.5 py-1 text-xs font-bold rounded-full bg-amber-500/20 text-amber-400 border border-amber-500/30">HIGH</span>;
      case 'MEDIUM':
        return <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-blue-500/20 text-blue-400 border border-blue-500/30">MEDIUM</span>;
      default:
        return <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">LOW</span>;
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6">
      {/* Header */}
      <div className="max-w-7xl mx-auto mb-8 flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-400">
              <ShieldAlert className="w-7 h-7" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
                Human-in-the-Loop Review Center
                <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                  Zero Autonomous Harm Policy
                </span>
              </h1>
              <p className="text-sm text-slate-400">
                Deterministic safety gate requiring authorized medical officer sign-off before releasing clinical or claims decisions.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex bg-slate-900 border border-slate-800 rounded-lg p-1 text-xs font-medium">
            <button
              onClick={() => setActiveFilter('PENDING')}
              className={`px-3 py-1.5 rounded-md transition ${activeFilter === 'PENDING' ? 'bg-indigo-600 text-white shadow' : 'text-slate-400 hover:text-white'}`}
            >
              Pending Reviews
            </button>
            <button
              onClick={() => setActiveFilter('ESCALATED')}
              className={`px-3 py-1.5 rounded-md transition ${activeFilter === 'ESCALATED' ? 'bg-amber-600 text-white shadow' : 'text-slate-400 hover:text-white'}`}
            >
              Escalated
            </button>
            <button
              onClick={() => setActiveFilter('ALL')}
              className={`px-3 py-1.5 rounded-md transition ${activeFilter === 'ALL' ? 'bg-slate-700 text-white shadow' : 'text-slate-400 hover:text-white'}`}
            >
              All History
            </button>
          </div>

          <button
            onClick={fetchReviews}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-semibold border border-slate-700 transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {feedbackMsg && (
        <div className={`max-w-7xl mx-auto mb-6 p-4 rounded-xl border flex items-center gap-3 ${feedbackMsg.type === 'success' ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300' : 'bg-rose-500/10 border-rose-500/30 text-rose-300'}`}>
          {feedbackMsg.type === 'success' ? <CheckCircle className="w-5 h-5 flex-shrink-0" /> : <AlertTriangle className="w-5 h-5 flex-shrink-0" />}
          <span className="text-sm font-medium">{feedbackMsg.text}</span>
        </div>
      )}

      {/* Main Grid */}
      <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Queue List */}
        <div className="lg:col-span-5 bg-slate-900/60 border border-slate-800 rounded-2xl p-4 flex flex-col h-[750px]">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-3">
            <span className="text-xs font-bold tracking-wider text-slate-400 uppercase">
              Assigned Queue ({reviews.length})
            </span>
            <span className="text-xs text-slate-500">Live SSE Synced</span>
          </div>

          <div className="overflow-y-auto space-y-2.5 flex-1 pr-1">
            {reviews.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center p-6 text-slate-500">
                <CheckCircle className="w-12 h-12 text-slate-600 mb-3 stroke-[1.5]" />
                <p className="text-sm font-medium text-slate-400">Queue is completely clear</p>
                <p className="text-xs text-slate-500 mt-1">All clinical escalations have been processed.</p>
              </div>
            ) : (
              reviews.map((rev) => {
                const isSelected = selectedReview?.id === rev.id;
                return (
                  <div
                    key={rev.id}
                    onClick={() => setSelectedReview(rev)}
                    className={`p-4 rounded-xl border cursor-pointer transition ${
                      isSelected
                        ? 'bg-indigo-950/40 border-indigo-500/50 shadow-lg ring-1 ring-indigo-500/20'
                        : 'bg-slate-900 border-slate-800/80 hover:border-slate-700'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-mono font-medium text-slate-400">
                        #{rev.id} · WF: {rev.workflow_id?.substring(0, 8)}...
                      </span>
                      {getRiskBadge(rev.risk_level)}
                    </div>
                    <p className="text-sm font-semibold text-slate-200 line-clamp-2">
                      {rev.trigger_reason}
                    </p>
                    <div className="flex items-center justify-between mt-3 pt-2 border-t border-slate-800/60 text-xs text-slate-400">
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3 text-slate-500" />
                        {rev.created_at ? new Date(rev.created_at).toLocaleTimeString() : 'Recent'}
                      </span>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        rev.status === 'PENDING' ? 'bg-amber-500/20 text-amber-300' :
                        rev.status === 'APPROVED' ? 'bg-emerald-500/20 text-emerald-300' :
                        rev.status === 'REJECTED' ? 'bg-rose-500/20 text-rose-300' : 'bg-indigo-500/20 text-indigo-300'
                      }`}>
                        {rev.status}
                      </span>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Right: Detailed Dossier & Action Panel */}
        <div className="lg:col-span-7 bg-slate-900/60 border border-slate-800 rounded-2xl p-6 flex flex-col h-[750px]">
          {selectedReview ? (
            <div className="flex flex-col h-full">
              {/* Header */}
              <div className="flex items-center justify-between pb-4 border-b border-slate-800">
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="text-lg font-bold text-white">Review Ticket #{selectedReview.id}</h2>
                    {getRiskBadge(selectedReview.risk_level)}
                  </div>
                  <p className="text-xs font-mono text-slate-400 mt-0.5">
                    Workflow Target: <span className="text-indigo-400">{selectedReview.workflow_id}</span>
                  </p>
                </div>
                <div className="text-right text-xs text-slate-400">
                  <div>Status: <span className="font-semibold text-white">{selectedReview.status}</span></div>
                  <div>Patient ID: <span className="font-mono text-slate-300">{selectedReview.patient_id ?? 'N/A'}</span></div>
                </div>
              </div>

              {/* Body */}
              <div className="flex-1 overflow-y-auto py-4 space-y-4 pr-1">
                {/* Escalation Trigger */}
                <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-4">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-rose-400 flex items-center gap-1.5 mb-2">
                    <AlertTriangle className="w-4 h-4" /> Trigger Rationale
                  </h3>
                  <p className="text-sm text-slate-200 leading-relaxed font-medium">
                    {selectedReview.trigger_reason}
                  </p>
                </div>

                {/* Agent Evidence & Output */}
                <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-4">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5 mb-2">
                    <FileText className="w-4 h-4 text-indigo-400" /> Evidence Dossier & Telemetry
                  </h3>
                  <div className="bg-slate-900 p-3 rounded-lg border border-slate-800 text-xs font-mono text-slate-300 overflow-x-auto max-h-48">
                    {selectedReview.evidence ? (
                      <pre>{JSON.stringify(selectedReview.evidence, null, 2)}</pre>
                    ) : (
                      <span className="text-slate-500">Autonomous workflow checkpoint data serialized under workflow ID {selectedReview.workflow_id}.</span>
                    )}
                  </div>
                </div>

                {/* Reviewer Action Input */}
                {selectedReview.status === 'PENDING' || selectedReview.status === 'ESCALATED' ? (
                  <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-4 space-y-3">
                    <label className="block text-xs font-bold uppercase tracking-wider text-slate-300">
                      Medical Officer Decision Notes *
                    </label>
                    <textarea
                      value={actionComments}
                      onChange={(e) => setActionComments(e.target.value)}
                      placeholder="Enter clinical assessment, rationale, or instructions for the treating team..."
                      rows={3}
                      className="w-full bg-slate-900 border border-slate-800 rounded-lg p-3 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
                    />

                    {/* Action Buttons */}
                    <div className="grid grid-cols-3 gap-3 pt-2">
                      <button
                        onClick={() => handleDecision('APPROVE')}
                        disabled={submitting}
                        className="flex items-center justify-center gap-2 px-4 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-bold transition shadow-lg shadow-emerald-900/20 disabled:opacity-50"
                      >
                        <CheckCircle className="w-4 h-4" />
                        Approve & Release
                      </button>
                      <button
                        onClick={() => handleDecision('REJECT')}
                        disabled={submitting}
                        className="flex items-center justify-center gap-2 px-4 py-2.5 bg-rose-600 hover:bg-rose-500 text-white rounded-xl text-xs font-bold transition shadow-lg shadow-rose-900/20 disabled:opacity-50"
                      >
                        <XCircle className="w-4 h-4" />
                        Reject Output
                      </button>
                      <button
                        onClick={() => handleDecision('ESCALATE')}
                        disabled={submitting}
                        className="flex items-center justify-center gap-2 px-4 py-2.5 bg-amber-600 hover:bg-amber-500 text-white rounded-xl text-xs font-bold transition shadow-lg shadow-amber-900/20 disabled:opacity-50"
                      >
                        <ArrowUpRight className="w-4 h-4" />
                        Escalate to Specialist
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-4">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
                      Recorded Decision Audit
                    </h3>
                    <p className="text-xs text-slate-300">
                      <strong>Remarks:</strong> {selectedReview.reviewer_comments || 'No remarks captured.'}
                    </p>
                    <p className="text-xs text-slate-500 mt-1">
                      Concluded on {selectedReview.reviewed_at ? new Date(selectedReview.reviewed_at).toLocaleString() : 'N/A'}.
                    </p>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-center text-slate-500">
              <UserCheck className="w-12 h-12 text-slate-600 mb-3" />
              <p className="text-sm font-medium text-slate-400">No review ticket selected</p>
              <p className="text-xs text-slate-500 mt-1">Select an item from the queue to view evidence and act.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

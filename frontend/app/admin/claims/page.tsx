'use client';

import React, { useState, useEffect } from 'react';
import api from '@/lib/api';
import { useAuth } from '@/lib/authContext';
import { AdminHeader } from '@/components/admin/AdminHeader';
import { FilterPanel } from '@/components/admin/FilterPanel';
import { DataTable, Column } from '@/components/admin/DataTable';

interface ClaimSummary {
  id: number;
  user_id: number;
  patient_name: string;
  patient_email: string;
  hospital_name: string;
  insurance_plan: string;
  claim_amount: number;
  claim_status: string;
  claim_description?: string;
  claim_date?: string;
}

interface ClaimDetail {
  id: number;
  patient: {
    id: number;
    name: string;
    email: string;
    phone?: string;
  };
  hospital: {
    name: string;
    location?: string;
  };
  insurance: {
    name: string;
    provider?: string;
  };
  claim_amount: number;
  claim_status: string;
  claim_description?: string;
  claim_date?: string;
  timeline_history: Array<{
    id: number;
    previous_status?: string;
    new_status: string;
    comment?: string;
    updated_by_name: string;
    created_at?: string;
  }>;
}

export default function AdminClaimsPage() {
  const { user } = useAuth();
  const [claims, setClaims] = useState<ClaimSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [isLoading, setIsLoading] = useState(true);

  // Detail / Status Transition Modal
  const [selectedClaimId, setSelectedClaimId] = useState<number | null>(null);
  const [claimDetail, setClaimDetail] = useState<ClaimDetail | null>(null);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);
  const [newStatus, setNewStatus] = useState('UNDER_REVIEW');
  const [statusComment, setStatusComment] = useState('');
  const [isUpdatingStatus, setIsUpdatingStatus] = useState(false);
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  const fetchClaims = async () => {
    setIsLoading(true);
    try {
      const params: any = { page, limit: 12 };
      if (statusFilter !== 'ALL') params.status = statusFilter;
      const res = await api.get('/admin/claims', { params });
      setClaims(res.data.items || []);
      setTotal(res.data.total || 0);
    } catch (err: any) {
      console.error('Error loading claims:', err);
      setFeedback({ type: 'error', message: err.response?.data?.detail || 'Failed to load claims.' });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchClaims();
  }, [page, statusFilter]);

  const openClaimDetail = async (claimId: number) => {
    setSelectedClaimId(claimId);
    setIsLoadingDetail(true);
    setStatusComment('');
    try {
      const res = await api.get<ClaimDetail>(`/admin/claims/${claimId}`);
      setClaimDetail(res.data);
      setNewStatus(res.data.claim_status);
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.response?.data?.detail || 'Failed to load claim details.' });
      setSelectedClaimId(null);
    } finally {
      setIsLoadingDetail(false);
    }
  };

  const handleUpdateStatus = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedClaimId) return;
    setIsUpdatingStatus(true);
    setFeedback(null);
    try {
      await api.patch(`/admin/claims/${selectedClaimId}/status`, {
        new_status: newStatus,
        comment: statusComment || `Status changed to ${newStatus} by medical underwriter.`,
      });
      setFeedback({ type: 'success', message: `Claim #${selectedClaimId} transitioned to ${newStatus}.` });
      setSelectedClaimId(null);
      fetchClaims();
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.response?.data?.detail || 'Status transition rejected.' });
    } finally {
      setIsUpdatingStatus(false);
    }
  };

  const getStatusBadge = (st: string) => {
    const map: Record<string, string> = {
      APPROVED: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40',
      REJECTED: 'bg-rose-500/20 text-rose-300 border-rose-500/40',
      UNDER_REVIEW: 'bg-blue-500/20 text-blue-300 border-blue-500/40',
      DOCUMENTS_REQUIRED: 'bg-amber-500/20 text-amber-300 border-amber-500/40',
      SUBMITTED: 'bg-purple-500/20 text-purple-300 border-purple-500/40',
      COMPLETED: 'bg-teal-500/20 text-teal-300 border-teal-500/40',
    };
    return (
      <span
        className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold border ${
          map[st] || 'bg-gray-700/40 text-gray-300 border-white/10'
        }`}
      >
        {st.replace('_', ' ')}
      </span>
    );
  };

  const columns: Column<ClaimSummary>[] = [
    {
      key: 'id',
      header: 'Claim ID & Patient',
      render: (c) => (
        <div>
          <div className="font-extrabold text-white text-xs flex items-center gap-1.5">
            <span className="text-blue-400">#{c.id}</span>
            <span>{c.patient_name}</span>
          </div>
          <div className="text-[11px] text-gray-400 truncate max-w-[170px]">{c.patient_email}</div>
        </div>
      ),
    },
    {
      key: 'hospital_name',
      header: 'Hospital & Plan',
      render: (c) => (
        <div>
          <div className="text-gray-200 text-xs font-semibold">{c.hospital_name}</div>
          <div className="text-[11px] text-purple-400">{c.insurance_plan}</div>
        </div>
      ),
    },
    {
      key: 'claim_amount',
      header: 'Amount (₹)',
      render: (c) => (
        <span className="font-extrabold text-white text-xs">
          ₹{c.claim_amount ? c.claim_amount.toLocaleString() : '0.00'}
        </span>
      ),
    },
    {
      key: 'claim_status',
      header: 'Claim Status',
      render: (c) => getStatusBadge(c.claim_status),
    },
    {
      key: 'claim_date',
      header: 'Filing Date',
      render: (c) => (
        <span className="text-gray-400 text-[11px]">
          {c.claim_date ? new Date(c.claim_date).toLocaleDateString() : '—'}
        </span>
      ),
    },
    {
      key: 'actions',
      header: 'Review & Action',
      align: 'right',
      render: (c) => (
        <button
          onClick={() => openClaimDetail(c.id)}
          className="px-3 py-1 rounded-lg bg-blue-600/80 hover:bg-blue-600 text-white font-semibold text-xs flex items-center gap-1 shadow transition-all"
        >
          <span className="material-symbols-outlined text-sm">visibility</span>
          <span>Review</span>
        </button>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <AdminHeader
        title="Insurance Claim Settlement Desk"
        subtitle="Perform medical underwriter evaluations, inspect clinical discharge files, approve settlements, and maintain compliant audit trails."
      />

      {feedback && (
        <div
          className={`p-4 rounded-2xl border text-xs flex items-center justify-between gap-3 ${
            feedback.type === 'success'
              ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
              : 'bg-red-500/10 border-red-500/30 text-red-300'
          }`}
        >
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-base">
              {feedback.type === 'success' ? 'check_circle' : 'error'}
            </span>
            <span>{feedback.message}</span>
          </div>
          <button onClick={() => setFeedback(null)} className="text-gray-400 hover:text-white">
            <span className="material-symbols-outlined text-sm">close</span>
          </button>
        </div>
      )}

      <FilterPanel
        filters={[
          {
            key: 'status',
            label: 'Status',
            value: statusFilter,
            onChange: (v) => {
              setStatusFilter(v);
              setPage(1);
            },
            options: [
              { label: 'All Claim Statuses', value: 'ALL' },
              { label: 'Under Review', value: 'UNDER_REVIEW' },
              { label: 'Documents Required', value: 'DOCUMENTS_REQUIRED' },
              { label: 'Approved', value: 'APPROVED' },
              { label: 'Rejected', value: 'REJECTED' },
              { label: 'Submitted', value: 'SUBMITTED' },
              { label: 'Completed', value: 'COMPLETED' },
            ],
          },
        ]}
        onReset={() => {
          setStatusFilter('ALL');
          setPage(1);
        }}
      />

      <DataTable
        columns={columns}
        data={claims}
        isLoading={isLoading}
        page={page}
        total={total}
        limit={12}
        onPageChange={(p) => setPage(p)}
        emptyMessage="No claims matching the selected filters."
      />

      {/* Claim Detail & Adjudication Modal */}
      {selectedClaimId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="fixed inset-0 bg-black/80 backdrop-blur-sm" onClick={() => setSelectedClaimId(null)} />
          <div className="relative bg-gray-900 border border-white/15 rounded-2xl max-w-2xl w-full p-6 shadow-2xl z-10 space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-3 border-b border-white/10">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-blue-400">receipt_long</span>
                <h3 className="text-base font-bold text-white font-['Manrope']">
                  Claim Adjudication & Audit: #{selectedClaimId}
                </h3>
              </div>
              <button onClick={() => setSelectedClaimId(null)} className="text-gray-400 hover:text-white">
                <span className="material-symbols-outlined text-lg">close</span>
              </button>
            </div>

            {isLoadingDetail ? (
              <div className="text-center py-12">
                <span className="material-symbols-outlined text-3xl text-blue-400 animate-spin">
                  progress_activity
                </span>
                <p className="text-xs text-gray-400 mt-2">Loading claim dossier...</p>
              </div>
            ) : claimDetail ? (
              <div className="space-y-4 text-xs">
                {/* High level overview grid */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-black/40 border border-white/10 rounded-xl p-3">
                  <div>
                    <span className="text-[10px] text-gray-400 font-bold uppercase">Patient</span>
                    <p className="text-white font-bold truncate">{claimDetail.patient.name}</p>
                    <p className="text-[10px] text-gray-400 truncate">{claimDetail.patient.email}</p>
                  </div>
                  <div>
                    <span className="text-[10px] text-gray-400 font-bold uppercase">Hospital</span>
                    <p className="text-white font-bold truncate">{claimDetail.hospital.name}</p>
                  </div>
                  <div>
                    <span className="text-[10px] text-gray-400 font-bold uppercase">Insurance Plan</span>
                    <p className="text-purple-400 font-bold truncate">{claimDetail.insurance.name}</p>
                  </div>
                  <div>
                    <span className="text-[10px] text-gray-400 font-bold uppercase">Claim Amount</span>
                    <p className="text-emerald-400 font-extrabold text-sm">₹{claimDetail.claim_amount.toLocaleString()}</p>
                  </div>
                </div>

                {claimDetail.claim_description && (
                  <div className="bg-white/5 border border-white/10 rounded-xl p-3">
                    <span className="text-[10px] text-gray-400 font-bold uppercase block mb-1">Clinical Diagnosis & Notes</span>
                    <p className="text-gray-200 leading-relaxed">{claimDetail.claim_description}</p>
                  </div>
                )}

                {/* Audit Timeline */}
                <div>
                  <h4 className="text-xs font-bold text-white uppercase tracking-wider mb-2 flex items-center gap-1.5">
                    <span className="material-symbols-outlined text-purple-400 text-sm">timeline</span>
                    <span>Claim Status Audit Trail</span>
                  </h4>
                  <div className="bg-black/30 border border-white/10 rounded-xl p-3 max-h-44 overflow-y-auto space-y-2">
                    {claimDetail.timeline_history.length === 0 ? (
                      <p className="text-gray-500 text-center py-2">No historical status modifications on record.</p>
                    ) : (
                      claimDetail.timeline_history.map((h) => (
                        <div key={h.id} className="flex items-start justify-between gap-3 text-[11px] pb-2 border-b border-white/5 last:border-none">
                          <div>
                            <span className="font-bold text-blue-400">{h.new_status}</span>
                            {h.comment && <p className="text-gray-300 text-[10px] mt-0.5">{h.comment}</p>}
                          </div>
                          <div className="text-right flex-shrink-0">
                            <span className="text-gray-400 font-medium">{h.updated_by_name}</span>
                            <span className="text-[10px] text-gray-500 block">
                              {h.created_at ? new Date(h.created_at).toLocaleString() : ''}
                            </span>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>

                {/* Status Transition Adjudication Form */}
                <form onSubmit={handleUpdateStatus} className="bg-gradient-to-br from-blue-900/20 to-purple-900/20 border border-blue-500/30 rounded-xl p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-white">Underwriter Status Decision</span>
                    <span className="text-[10px] text-gray-400">Current: {claimDetail.claim_status}</span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <label className="block text-gray-300 font-semibold mb-1">New Claim Status</label>
                      <select
                        value={newStatus}
                        onChange={(e) => setNewStatus(e.target.value)}
                        className="w-full bg-black/60 border border-white/15 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                      >
                        <option value="UNDER_REVIEW" className="bg-gray-900">UNDER REVIEW (In Process)</option>
                        <option value="DOCUMENTS_REQUIRED" className="bg-gray-900">DOCUMENTS REQUIRED (More Info Needed)</option>
                        <option value="APPROVED" className="bg-gray-900">APPROVED (Cashless Authorization)</option>
                        <option value="REJECTED" className="bg-gray-900">REJECTED (Denial with Reason)</option>
                        <option value="COMPLETED" className="bg-gray-900">COMPLETED (Funds Settled)</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-gray-300 font-semibold mb-1">Decision Comment / Audit Rationale</label>
                      <input
                        type="text"
                        required
                        placeholder="e.g. All hospital bills verified against policy coverage limits."
                        value={statusComment}
                        onChange={(e) => setStatusComment(e.target.value)}
                        className="w-full bg-black/60 border border-white/15 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                      />
                    </div>
                  </div>

                  <div className="flex items-center justify-end gap-2 pt-2">
                    <button
                      type="button"
                      onClick={() => setSelectedClaimId(null)}
                      className="px-3 py-1.5 rounded-xl border border-white/10 text-gray-300 hover:text-white"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={isUpdatingStatus}
                      className="px-4 py-1.5 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 text-white font-bold flex items-center gap-1 shadow"
                    >
                      {isUpdatingStatus && <span className="material-symbols-outlined text-sm animate-spin">progress_activity</span>}
                      <span>Commit Status Update</span>
                    </button>
                  </div>
                </form>
              </div>
            ) : null}
          </div>
        </div>
      )}
    </div>
  );
}

'use client';

import React, { useState, useEffect } from 'react';
import api from '@/lib/api';
import { useAuth } from '@/lib/authContext';
import { AdminHeader } from '@/components/admin/AdminHeader';
import { FilterPanel } from '@/components/admin/FilterPanel';
import { DataTable, Column } from '@/components/admin/DataTable';

interface DocumentRecord {
  id: number;
  user_id: number;
  patient_name: string;
  patient_email: string;
  doc_type: string;
  filename: string;
  file_path: string;
  file_size: number;
  status: string;
  upload_date?: string;
  verified_at?: string;
  rejection_reason?: string;
}

export default function AdminDocumentsPage() {
  const { user } = useAuth();
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [docTypeFilter, setDocTypeFilter] = useState('ALL');
  const [isLoading, setIsLoading] = useState(true);

  // Verification Decision Modal
  const [selectedDoc, setSelectedDoc] = useState<DocumentRecord | null>(null);
  const [decision, setDecision] = useState<'APPROVED' | 'REJECTED'>('APPROVED');
  const [rejectionReason, setRejectionReason] = useState('');
  const [isVerifying, setIsVerifying] = useState(false);
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  const fetchDocuments = async () => {
    setIsLoading(true);
    try {
      const params: any = { page, limit: 12 };
      if (statusFilter !== 'ALL') params.status = statusFilter;
      if (docTypeFilter !== 'ALL') params.doc_type = docTypeFilter;
      const res = await api.get('/admin/documents', { params });
      setDocuments(res.data.items || []);
      setTotal(res.data.total || 0);
    } catch (err: any) {
      console.error('Error fetching documents:', err);
      setFeedback({ type: 'error', message: err.response?.data?.detail || 'Failed to load documents.' });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, [page, statusFilter, docTypeFilter]);

  const openVerifyModal = (doc: DocumentRecord, action: 'APPROVED' | 'REJECTED') => {
    setSelectedDoc(doc);
    setDecision(action);
    setRejectionReason(action === 'REJECTED' ? 'Document image is blurred or missing official hospital stamp.' : '');
  };

  const handleCommitVerification = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedDoc) return;
    setIsVerifying(true);
    setFeedback(null);
    try {
      await api.patch(`/admin/documents/${selectedDoc.id}/verify`, {
        status: decision,
        rejection_reason: decision === 'REJECTED' ? rejectionReason : undefined,
      });
      setFeedback({
        type: 'success',
        message: `Document #${selectedDoc.id} (${selectedDoc.doc_type}) successfully marked as ${decision}.`,
      });
      setSelectedDoc(null);
      fetchDocuments();
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.response?.data?.detail || 'Verification update failed.' });
    } finally {
      setIsVerifying(false);
    }
  };

  const columns: Column<DocumentRecord>[] = [
    {
      key: 'filename',
      header: 'File & Patient Info',
      render: (d) => (
        <div>
          <div className="font-bold text-white text-xs flex items-center gap-1.5 truncate max-w-[200px]">
            <span className="material-symbols-outlined text-sm text-blue-400">description</span>
            <span className="truncate">{d.filename}</span>
          </div>
          <div className="text-[11px] text-gray-400 mt-0.5">
            Patient: <span className="text-gray-300 font-semibold">{d.patient_name}</span> ({d.patient_email})
          </div>
        </div>
      ),
    },
    {
      key: 'doc_type',
      header: 'Document Type',
      render: (d) => (
        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-white/5 border border-white/10 text-gray-300">
          {d.doc_type}
        </span>
      ),
    },
    {
      key: 'status',
      header: 'Verification Status',
      render: (d) => {
        const badgeColors: Record<string, string> = {
          APPROVED: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40',
          REJECTED: 'bg-rose-500/20 text-rose-300 border-rose-500/40',
          PENDING: 'bg-amber-500/20 text-amber-300 border-amber-500/40',
        };
        return (
          <div>
            <span
              className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold border ${
                badgeColors[d.status] || 'bg-gray-700/40 text-gray-300 border-white/10'
              }`}
            >
              {d.status}
            </span>
            {d.rejection_reason && (
              <span className="text-[10px] text-rose-400 block mt-0.5 truncate max-w-[150px]">
                {d.rejection_reason}
              </span>
            )}
          </div>
        );
      },
    },
    {
      key: 'upload_date',
      header: 'Uploaded Date',
      render: (d) => (
        <span className="text-gray-400 text-[11px]">
          {d.upload_date ? new Date(d.upload_date).toLocaleDateString() : '—'}
        </span>
      ),
    },
    {
      key: 'actions',
      header: 'Admin Decision',
      align: 'right',
      render: (d) => (
        <div className="flex items-center justify-end gap-1.5">
          {d.status === 'PENDING' ? (
            <>
              <button
                onClick={() => openVerifyModal(d, 'APPROVED')}
                className="px-2.5 py-1 rounded-lg bg-emerald-600/80 hover:bg-emerald-600 text-white font-semibold text-xs flex items-center gap-1 shadow"
              >
                <span className="material-symbols-outlined text-xs">check</span>
                <span>Approve</span>
              </button>
              <button
                onClick={() => openVerifyModal(d, 'REJECTED')}
                className="px-2.5 py-1 rounded-lg bg-red-600/80 hover:bg-red-600 text-white font-semibold text-xs flex items-center gap-1 shadow"
              >
                <span className="material-symbols-outlined text-xs">close</span>
                <span>Reject</span>
              </button>
            </>
          ) : (
            <button
              onClick={() => openVerifyModal(d, d.status === 'APPROVED' ? 'REJECTED' : 'APPROVED')}
              className="px-2.5 py-1 rounded-lg bg-white/5 hover:bg-white/10 text-gray-300 hover:text-white border border-white/10 text-xs font-semibold"
            >
              Change Decision
            </button>
          )}
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <AdminHeader
        title="Medical Document Verification Desk"
        subtitle="Review uploaded identity proofs, insurance policy cards, diagnostic reports, and discharge summaries with human-in-the-loop validation."
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
              { label: 'All Documents', value: 'ALL' },
              { label: 'Pending Verification', value: 'PENDING' },
              { label: 'Approved Documents', value: 'APPROVED' },
              { label: 'Rejected Documents', value: 'REJECTED' },
            ],
          },
          {
            key: 'doc_type',
            label: 'Document Type',
            value: docTypeFilter,
            onChange: (v) => {
              setDocTypeFilter(v);
              setPage(1);
            },
            options: [
              { label: 'All Types', value: 'ALL' },
              { label: 'Discharge Summary', value: 'Discharge Summary' },
              { label: 'Insurance Card', value: 'Insurance Card' },
              { label: 'Government ID', value: 'Government ID' },
              { label: 'Medical Prescription', value: 'Prescription' },
            ],
          },
        ]}
        onReset={() => {
          setStatusFilter('ALL');
          setDocTypeFilter('ALL');
          setPage(1);
        }}
      />

      <DataTable
        columns={columns}
        data={documents}
        isLoading={isLoading}
        page={page}
        total={total}
        limit={12}
        onPageChange={(p) => setPage(p)}
        emptyMessage="No documents currently in the verification queue."
      />

      {/* Verification Modal */}
      {selectedDoc && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="fixed inset-0 bg-black/80 backdrop-blur-sm" onClick={() => setSelectedDoc(null)} />
          <div className="relative bg-gray-900 border border-white/15 rounded-2xl max-w-md w-full p-6 shadow-2xl z-10 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-white/10">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-blue-400">verified</span>
                <h3 className="text-base font-bold text-white font-['Manrope']">
                  {decision === 'APPROVED' ? 'Approve Document' : 'Reject Document'}
                </h3>
              </div>
              <button onClick={() => setSelectedDoc(null)} className="text-gray-400 hover:text-white">
                <span className="material-symbols-outlined text-lg">close</span>
              </button>
            </div>

            <form onSubmit={handleCommitVerification} className="space-y-4 text-xs">
              <div className="bg-black/40 border border-white/10 rounded-xl p-3 space-y-1">
                <div className="text-white font-bold truncate">{selectedDoc.filename}</div>
                <div className="text-gray-400 text-[11px]">
                  Type: <span className="text-gray-200">{selectedDoc.doc_type}</span> | Owner:{' '}
                  <span className="text-gray-200">{selectedDoc.patient_name}</span>
                </div>
              </div>

              <div>
                <label className="block text-gray-300 font-semibold mb-1">Verification Decision</label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => setDecision('APPROVED')}
                    className={`py-2 rounded-xl font-bold border transition-all text-xs flex items-center justify-center gap-1 ${
                      decision === 'APPROVED'
                        ? 'bg-emerald-600 text-white border-emerald-500 shadow'
                        : 'bg-white/5 border-white/10 text-gray-400 hover:text-white'
                    }`}
                  >
                    <span className="material-symbols-outlined text-sm">check_circle</span>
                    <span>Approve</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => setDecision('REJECTED')}
                    className={`py-2 rounded-xl font-bold border transition-all text-xs flex items-center justify-center gap-1 ${
                      decision === 'REJECTED'
                        ? 'bg-red-600 text-white border-red-500 shadow'
                        : 'bg-white/5 border-white/10 text-gray-400 hover:text-white'
                    }`}
                  >
                    <span className="material-symbols-outlined text-sm">cancel</span>
                    <span>Reject</span>
                  </button>
                </div>
              </div>

              {decision === 'REJECTED' && (
                <div>
                  <label className="block text-gray-300 font-semibold mb-1">Rejection Reason / Guidance for Patient *</label>
                  <textarea
                    required
                    rows={3}
                    value={rejectionReason}
                    onChange={(e) => setRejectionReason(e.target.value)}
                    placeholder="Provide specific feedback on why the document was denied..."
                    className="w-full bg-black/40 border border-white/10 rounded-xl p-2.5 text-white focus:outline-none focus:border-red-500"
                  />
                </div>
              )}

              <div className="pt-3 border-t border-white/10 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setSelectedDoc(null)}
                  className="px-3 py-1.5 rounded-xl border border-white/10 text-gray-300 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isVerifying}
                  className={`px-4 py-1.5 rounded-xl text-white font-bold flex items-center gap-1 shadow ${
                    decision === 'APPROVED'
                      ? 'bg-gradient-to-r from-emerald-600 to-teal-600'
                      : 'bg-gradient-to-r from-red-600 to-rose-600'
                  }`}
                >
                  {isVerifying && <span className="material-symbols-outlined text-sm animate-spin">progress_activity</span>}
                  <span>Confirm {decision}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

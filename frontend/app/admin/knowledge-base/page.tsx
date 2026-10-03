'use client';

import React, { useState, useEffect } from 'react';
import api from '@/lib/api';
import { useAuth } from '@/lib/authContext';
import { AdminHeader } from '@/components/admin/AdminHeader';
import { FilterPanel } from '@/components/admin/FilterPanel';
import { DataTable, Column } from '@/components/admin/DataTable';
import { StatCard } from '@/components/admin/StatCard';
import { ConfirmActionModal } from '@/components/admin/ConfirmActionModal';

interface DatasetItem {
  id: number;
  name: string;
  description?: string;
  file_name?: string;
  file_type?: string;
  source_type: string;
  uploaded_by?: number;
  status: string;
  visibility: string;
  hospital_id?: number;
  document_count: number;
  chunk_count: number;
  vector_count?: number;
  created_at?: string;
}

interface DocumentItem {
  id: number;
  dataset_id: number;
  title: string;
  content: string;
  visibility: string;
}

interface ChunkItem {
  id: number;
  document_id: number;
  chunk_index: number;
  content: string;
  embedding_reference?: string;
}

interface LogItem {
  id: number;
  status: string;
  message?: string;
  processed_at?: string;
}

interface TestSearchResult {
  query: string;
  total_vectors_in_store: number;
  matched_count: number;
  qdrant_healthy: boolean;
  retrieved_chunks: Array<{
    id: string;
    score: number;
    confidence: number;
    title: string;
    content: string;
    dataset_id?: number;
    visibility: string;
  }>;
}

interface RAGDebugInfo {
  dataset_status: string;
  document_count: number;
  chunk_count: number;
  embedding_count: number;
  vector_count: number;
  collection_name: string;
  last_processing_error?: string | null;
}

export default function AdminKnowledgeBasePage() {
  const { user } = useAuth();
  const [datasets, setDatasets] = useState<DatasetItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [visibilityFilter, setVisibilityFilter] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  // Upload Modal State
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [datasetName, setDatasetName] = useState('');
  const [datasetDesc, setDatasetDesc] = useState('');
  const [visibility, setVisibility] = useState('USER_AUTHORIZED');
  const [sourceType, setSourceType] = useState('ADMIN_UPLOAD');
  const [isUploading, setIsUploading] = useState(false);

  // Inspector Modals
  const [activeDataset, setActiveDataset] = useState<DatasetItem | null>(null);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [chunks, setChunks] = useState<ChunkItem[]>([]);
  const [logs, setLogs] = useState<LogItem[]>([]);
  const [viewMode, setViewMode] = useState<'NONE' | 'DOCS' | 'CHUNKS' | 'LOGS' | 'DEBUG'>('NONE');
  const [isLoadingDetails, setIsLoadingDetails] = useState(false);
  const [debugInfo, setDebugInfo] = useState<RAGDebugInfo | null>(null);

  // Test Search State
  const [testSearchOpen, setTestSearchOpen] = useState(false);
  const [testQuery, setTestQuery] = useState('Find cardiology hospitals in Bengaluru');
  const [testDatasetFilter, setTestDatasetFilter] = useState<number | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [searchResult, setSearchResult] = useState<TestSearchResult | null>(null);

  // Delete / Action Confirmation
  const [confirmDeleteId, setConfirmDeleteId] = useState<number | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  const fetchDatasets = async () => {
    setIsLoading(true);
    try {
      const params: any = {};
      if (statusFilter !== 'ALL') params.status = statusFilter;
      if (visibilityFilter !== 'ALL') params.visibility = visibilityFilter;
      const res = await api.get<DatasetItem[]>('/admin/datasets', { params });
      setDatasets(res.data || []);
    } catch (err: any) {
      console.error('Error fetching datasets:', err);
      setFeedback({ type: 'error', message: err.response?.data?.detail || 'Failed to load datasets.' });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDatasets();
  }, [statusFilter, visibilityFilter]);

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!datasetName.trim()) return;
    setIsUploading(true);
    setFeedback(null);
    try {
      const formData = new FormData();
      formData.append('name', datasetName);
      if (datasetDesc) formData.append('description', datasetDesc);
      formData.append('visibility', visibility);
      formData.append('source_type', sourceType);
      if (uploadFile) formData.append('file', uploadFile);

      await api.post('/admin/datasets/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      setFeedback({ type: 'success', message: `Dataset "${datasetName}" uploaded and indexed successfully.` });
      setUploadModalOpen(false);
      setDatasetName('');
      setDatasetDesc('');
      setUploadFile(null);
      fetchDatasets();
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.response?.data?.detail || 'Failed to upload dataset.' });
    } finally {
      setIsUploading(false);
    }
  };

  const handleApprove = async (id: number) => {
    try {
      await api.post(`/admin/datasets/${id}/approve`);
      setFeedback({ type: 'success', message: 'Employee dataset approved and indexed into private vector memory.' });
      fetchDatasets();
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.response?.data?.detail || 'Approval failed.' });
    }
  };

  const handleReject = async (id: number) => {
    try {
      await api.post(`/admin/datasets/${id}/reject`);
      setFeedback({ type: 'success', message: 'Dataset rejected.' });
      fetchDatasets();
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.response?.data?.detail || 'Rejection failed.' });
    }
  };

  const handleReprocess = async (id: number) => {
    try {
      await api.post(`/admin/datasets/${id}/reprocess`);
      setFeedback({ type: 'success', message: 'Dataset reprocessed and re-indexed into private vector store.' });
      fetchDatasets();
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.response?.data?.detail || 'Reprocessing failed.' });
    }
  };

  const handleToggleStatus = async (id: number) => {
    try {
      const res = await api.patch(`/admin/datasets/${id}/toggle-status`);
      setFeedback({ type: 'success', message: res.data.message || 'Status updated.' });
      fetchDatasets();
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.response?.data?.detail || 'Toggle status failed.' });
    }
  };

  const handleDelete = async () => {
    if (!confirmDeleteId) return;
    setIsDeleting(true);
    try {
      await api.delete(`/admin/datasets/${confirmDeleteId}`);
      setFeedback({ type: 'success', message: 'Dataset, vectors, and chunks purged completely.' });
      setConfirmDeleteId(null);
      fetchDatasets();
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.response?.data?.detail || 'Delete failed.' });
    } finally {
      setIsDeleting(false);
    }
  };

  const handleTestSearch = async () => {
    if (!testQuery.trim()) return;
    setIsSearching(true);
    try {
      const payload: any = { query: testQuery };
      if (testDatasetFilter) payload.dataset_id = testDatasetFilter;
      const res = await api.post<TestSearchResult>('/admin/rag/test-search', payload);
      setSearchResult(res.data);
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.response?.data?.detail || 'Test search failed.' });
    } finally {
      setIsSearching(false);
    }
  };

  const handleOpenDebug = async (ds: DatasetItem) => {
    setActiveDataset(ds);
    setViewMode('DEBUG');
    setIsLoadingDetails(true);
    try {
      const res = await api.get<RAGDebugInfo>(`/admin/rag/debug/${ds.id}`);
      setDebugInfo(res.data);
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.response?.data?.detail || 'Failed to load RAG debug info.' });
    } finally {
      setIsLoadingDetails(false);
    }
  };

  const openInspector = async (ds: DatasetItem, mode: 'DOCS' | 'CHUNKS' | 'LOGS' | 'DEBUG') => {
    setActiveDataset(ds);
    setViewMode(mode);
    setIsLoadingDetails(true);
    try {
      if (mode === 'DOCS') {
        const res = await api.get<DocumentItem[]>(`/admin/datasets/${ds.id}/documents`);
        setDocuments(res.data || []);
      } else if (mode === 'CHUNKS') {
        const res = await api.get<ChunkItem[]>(`/admin/datasets/${ds.id}/chunks`);
        setChunks(res.data || []);
      } else if (mode === 'LOGS') {
        const res = await api.get<LogItem[]>(`/admin/datasets/${ds.id}/logs`);
        setLogs(res.data || []);
      } else if (mode === 'DEBUG') {
        const res = await api.get<RAGDebugInfo>(`/admin/rag/debug/${ds.id}`);
        setDebugInfo(res.data);
      }
    } catch (err) {
      console.error('Error loading dataset details:', err);
    } finally {
      setIsLoadingDetails(false);
    }
  };

  const getStatusBadge = (st: string) => {
    const map: Record<string, string> = {
      READY: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40',
      APPROVED: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40',
      PROCESSING: 'bg-blue-500/20 text-blue-300 border-blue-500/40 animate-pulse',
      UPLOADED: 'bg-indigo-500/20 text-indigo-300 border-indigo-500/40',
      PENDING_REVIEW: 'bg-amber-500/20 text-amber-300 border-amber-500/40',
      REJECTED: 'bg-rose-500/20 text-rose-300 border-rose-500/40',
      DISABLED: 'bg-gray-700/40 text-gray-400 border-white/10',
      FAILED: 'bg-red-500/20 text-red-300 border-red-500/40',
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

  const filteredDatasets = datasets.filter((d) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return d.name.toLowerCase().includes(q) || (d.description && d.description.toLowerCase().includes(q));
  });

  const columns: Column<DatasetItem>[] = [
    {
      key: 'name',
      header: 'Dataset & Source Info',
      render: (d) => (
        <div>
          <div className="font-extrabold text-white text-xs flex items-center gap-1.5">
            <span className="material-symbols-outlined text-sm text-purple-400">dataset</span>
            <span>{d.name}</span>
          </div>
          <div className="text-[11px] text-gray-400 mt-0.5 flex items-center gap-2">
            <span>{d.file_name || 'Manual Dataset'}</span>
            <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-white/10 text-gray-300">
              {d.file_type || 'MANUAL'}
            </span>
          </div>
        </div>
      ),
    },
    {
      key: 'status',
      header: 'Ingestion Status',
      render: (d) => getStatusBadge(d.status),
    },
    {
      key: 'visibility',
      header: 'RBAC Scope',
      render: (d) => (
        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-500/10 text-blue-300 border border-blue-500/30">
          {d.visibility.replace('_', ' ')}
        </span>
      ),
    },
    {
      key: 'chunk_count',
      header: 'Index Metrics & Vector Status',
      render: (d) => (
        <div className="text-xs space-y-1">
          <div className="flex items-center gap-1.5">
            <span className="text-emerald-400 font-extrabold">{d.vector_count ?? d.chunk_count} Vectors</span>
            <span className="text-gray-400 text-[10px]">({d.chunk_count} Chunks)</span>
          </div>
          <div className="text-[10px] text-gray-400 flex items-center gap-2">
            <span>{d.document_count} Doc Sections</span>
            <span
              className={`px-1.5 py-0.2 rounded text-[9px] font-bold ${
                d.status === 'READY'
                  ? 'bg-emerald-500/20 text-emerald-300'
                  : d.status === 'FAILED'
                  ? 'bg-red-500/20 text-red-300'
                  : d.status === 'PROCESSING'
                  ? 'bg-blue-500/20 text-blue-300'
                  : 'bg-amber-500/20 text-amber-300'
              }`}
            >
              Index: {d.status}
            </span>
          </div>
        </div>
      ),
    },
    {
      key: 'actions',
      header: 'Actions & Diagnostics',
      align: 'right',
      render: (d) => (
        <div className="flex items-center justify-end gap-1.5">
          {d.status === 'PENDING_REVIEW' && user?.role === 'SUPER_ADMIN' && (
            <>
              <button
                onClick={() => handleApprove(d.id)}
                className="px-2 py-1 rounded-lg bg-emerald-600/80 hover:bg-emerald-600 text-white font-bold text-[10px] flex items-center gap-0.5 shadow"
                title="Approve and index dataset"
              >
                <span className="material-symbols-outlined text-xs">check</span>
                <span>Approve</span>
              </button>
              <button
                onClick={() => handleReject(d.id)}
                className="px-2 py-1 rounded-lg bg-rose-600/80 hover:bg-rose-600 text-white font-bold text-[10px] flex items-center gap-0.5 shadow"
                title="Reject dataset"
              >
                <span className="material-symbols-outlined text-xs">close</span>
                <span>Reject</span>
              </button>
            </>
          )}

          {user?.role === 'SUPER_ADMIN' && (
            <button
              onClick={() => openInspector(d, 'DEBUG')}
              className="p-1.5 rounded-lg bg-purple-500/10 hover:bg-purple-500/20 text-purple-300 border border-purple-500/30"
              title="RAG Diagnostic Inspection"
            >
              <span className="material-symbols-outlined text-sm">troubleshoot</span>
            </button>
          )}

          <button
            onClick={() => openInspector(d, 'CHUNKS')}
            className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-purple-400 border border-white/10"
            title="Inspect Chunks & Embeddings"
          >
            <span className="material-symbols-outlined text-sm">hub</span>
          </button>

          <button
            onClick={() => openInspector(d, 'LOGS')}
            className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-blue-400 border border-white/10"
            title="View Ingestion Logs"
          >
            <span className="material-symbols-outlined text-sm">terminal</span>
          </button>

          <button
            onClick={() => handleReprocess(d.id)}
            className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-gray-300 hover:text-white border border-white/10"
            title="Reprocess Dataset"
          >
            <span className="material-symbols-outlined text-sm">refresh</span>
          </button>

          <button
            onClick={() => handleToggleStatus(d.id)}
            className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-amber-400 border border-white/10"
            title={d.status === 'DISABLED' ? 'Enable Retrieval' : 'Disable Retrieval'}
          >
            <span className="material-symbols-outlined text-sm">
              {d.status === 'DISABLED' ? 'visibility' : 'visibility_off'}
            </span>
          </button>

          {user?.role === 'SUPER_ADMIN' && (
            <button
              onClick={() => setConfirmDeleteId(d.id)}
              className="p-1.5 rounded-lg bg-white/5 hover:bg-red-500/20 text-gray-400 hover:text-red-400 border border-white/10"
              title="Purge Dataset & Vectors"
            >
              <span className="material-symbols-outlined text-sm">delete</span>
            </button>
          )}
        </div>
      ),
    },
  ];

  const totalChunks = datasets.reduce((acc, d) => acc + (d.chunk_count || 0), 0);
  const totalVectors = datasets.reduce((acc, d) => acc + (d.vector_count !== undefined ? d.vector_count : (d.chunk_count || 0)), 0);
  const readyDatasets = datasets.filter((d) => d.status === 'READY' || d.status === 'APPROVED').length;
  const pendingReview = datasets.filter((d) => d.status === 'PENDING_REVIEW').length;

  return (
    <div className="space-y-6">
      <AdminHeader
        title="Private Enterprise Knowledge Base"
        subtitle="Manage authoritative datasets, hospital records, insurance contracts, and government policy files for deterministic, permission-enforced RAG retrieval."
        actions={
          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                setTestSearchOpen(true);
                handleTestSearch();
              }}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold text-purple-300 bg-purple-900/30 hover:bg-purple-900/50 border border-purple-500/40 transition-all shadow-sm"
            >
              <span className="material-symbols-outlined text-sm text-purple-400">saved_search</span>
              <span>Test RAG Search</span>
            </button>
            <button
              onClick={() => setUploadModalOpen(true)}
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-semibold text-white bg-gradient-to-r from-blue-600 to-purple-600 hover:shadow-lg hover:shadow-blue-500/20 transition-all"
            >
              <span className="material-symbols-outlined text-sm">upload_file</span>
              <span>Upload Private Dataset</span>
            </button>
          </div>
        }
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

      {/* KPI Highlights */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard
          title="Indexed Knowledge Vectors"
          value={totalChunks.toLocaleString()}
          subtitle="Semantic chunk embeddings in vector store"
          icon="hub"
          color="purple"
        />
        <StatCard
          title="Active Ready Datasets"
          value={readyDatasets}
          subtitle="Authoritative RAG retrieval sources"
          icon="verified"
          color="emerald"
        />
        <StatCard
          title="Pending Employee Submissions"
          value={pendingReview}
          subtitle="Datasets awaiting administrator approval"
          icon="rate_review"
          color="blue"
        />
      </div>

      <FilterPanel
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        searchPlaceholder="Search datasets by title or description..."
        filters={[
          {
            key: 'status',
            label: 'Status',
            value: statusFilter,
            onChange: setStatusFilter,
            options: [
              { label: 'All Statuses', value: 'ALL' },
              { label: 'Ready (Indexed)', value: 'READY' },
              { label: 'Pending Review', value: 'PENDING_REVIEW' },
              { label: 'Processing', value: 'PROCESSING' },
              { label: 'Disabled', value: 'DISABLED' },
              { label: 'Failed', value: 'FAILED' },
            ],
          },
          {
            key: 'visibility',
            label: 'Visibility Scope',
            value: visibilityFilter,
            onChange: setVisibilityFilter,
            options: [
              { label: 'All Permissions', value: 'ALL' },
              { label: 'User Authorized', value: 'USER_AUTHORIZED' },
              { label: 'Private Hospital', value: 'PRIVATE_HOSPITAL' },
              { label: 'Private Admin', value: 'PRIVATE_ADMIN' },
              { label: 'Super Admin Only', value: 'SUPER_ADMIN_ONLY' },
            ],
          },
        ]}
        onReset={() => {
          setStatusFilter('ALL');
          setVisibilityFilter('ALL');
          setSearchQuery('');
        }}
      />

      <DataTable
        columns={columns}
        data={filteredDatasets}
        isLoading={isLoading}
        emptyMessage="No datasets configured in private knowledge base."
      />

      {/* Dataset Upload Modal */}
      {uploadModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="fixed inset-0 bg-black/80 backdrop-blur-sm" onClick={() => setUploadModalOpen(false)} />
          <div className="relative bg-gray-900 border border-white/15 rounded-2xl max-w-lg w-full p-6 shadow-2xl z-10 space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-3 border-b border-white/10">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-purple-400">upload_file</span>
                <h3 className="text-base font-bold text-white font-['Manrope']">Upload & Ingest Private Dataset</h3>
              </div>
              <button onClick={() => setUploadModalOpen(false)} className="text-gray-400 hover:text-white">
                <span className="material-symbols-outlined text-lg">close</span>
              </button>
            </div>

            <form onSubmit={handleUpload} className="space-y-4 text-xs">
              <div>
                <label className="block text-gray-300 font-semibold mb-1">Dataset Title *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Apollo Hospital Cardiology Protocol & Bed Index 2026"
                  value={datasetName}
                  onChange={(e) => setDatasetName(e.target.value)}
                  className="w-full bg-black/40 border border-white/10 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-gray-300 font-semibold mb-1">Description / Summary</label>
                <textarea
                  rows={2}
                  placeholder="Overview of knowledge contents and intended clinical/insurance scope..."
                  value={datasetDesc}
                  onChange={(e) => setDatasetDesc(e.target.value)}
                  className="w-full bg-black/40 border border-white/10 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-gray-300 font-semibold mb-1">RBAC Visibility</label>
                  <select
                    value={visibility}
                    onChange={(e) => setVisibility(e.target.value)}
                    className="w-full bg-black/60 border border-white/10 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                  >
                    <option value="USER_AUTHORIZED" className="bg-gray-900">User Authorized (Public in Network)</option>
                    <option value="PRIVATE_HOSPITAL" className="bg-gray-900">Private Hospital (Facility Staff Only)</option>
                    <option value="PRIVATE_ADMIN" className="bg-gray-900">Private Admin (All Administrators)</option>
                    <option value="SUPER_ADMIN_ONLY" className="bg-gray-900">Super Admin Only (Confidential)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-gray-300 font-semibold mb-1">Source Category</label>
                  <select
                    value={sourceType}
                    onChange={(e) => setSourceType(e.target.value)}
                    className="w-full bg-black/60 border border-white/10 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                  >
                    <option value="ADMIN_UPLOAD" className="bg-gray-900">Admin Upload</option>
                    <option value="EMPLOYEE_UPLOAD" className="bg-gray-900">Employee Upload</option>
                    <option value="HOSPITAL_RECORD" className="bg-gray-900">Hospital Clinical Record</option>
                    <option value="INSURANCE_DOC" className="bg-gray-900">Insurance Underwriting</option>
                    <option value="SCHEME_DOC" className="bg-gray-900">Government Scheme</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-gray-300 font-semibold mb-1">Document File (PDF, DOCX, CSV, XLSX, TXT)</label>
                <input
                  type="file"
                  accept=".pdf,.docx,.doc,.csv,.xlsx,.xls,.txt"
                  onChange={(e) => setUploadFile(e.target.files ? e.target.files[0] : null)}
                  className="w-full bg-black/40 border border-white/10 rounded-xl p-2 text-white text-xs file:mr-2 file:py-1 file:px-2 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-blue-600 file:text-white hover:file:bg-blue-700"
                />
              </div>

              <div className="pt-3 border-t border-white/10 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setUploadModalOpen(false)}
                  className="px-3 py-1.5 rounded-xl border border-white/10 text-gray-300 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isUploading}
                  className="px-4 py-1.5 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 text-white font-bold flex items-center gap-1 shadow"
                >
                  {isUploading && <span className="material-symbols-outlined text-sm animate-spin">progress_activity</span>}
                  <span>Ingest & Index Vector Data</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Inspector Modal (Docs, Chunks, Logs, Debug) */}
      {viewMode !== 'NONE' && activeDataset && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="fixed inset-0 bg-black/80 backdrop-blur-sm" onClick={() => setViewMode('NONE')} />
          <div className="relative bg-gray-900 border border-white/15 rounded-2xl max-w-2xl w-full p-6 shadow-2xl z-10 space-y-4 max-h-[85vh] flex flex-col">
            <div className="flex items-center justify-between pb-3 border-b border-white/10 flex-shrink-0">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-purple-400">
                  {viewMode === 'CHUNKS'
                    ? 'hub'
                    : viewMode === 'DOCS'
                    ? 'folder_open'
                    : viewMode === 'DEBUG'
                    ? 'troubleshoot'
                    : 'terminal'}
                </span>
                <h3 className="text-base font-bold text-white font-['Manrope']">
                  {viewMode === 'CHUNKS'
                    ? `Vector Chunks: ${activeDataset.name}`
                    : viewMode === 'DOCS'
                    ? `Extracted Documents: ${activeDataset.name}`
                    : viewMode === 'DEBUG'
                    ? `RAG Diagnostic Report: ${activeDataset.name}`
                    : `Processing Logs: ${activeDataset.name}`}
                </h3>
              </div>
              <button onClick={() => setViewMode('NONE')} className="text-gray-400 hover:text-white">
                <span className="material-symbols-outlined text-lg">close</span>
              </button>
            </div>

            <div className="flex-1 overflow-y-auto space-y-3 text-xs pr-1">
              {isLoadingDetails ? (
                <div className="text-center py-12">
                  <span className="material-symbols-outlined text-3xl text-purple-400 animate-spin">
                    progress_activity
                  </span>
                  <p className="text-gray-400 mt-2">Loading diagnostics...</p>
                </div>
              ) : viewMode === 'DEBUG' && debugInfo ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                    <div className="bg-black/40 border border-white/10 p-3 rounded-xl">
                      <span className="text-[10px] text-gray-400 uppercase font-semibold">Dataset Status</span>
                      <div className="text-sm font-extrabold text-white mt-0.5">{debugInfo.dataset_status}</div>
                    </div>
                    <div className="bg-black/40 border border-white/10 p-3 rounded-xl">
                      <span className="text-[10px] text-gray-400 uppercase font-semibold">Documents</span>
                      <div className="text-sm font-extrabold text-blue-400 mt-0.5">{debugInfo.document_count}</div>
                    </div>
                    <div className="bg-black/40 border border-white/10 p-3 rounded-xl">
                      <span className="text-[10px] text-gray-400 uppercase font-semibold">Chunk Records</span>
                      <div className="text-sm font-extrabold text-purple-400 mt-0.5">{debugInfo.chunk_count}</div>
                    </div>
                    <div className="bg-black/40 border border-white/10 p-3 rounded-xl">
                      <span className="text-[10px] text-gray-400 uppercase font-semibold">Embeddings</span>
                      <div className="text-sm font-extrabold text-indigo-400 mt-0.5">{debugInfo.embedding_count}</div>
                    </div>
                    <div className="bg-black/40 border border-white/10 p-3 rounded-xl">
                      <span className="text-[10px] text-gray-400 uppercase font-semibold">Vectors in Store</span>
                      <div className="text-sm font-extrabold text-emerald-400 mt-0.5">{debugInfo.vector_count}</div>
                    </div>
                    <div className="bg-black/40 border border-white/10 p-3 rounded-xl">
                      <span className="text-[10px] text-gray-400 uppercase font-semibold">Qdrant Collection</span>
                      <div className="text-xs font-mono font-bold text-gray-300 mt-0.5 truncate">{debugInfo.collection_name}</div>
                    </div>
                  </div>

                  {debugInfo.last_processing_error ? (
                    <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-xl text-red-300 font-mono text-[11px]">
                      <div className="font-bold flex items-center gap-1 text-red-400 mb-1">
                        <span className="material-symbols-outlined text-sm">error</span>
                        <span>Last Ingestion Error</span>
                      </div>
                      <p>{debugInfo.last_processing_error}</p>
                    </div>
                  ) : (
                    <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-emerald-300 font-mono text-[11px] flex items-center gap-1.5">
                      <span className="material-symbols-outlined text-sm text-emerald-400">check_circle</span>
                      <span>Dataset fully verified and indexed into private vector memory with 0 errors.</span>
                    </div>
                  )}

                  <div className="pt-2 flex justify-end">
                    <button
                      onClick={() => {
                        setViewMode('NONE');
                        setTestDatasetFilter(activeDataset.id);
                        setTestSearchOpen(true);
                        handleTestSearch();
                      }}
                      className="px-3 py-1.5 rounded-xl bg-purple-600 hover:bg-purple-700 text-white font-bold text-xs flex items-center gap-1 shadow"
                    >
                      <span className="material-symbols-outlined text-sm">saved_search</span>
                      <span>Run Vector Test Search on this Dataset</span>
                    </button>
                  </div>
                </div>
              ) : viewMode === 'CHUNKS' ? (
                chunks.length === 0 ? (
                  <p className="text-gray-500 text-center py-8">No indexed chunks found for this dataset.</p>
                ) : (
                  chunks.map((c) => (
                    <div key={c.id} className="bg-black/40 border border-white/10 rounded-xl p-3 space-y-1.5">
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-purple-400 font-bold">Chunk #{c.chunk_index}</span>
                        <span className="font-mono text-[10px] text-gray-500 truncate max-w-[200px]">
                          {c.embedding_reference || 'Vector Indexed'}
                        </span>
                      </div>
                      <p className="text-gray-300 leading-relaxed font-mono text-[11px] bg-black/60 p-2.5 rounded-lg">
                        {c.content}
                      </p>
                    </div>
                  ))
                )
              ) : viewMode === 'DOCS' ? (
                documents.length === 0 ? (
                  <p className="text-gray-500 text-center py-8">No extracted documents found.</p>
                ) : (
                  documents.map((d) => (
                    <div key={d.id} className="bg-black/40 border border-white/10 rounded-xl p-3 space-y-1.5">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-white text-xs">{d.title}</span>
                        <span className="text-[10px] text-blue-400 font-semibold">{d.visibility}</span>
                      </div>
                      <p className="text-gray-300 leading-relaxed font-mono text-[11px] bg-black/60 p-2.5 rounded-lg whitespace-pre-line">
                        {d.content}
                      </p>
                    </div>
                  ))
                )
              ) : viewMode === 'LOGS' ? (
                logs.length === 0 ? (
                  <p className="text-gray-500 text-center py-8">No logs recorded.</p>
                ) : (
                  logs.map((l) => (
                    <div key={l.id} className="p-2.5 rounded-xl border border-white/5 bg-black/30 flex items-start justify-between gap-3 font-mono text-[11px]">
                      <div>
                        <span className="text-blue-400 font-bold">{l.status}</span>
                        <p className="text-gray-300 mt-0.5">{l.message}</p>
                      </div>
                      <span className="text-gray-500 text-[10px] flex-shrink-0">
                        {l.processed_at ? new Date(l.processed_at).toLocaleTimeString() : ''}
                      </span>
                    </div>
                  ))
                )
              ) : null}
            </div>
          </div>
        </div>
      )}

      {/* Test RAG Search Modal */}
      {testSearchOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="fixed inset-0 bg-black/80 backdrop-blur-sm" onClick={() => setTestSearchOpen(false)} />
          <div className="relative bg-gray-900 border border-purple-500/30 rounded-2xl max-w-2xl w-full p-6 shadow-2xl z-10 space-y-4 max-h-[85vh] flex flex-col">
            <div className="flex items-center justify-between pb-3 border-b border-white/10 flex-shrink-0">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-purple-400">saved_search</span>
                <h3 className="text-base font-bold text-white font-['Manrope']">Interactive RAG Vector Test Search</h3>
              </div>
              <button onClick={() => setTestSearchOpen(false)} className="text-gray-400 hover:text-white">
                <span className="material-symbols-outlined text-lg">close</span>
              </button>
            </div>

            <div className="space-y-3">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={testQuery}
                  onChange={(e) => setTestQuery(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleTestSearch()}
                  placeholder="Enter test clinical query (e.g. Find cardiology hospitals in Bengaluru)..."
                  className="flex-1 bg-black/50 border border-white/15 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-purple-500"
                />
                <button
                  onClick={handleTestSearch}
                  disabled={isSearching}
                  className="px-4 py-2 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 text-white font-bold text-xs rounded-xl flex items-center gap-1 shadow"
                >
                  {isSearching ? (
                    <span className="material-symbols-outlined text-sm animate-spin">progress_activity</span>
                  ) : (
                    <span className="material-symbols-outlined text-sm">search</span>
                  )}
                  <span>Search</span>
                </button>
              </div>

              {/* Sample Quick Queries */}
              <div className="flex flex-wrap items-center gap-1.5 text-[11px]">
                <span className="text-gray-400">Sample queries:</span>
                <button
                  type="button"
                  onClick={() => {
                    setTestQuery('Find cardiology hospitals in Bengaluru');
                  }}
                  className="px-2 py-0.5 rounded bg-white/5 hover:bg-white/10 text-purple-300 border border-white/10 font-mono text-[10px]"
                >
                  Cardiology Bengaluru
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setTestQuery('What government schemes cover knee surgery?');
                  }}
                  className="px-2 py-0.5 rounded bg-white/5 hover:bg-white/10 text-blue-300 border border-white/10 font-mono text-[10px]"
                >
                  Knee Surgery Schemes
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setTestQuery('Cashless hospital admission claim policy');
                  }}
                  className="px-2 py-0.5 rounded bg-white/5 hover:bg-white/10 text-emerald-300 border border-white/10 font-mono text-[10px]"
                >
                  Cashless Claims
                </button>
              </div>
            </div>

            {/* Results container */}
            <div className="flex-1 overflow-y-auto space-y-3 text-xs pr-1 border-t border-white/5 pt-3">
              {isSearching ? (
                <div className="text-center py-10">
                  <span className="material-symbols-outlined text-3xl text-purple-400 animate-spin">
                    progress_activity
                  </span>
                  <p className="text-gray-400 mt-2 text-xs">Computing semantic similarity and querying vector store...</p>
                </div>
              ) : searchResult ? (
                <div className="space-y-3">
                  <div className="flex items-center justify-between text-[11px] text-gray-400 bg-black/30 p-2.5 rounded-xl border border-white/5">
                    <span>
                      Matched <span className="text-emerald-400 font-bold">{searchResult.matched_count}</span> candidate chunks (Total vectors: {searchResult.total_vectors_in_store})
                    </span>
                    <span className="flex items-center gap-1 font-mono text-[10px]">
                      Qdrant: {searchResult.qdrant_healthy ? <span className="text-emerald-400 font-bold">ONLINE</span> : <span className="text-blue-400 font-bold">LOCAL VECTOR INDEX</span>}
                    </span>
                  </div>

                  {searchResult.retrieved_chunks.length === 0 ? (
                    <div className="text-center py-8 text-gray-400 space-y-1">
                      <span className="material-symbols-outlined text-3xl text-gray-500">search_off</span>
                      <p className="text-xs font-semibold">No chunks met the similarity threshold.</p>
                      <p className="text-[10px] text-gray-500">Ensure datasets are uploaded, approved, and status is READY.</p>
                    </div>
                  ) : (
                    searchResult.retrieved_chunks.map((chunk, idx) => (
                      <div key={chunk.id || idx} className="bg-black/50 border border-purple-500/20 rounded-xl p-3.5 space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-white text-xs">{chunk.title}</span>
                          <div className="flex items-center gap-2">
                            <span className="px-2 py-0.5 bg-emerald-500/20 text-emerald-300 font-mono font-bold text-[10px] rounded-full border border-emerald-500/30">
                              Score: {chunk.score} ({Math.round(chunk.confidence * 100)}%)
                            </span>
                            <span className="px-1.5 py-0.2 bg-blue-500/20 text-blue-300 text-[9px] font-bold rounded">
                              {chunk.visibility}
                            </span>
                          </div>
                        </div>
                        <p className="text-gray-300 font-mono text-[11px] leading-relaxed bg-black/60 p-2.5 rounded-lg">
                          {chunk.content}
                        </p>
                      </div>
                    ))
                  )}
                </div>
              ) : (
                <div className="text-center py-10 text-gray-500 text-xs">
                  Enter a query above to test similarity vector retrieval.
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Purge Confirmation Modal */}
      {confirmDeleteId && (
        <ConfirmActionModal
          isOpen={true}
          title="Purge Knowledge Dataset"
          description="Are you sure you want to completely purge this dataset? This will permanently delete all extracted documents, chunk records, and dense vector embeddings from memory and disk."
          confirmText="Purge Dataset & Vectors"
          isLoading={isDeleting}
          isDestructive={true}
          onConfirm={handleDelete}
          onClose={() => setConfirmDeleteId(null)}
        />
      )}
    </div>
  );
}


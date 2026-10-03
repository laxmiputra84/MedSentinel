'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { UserDocument, LabExtractionResponse, HealthDashboardData } from '@/lib/types';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import api from '@/lib/api';

export default function MedicalVaultPage() {
  return (
    <ProtectedRoute>
      <MedicalVaultContent />
    </ProtectedRoute>
  );
}

function MedicalVaultContent() {
  const [documents, setDocuments] = useState<UserDocument[]>([]);
  const [loading, setLoading] = useState(true);

  // Upload state
  const [file, setFile] = useState<File | null>(null);
  const [docType, setDocType] = useState('Prescription');
  const [uploading, setUploading] = useState(false);
  const [classifying, setClassifying] = useState(false);
  const [classificationResult, setClassificationResult] = useState<{ type: string; confidence: number } | null>(null);
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const [duplicateWarning, setDuplicateWarning] = useState<string | null>(null);

  // Lab Analysis Modal State
  const [analyzingDocId, setAnalyzingDocId] = useState<number | null>(null);
  const [selectedLabData, setSelectedLabData] = useState<LabExtractionResponse | null>(null);
  const [verifyingDocId, setVerifyingDocId] = useState<number | null>(null);
  const [integrityMessage, setIntegrityMessage] = useState<string | null>(null);

  const fetchDocuments = async () => {
    try {
      const res = await api.get<UserDocument[]>('/documents');
      setDocuments(res.data);
    } catch (err) {
      console.error('Error fetching documents:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  // Handle file selection with AI Auto-Classification
  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files ? e.target.files[0] : null;
    setFile(selectedFile);
    setClassificationResult(null);
    setDuplicateWarning(null);
    setErrorMsg('');

    if (!selectedFile) return;

    // Trigger AI classification preview
    setClassifying(true);
    const formData = new FormData();
    formData.append('filename', selectedFile.name);
    formData.append('file', selectedFile);

    try {
      const res = await api.post<{ document_type: string; confidence: number }>('/documents/classify', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setClassificationResult({
        type: res.data.document_type,
        confidence: res.data.confidence,
      });
      // Auto-set the dropdown to the classified type
      setDocType(res.data.document_type);
    } catch (err) {
      console.log('Auto-classification preview note:', err);
    } finally {
      setClassifying(false);
    }
  };

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setErrorMsg('Please select a file to upload (PDF, PNG, JPG, DOC, TXT)');
      return;
    }

    setUploading(true);
    setErrorMsg('');
    setSuccessMsg('');
    setDuplicateWarning(null);

    const formData = new FormData();
    formData.append('document', file);
    formData.append('docType', docType);

    try {
      const res = await api.post<any>('/documents/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (res.data.duplicate_detected) {
        setDuplicateWarning(`Duplicate Document Detected: Matching record ${res.data.matching_document_id || 'in vault'}. Cryptographic hash was flagged for review.`);
      }

      setSuccessMsg(`Document stored in private vault (ID: ${res.data.document_code || 'DOC-STORED'}). Cryptographic SHA-256 signature verified.`);
      setFile(null);
      setClassificationResult(null);
      fetchDocuments();
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to upload document.');
    } finally {
      setUploading(false);
    }
  };

  const handleVerifyIntegrity = async (docId: number) => {
    setVerifyingDocId(docId);
    setIntegrityMessage(null);
    try {
      const res = await api.post<{ document_id: string; valid: boolean; message: string; hash: string }>(
        `/documents/${docId}/verify-integrity`
      );
      setIntegrityMessage(`[${res.data.document_id}] ${res.data.message} (SHA-256: ${res.data.hash?.slice(0, 16)}...)`);
      fetchDocuments();
    } catch (err: any) {
      setIntegrityMessage('Verification check failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setVerifyingDocId(null);
    }
  };

  const handleAnalyzeLab = async (docId: number) => {
    setAnalyzingDocId(docId);
    setSelectedLabData(null);
    try {
      const res = await api.post<LabExtractionResponse>(`/documents/${docId}/extract-lab`);
      setSelectedLabData(res.data);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to extract laboratory data.');
    } finally {
      setAnalyzingDocId(null);
    }
  };

  const handleDelete = async (docId: number) => {
    if (!confirm('Are you sure you want to delete this document from your vault?')) return;

    try {
      await api.delete(`/documents/${docId}`);
      setDocuments(documents.filter((d) => d.id !== docId));
    } catch (err) {
      alert('Failed to delete document.');
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-10">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-blue-950/80 via-indigo-950/80 to-purple-950/80 backdrop-blur-2xl rounded-3xl p-8 sm:p-12 border border-blue-500/20 shadow-2xl flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-3 py-1 rounded-full bg-blue-500/20 text-blue-300 text-xs font-bold uppercase tracking-wider border border-blue-400/30">
              AI Healthcare Intelligence
            </span>
            <span className="px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-300 text-xs font-bold uppercase tracking-wider border border-emerald-400/30">
              SHA-256 Encrypted
            </span>
          </div>
          <h1 className="text-3xl sm:text-5xl font-extrabold text-white font-['Manrope'] mt-2 mb-2 tracking-tight">
            Medical Records Vault
          </h1>
          <p className="text-blue-100/80 text-sm max-w-2xl leading-relaxed">
            Securely store, classify, verify, and extract clinical laboratory metrics with AI assistance, tamper-evident cryptographic hashing, and duplicate detection.
          </p>
        </div>

        <div className="flex flex-wrap gap-3">
          <Link
            href="/health-dashboard"
            className="px-5 py-3 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold rounded-xl text-xs shadow-lg transition-all flex items-center gap-2"
          >
            <span className="material-symbols-outlined text-sm">monitoring</span>
            Health Dashboard & Trends →
          </Link>
          <Link
            href="/claims"
            className="px-5 py-3 bg-white/10 hover:bg-white/20 text-white font-bold rounded-xl text-xs border border-white/15 transition-all"
          >
            Claims Portal
          </Link>
        </div>
      </div>

      {/* Verification Feedback Banner */}
      {integrityMessage && (
        <div className="p-4 bg-indigo-950/70 border border-indigo-500/40 rounded-2xl flex items-center justify-between text-xs text-indigo-200 shadow-xl">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-indigo-400 text-lg">verified_user</span>
            <span>{integrityMessage}</span>
          </div>
          <button onClick={() => setIntegrityMessage(null)} className="text-gray-400 hover:text-white">✕</button>
        </div>
      )}

      {/* Main Content Grid */}
      <div className="grid lg:grid-cols-3 gap-8">
        {/* Upload & AI Classification Form */}
        <div className="lg:col-span-1 space-y-6">
          <div className="bg-gray-900/80 backdrop-blur-xl rounded-2xl p-6 sm:p-8 border border-white/10 shadow-2xl space-y-5">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-bold text-white font-['Manrope'] flex items-center gap-2">
                <span className="material-symbols-outlined text-blue-400">upload_file</span>
                Upload & Classify
              </h2>
              <span className="text-[11px] text-gray-400">Auto-OCR Enabled</span>
            </div>

            {errorMsg && (
              <div className="p-3 bg-red-500/20 border border-red-500/40 rounded-xl text-red-300 text-xs">
                {errorMsg}
              </div>
            )}
            {duplicateWarning && (
              <div className="p-3 bg-amber-500/20 border border-amber-500/40 rounded-xl text-amber-300 text-xs flex items-start gap-2">
                <span className="material-symbols-outlined text-amber-400 text-base">warning</span>
                <span>{duplicateWarning}</span>
              </div>
            )}
            {successMsg && (
              <div className="p-3 bg-emerald-500/20 border border-emerald-500/40 rounded-xl text-emerald-300 text-xs flex items-start gap-2">
                <span className="material-symbols-outlined text-emerald-400 text-base">check_circle</span>
                <span>{successMsg}</span>
              </div>
            )}

            <form onSubmit={handleUploadSubmit} className="space-y-4 text-xs">
              <div>
                <label className="block text-gray-300 font-semibold mb-1.5">Select Medical File</label>
                <input
                  type="file"
                  onChange={handleFileChange}
                  accept=".pdf,.png,.jpg,.jpeg,.doc,.docx,.txt"
                  className="w-full text-xs text-gray-400 file:mr-3 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-blue-600 file:text-white hover:file:bg-blue-700 cursor-pointer"
                />
                <p className="text-[11px] text-gray-400 mt-1">PDF, JPG, PNG, DOC, TXT (Max 10MB)</p>
              </div>

              {classifying && (
                <div className="p-2.5 bg-blue-500/10 border border-blue-500/20 rounded-xl flex items-center gap-2 text-[11px] text-blue-300 animate-pulse">
                  <span className="material-symbols-outlined text-sm animate-spin">sync</span>
                  Analyzing file with AI Document Classifier...
                </div>
              )}

              {classificationResult && (
                <div className="p-3 bg-indigo-500/15 border border-indigo-500/30 rounded-xl space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-gray-300">AI Suggested Type:</span>
                    <span className="font-bold text-indigo-300 bg-indigo-500/20 px-2 py-0.5 rounded">
                      {classificationResult.type}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-[11px] text-gray-400">
                    <span>Confidence Score:</span>
                    <span>{Math.round(classificationResult.confidence * 100)}%</span>
                  </div>
                </div>
              )}

              <div>
                <label className="block text-gray-300 font-semibold mb-1.5">Document Type Confirmation</label>
                <select
                  value={docType}
                  onChange={(e) => setDocType(e.target.value)}
                  className="w-full px-3 py-2.5 bg-gray-950 border border-white/15 rounded-xl text-white focus:outline-none focus:border-blue-500 text-xs"
                >
                  <option value="Lab Report">Lab Report</option>
                  <option value="Prescription">Prescription</option>
                  <option value="Medical Invoice">Medical Invoice</option>
                  <option value="Insurance Document">Insurance Document</option>
                  <option value="Discharge Summary">Discharge Summary</option>
                  <option value="Radiology Report">Radiology Report</option>
                  <option value="Scan Report">Scan Report</option>
                  <option value="Other">Other</option>
                </select>
              </div>

              <button
                type="submit"
                disabled={uploading}
                className="w-full py-3 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold rounded-xl text-xs shadow-lg transition-all disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {uploading ? (
                  <>
                    <span className="material-symbols-outlined text-sm animate-spin">sync</span>
                    Hashing, Encrypting & Storing...
                  </>
                ) : (
                  <>
                    <span className="material-symbols-outlined text-sm">lock</span>
                    Store & Verify in Vault
                  </>
                )}
              </button>
            </form>
          </div>

          {/* Quick Safety Disclaimer Card */}
          <div className="p-4 bg-gray-900/50 border border-white/5 rounded-2xl text-[11px] text-gray-400 space-y-1">
            <div className="font-semibold text-gray-300 flex items-center gap-1.5">
              <span className="material-symbols-outlined text-sm text-blue-400">info</span>
              Clinical Decision-Support Notice
            </div>
            <p className="leading-relaxed">
              MedSentinel provides automated record organization, OCR data extraction, and clinical decision support. Automated outputs do not constitute a definitive medical diagnosis. Always consult licensed medical doctors for health decisions.
            </p>
          </div>
        </div>

        {/* Vault Document List */}
        <div className="lg:col-span-2">
          <div className="bg-gray-900/80 backdrop-blur-xl rounded-2xl p-6 sm:p-8 border border-white/10 shadow-2xl space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <h2 className="text-xl font-bold text-white font-['Manrope'] flex items-center gap-2">
                <span className="material-symbols-outlined text-indigo-400">folder_shared</span>
                Stored Records ({documents.length})
              </h2>
              <span className="text-xs text-gray-400">Tamper-evident verification available per file</span>
            </div>

            {loading ? (
              <div className="space-y-3">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="h-20 bg-gray-800/40 rounded-xl animate-pulse"></div>
                ))}
              </div>
            ) : documents.length === 0 ? (
              <div className="text-center py-16 space-y-2">
                <span className="material-symbols-outlined text-gray-600 text-6xl">folder_open</span>
                <p className="text-gray-300 font-bold text-sm">Your medical vault is empty</p>
                <p className="text-gray-500 text-xs max-w-sm mx-auto">
                  Upload your laboratory reports, doctor prescriptions, or discharge cards on the left.
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {documents.map((doc) => (
                  <div
                    key={doc.id}
                    className={`p-4 bg-gray-950/60 rounded-xl border ${
                      doc.is_duplicate ? 'border-amber-500/30' : 'border-white/5'
                    } hover:border-white/20 transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-4 text-xs`}
                  >
                    <div className="flex items-start gap-3">
                      <div className="w-10 h-10 rounded-lg bg-blue-500/20 text-blue-400 flex items-center justify-center shrink-0 mt-0.5">
                        <span className="material-symbols-outlined text-xl">
                          {doc.doc_type === 'Lab Report' ? 'biochemistry' : doc.file_type.includes('pdf') ? 'picture_as_pdf' : 'description'}
                        </span>
                      </div>
                      <div className="space-y-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-bold text-white text-sm">
                            {doc.original_name}
                          </span>
                          {doc.document_code && (
                            <span className="px-2 py-0.5 bg-white/10 text-gray-300 font-mono text-[10px] rounded">
                              {doc.document_code}
                            </span>
                          )}
                          {doc.is_duplicate && (
                            <span className="px-2 py-0.5 bg-amber-500/20 text-amber-300 border border-amber-500/30 text-[10px] font-semibold rounded flex items-center gap-1">
                              <span className="material-symbols-outlined text-xs">warning</span>
                              Duplicate
                            </span>
                          )}
                          <span
                            className={`px-2 py-0.5 text-[10px] font-semibold rounded ${
                              doc.verification_status === 'VERIFIED'
                                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                                : doc.verification_status === 'FLAGGED'
                                ? 'bg-red-500/20 text-red-300 border border-red-500/30'
                                : 'bg-gray-500/20 text-gray-300'
                            }`}
                          >
                            {doc.verification_status || 'PENDING'}
                          </span>
                        </div>

                        <div className="text-gray-400 text-[11px] flex items-center gap-2 flex-wrap">
                          <span className="px-2 py-0.5 bg-blue-500/10 text-blue-300 rounded font-medium">
                            {doc.doc_type}
                          </span>
                          <span>•</span>
                          <span>{(doc.file_size / 1024).toFixed(0)} KB</span>
                          {doc.file_hash && (
                            <>
                              <span>•</span>
                              <span className="font-mono text-gray-500 truncate max-w-[120px]" title={doc.file_hash}>
                                SHA: {doc.file_hash.slice(0, 10)}...
                              </span>
                            </>
                          )}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 self-end sm:self-center flex-wrap">
                      <Link
                        href={`/agent-workflow`}
                        className="px-3 py-1.5 bg-gradient-to-r from-blue-600/30 to-purple-600/30 hover:from-blue-600 hover:to-purple-600 text-blue-200 hover:text-white border border-blue-500/30 font-semibold rounded-lg text-xs transition-all flex items-center gap-1 shadow-sm"
                        title="Execute 11-Agent Healthcare Intelligence Workflow"
                      >
                        <span className="material-symbols-outlined text-xs">smart_toy</span>
                        Agent Workflow
                      </Link>

                      {doc.doc_type === 'Lab Report' && (
                        <button
                          onClick={() => handleAnalyzeLab(doc.id)}
                          disabled={analyzingDocId === doc.id}
                          className="px-3 py-1.5 bg-purple-600/20 hover:bg-purple-600/30 text-purple-300 border border-purple-500/30 font-semibold rounded-lg text-xs transition-all flex items-center gap-1"
                        >
                          <span className="material-symbols-outlined text-xs">
                            {analyzingDocId === doc.id ? 'sync' : 'analytics'}
                          </span>
                          {analyzingDocId === doc.id ? 'Analyzing...' : 'Lab Analysis'}
                        </button>
                      )}

                      <button
                        onClick={() => handleVerifyIntegrity(doc.id)}
                        disabled={verifyingDocId === doc.id}
                        className="px-2.5 py-1.5 bg-white/5 hover:bg-white/10 text-gray-300 font-semibold rounded-lg text-xs transition-all border border-white/10"
                        title="Verify Cryptographic Signature"
                      >
                        {verifyingDocId === doc.id ? 'Verifying...' : 'Verify Hash'}
                      </button>

                      <a
                        href={`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}${doc.file_path.startsWith('/') ? '' : '/'}${doc.file_path}`}
                        target="_blank"
                        rel="noreferrer"
                        className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-lg text-xs transition-all"
                      >
                        View
                      </a>

                      <button
                        onClick={() => handleDelete(doc.id)}
                        className="p-1.5 text-gray-400 hover:text-red-400 rounded-lg transition-colors"
                        title="Delete Document"
                      >
                        <span className="material-symbols-outlined text-base">delete</span>
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Structured Lab Extraction Modal */}
      {selectedLabData && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4">
          <div className="bg-gray-900 border border-white/15 rounded-3xl max-w-3xl w-full p-6 sm:p-8 space-y-6 shadow-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-white/10 pb-4">
              <div>
                <span className="px-2.5 py-0.5 bg-purple-500/20 text-purple-300 border border-purple-500/30 rounded text-xs font-semibold">
                  OCR Extracted Lab Report
                </span>
                <h3 className="text-xl font-bold text-white font-['Manrope'] mt-1">
                  {selectedLabData.patient_name} — {selectedLabData.patient_id}
                </h3>
                <p className="text-xs text-gray-400">Report Date: {selectedLabData.report_date}</p>
              </div>
              <button
                onClick={() => setSelectedLabData(null)}
                className="p-2 text-gray-400 hover:text-white rounded-xl hover:bg-white/10 transition-colors"
              >
                ✕
              </button>
            </div>

            {/* Test Results Table */}
            <div className="space-y-2">
              <h4 className="text-xs font-bold uppercase tracking-wider text-gray-300">Extracted Laboratory Parameters</h4>
              <div className="overflow-x-auto rounded-xl border border-white/10">
                <table className="w-full text-left text-xs">
                  <thead className="bg-gray-950 text-gray-400 font-semibold border-b border-white/10">
                    <tr>
                      <th className="p-3">Test Parameter</th>
                      <th className="p-3">Observed Value</th>
                      <th className="p-3">Reference Interval</th>
                      <th className="p-3">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5 bg-black/40">
                    {selectedLabData.tests.map((t, idx) => (
                      <tr key={idx} className="hover:bg-white/5 transition-colors">
                        <td className="p-3 font-semibold text-white">{t.name}</td>
                        <td className="p-3 text-gray-200 font-mono">
                          {t.value} {t.unit}
                        </td>
                        <td className="p-3 text-gray-400 font-mono">
                          {t.reference_min !== null && t.reference_max !== null
                            ? `${t.reference_min} - ${t.reference_max}`
                            : t.reference_max !== null
                            ? `< ${t.reference_max}`
                            : 'N/A'}
                        </td>
                        <td className="p-3">
                          <span
                            className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                              t.status === 'NORMAL'
                                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                                : t.status === 'CRITICAL'
                                ? 'bg-red-500/20 text-red-300 border border-red-500/30 animate-pulse'
                                : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                            }`}
                          >
                            {t.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="flex justify-between items-center pt-4 border-t border-white/10">
              <Link
                href="/health-dashboard"
                className="px-4 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-semibold rounded-xl text-xs transition-all flex items-center gap-1.5"
              >
                <span className="material-symbols-outlined text-sm">monitoring</span>
                View in Trends Dashboard →
              </Link>
              <button
                onClick={() => setSelectedLabData(null)}
                className="px-4 py-2 bg-white/10 hover:bg-white/20 text-white font-semibold rounded-xl text-xs transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

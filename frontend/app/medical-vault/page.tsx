'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { UserDocument } from '@/lib/types';
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
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

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

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setErrorMsg('Please select a file to upload (PDF, PNG, JPG, DOC)');
      return;
    }

    setUploading(true);
    setErrorMsg('');
    setSuccessMsg('');

    const formData = new FormData();
    formData.append('document', file);
    formData.append('docType', docType);

    try {
      await api.post('/documents/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setSuccessMsg('Medical document uploaded securely to your private vault.');
      setFile(null);
      fetchDocuments();
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to upload document.');
    } finally {
      setUploading(false);
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
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-blue-900/60 via-purple-900/60 to-indigo-900/60 backdrop-blur-xl rounded-3xl p-8 sm:p-12 border border-blue-500/20 shadow-2xl mb-12 flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
        <div>
          <span className="text-blue-300 font-bold uppercase tracking-wider text-xs">Patient Digital Locker</span>
          <h1 className="text-3xl sm:text-5xl font-extrabold text-white font-['Manrope'] mt-1 mb-2">
            Medical Records Vault
          </h1>
          <p className="text-blue-100 text-sm max-w-xl">
            Securely store, organize, and access medical prescriptions, lab test reports, hospital discharge summaries, and insurance bills.
          </p>
        </div>

        <Link
          href="/profile"
          className="px-5 py-3 bg-white/10 hover:bg-white/20 text-white font-bold rounded-xl text-xs border border-white/15 transition-all whitespace-nowrap"
        >
          View Full Health Profile →
        </Link>
      </div>

      <div className="grid lg:grid-cols-3 gap-8">
        {/* Upload Box */}
        <div className="lg:col-span-1">
          <div className="bg-gray-800/80 backdrop-blur-xl rounded-2xl p-6 sm:p-8 border border-white/10 shadow-2xl space-y-6">
            <h2 className="text-lg font-bold text-white font-['Manrope'] flex items-center gap-2">
              <span className="material-symbols-outlined text-blue-400">upload_file</span>
              Upload Record
            </h2>

            {errorMsg && (
              <div className="p-3 bg-red-500/20 border border-red-500/40 rounded-xl text-red-300 text-xs">
                {errorMsg}
              </div>
            )}
            {successMsg && (
              <div className="p-3 bg-emerald-500/20 border border-emerald-500/40 rounded-xl text-emerald-300 text-xs flex items-center gap-1.5">
                <span className="material-symbols-outlined text-sm">check_circle</span>
                <span>{successMsg}</span>
              </div>
            )}

            <form onSubmit={handleUploadSubmit} className="space-y-4 text-xs">
              <div>
                <label className="block text-gray-300 font-semibold mb-1.5">Document Type</label>
                <select
                  value={docType}
                  onChange={(e) => setDocType(e.target.value)}
                  className="w-full px-3 py-2.5 bg-gray-900 border border-white/15 rounded-xl text-white focus:outline-none focus:border-blue-500"
                >
                  <option value="Prescription">Doctor Prescription</option>
                  <option value="Lab Report">Lab / Blood Test Report</option>
                  <option value="Imaging Scan">MRI / CT Scan / X-Ray</option>
                  <option value="Discharge Summary">Discharge Summary</option>
                  <option value="Hospital Bill">Hospital Bill / Receipt</option>
                  <option value="Other">Other Medical File</option>
                </select>
              </div>

              <div>
                <label className="block text-gray-300 font-semibold mb-1.5">Select File (Max 10MB)</label>
                <input
                  type="file"
                  onChange={(e) => setFile(e.target.files ? e.target.files[0] : null)}
                  accept=".pdf,.png,.jpg,.jpeg,.doc,.docx"
                  className="w-full text-xs text-gray-400 file:mr-3 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-blue-600 file:text-white hover:file:bg-blue-700 cursor-pointer"
                />
              </div>

              <button
                type="submit"
                disabled={uploading}
                className="w-full py-3 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-bold rounded-xl text-xs shadow-lg transition-all disabled:opacity-50"
              >
                {uploading ? 'Encrypting & Storing...' : 'Upload to Private Vault'}
              </button>
            </form>
          </div>
        </div>

        {/* Vault Document List */}
        <div className="lg:col-span-2">
          <div className="bg-gray-800/80 backdrop-blur-xl rounded-2xl p-6 sm:p-8 border border-white/10 shadow-2xl">
            <h2 className="text-xl font-bold text-white font-['Manrope'] mb-6 flex items-center justify-between">
              <span className="flex items-center gap-2">
                <span className="material-symbols-outlined text-purple-400">folder_shared</span>
                Stored Records ({documents.length})
              </span>
            </h2>

            {loading ? (
              <div className="space-y-3">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="h-16 bg-gray-700/40 rounded-xl animate-pulse"></div>
                ))}
              </div>
            ) : documents.length === 0 ? (
              <div className="text-center py-12">
                <span className="material-symbols-outlined text-gray-500 text-5xl mb-2">folder_open</span>
                <p className="text-gray-300 font-bold text-sm">Your medical vault is empty</p>
                <p className="text-gray-500 text-xs mt-1">Upload your medical files on the left to keep them safe and organized.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {documents.map((doc) => (
                  <div
                    key={doc.id}
                    className="p-4 bg-black/30 rounded-xl border border-white/5 flex items-center justify-between gap-4 text-xs hover:border-white/15 transition-all"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-lg bg-blue-500/20 text-blue-400 flex items-center justify-center">
                        <span className="material-symbols-outlined text-xl">
                          {doc.file_type.includes('pdf') ? 'picture_as_pdf' : 'description'}
                        </span>
                      </div>
                      <div>
                        <div className="font-bold text-white text-sm truncate max-w-[240px] sm:max-w-sm">
                          {doc.original_name}
                        </div>
                        <div className="text-gray-400 text-[11px] flex items-center gap-2 mt-0.5">
                          <span className="px-2 py-0.5 bg-white/5 rounded text-blue-300 font-medium">
                            {doc.doc_type}
                          </span>
                          <span>•</span>
                          <span>{(doc.file_size / 1024).toFixed(0)} KB</span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <a
                        href={`http://localhost:8000${doc.file_path}`}
                        target="_blank"
                        rel="noreferrer"
                        className="px-3 py-1.5 bg-white/10 hover:bg-white/20 text-white font-semibold rounded-lg text-xs transition-all"
                      >
                        View / Download
                      </a>
                      <button
                        onClick={() => handleDelete(doc.id)}
                        className="p-1.5 text-gray-400 hover:text-red-400 rounded-lg transition-colors"
                        title="Delete Document"
                      >
                        <span className="material-symbols-outlined text-lg">delete</span>
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

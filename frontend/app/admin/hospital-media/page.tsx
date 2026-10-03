'use client';

import React, { useState, useEffect } from 'react';
import api from '@/lib/api';
import { useAuth } from '@/lib/authContext';
import { AdminHeader } from '@/components/admin/AdminHeader';
import { FilterPanel } from '@/components/admin/FilterPanel';
import { ConfirmActionModal } from '@/components/admin/ConfirmActionModal';

interface HospitalSimple {
  id: number;
  name: string;
  location?: string;
}

interface HospitalMediaItem {
  id: number;
  hospital_id: number;
  file_path: string;
  image_type: string;
  title?: string;
  description?: string;
  ai_generated_caption?: string;
  is_approved_by_admin: boolean;
  is_active: boolean;
  created_at?: string;
}

export default function AdminHospitalMediaPage() {
  const { user } = useAuth();
  const [hospitals, setHospitals] = useState<HospitalSimple[]>([]);
  const [selectedHospitalId, setSelectedHospitalId] = useState<number | null>(null);
  const [mediaList, setMediaList] = useState<HospitalMediaItem[]>([]);
  const [typeFilter, setTypeFilter] = useState('ALL');
  const [isLoading, setIsLoading] = useState(true);

  // Upload Modal State
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [targetHospId, setTargetHospId] = useState<number>(1);
  const [imageType, setImageType] = useState('GALLERY');
  const [mediaTitle, setMediaTitle] = useState('');
  const [mediaDesc, setMediaDesc] = useState('');
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  // Delete modal
  const [confirmDeleteId, setConfirmDeleteId] = useState<number | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  const fetchHospitals = async () => {
    try {
      const res = await api.get('/hospitals');
      const list = res.data || [];
      setHospitals(list);
      if (list.length > 0 && !selectedHospitalId) {
        setSelectedHospitalId(list[0].id);
        setTargetHospId(list[0].id);
      }
    } catch (err) {
      console.error('Error fetching hospitals:', err);
    }
  };

  const fetchMedia = async () => {
    if (!selectedHospitalId) return;
    setIsLoading(true);
    try {
      const params: any = {};
      if (typeFilter !== 'ALL') params.image_type = typeFilter;
      const res = await api.get<HospitalMediaItem[]>(`/admin/hospitals/${selectedHospitalId}/media`, { params });
      setMediaList(res.data || []);
    } catch (err: any) {
      console.error('Error fetching media:', err);
      setFeedback({ type: 'error', message: err.response?.data?.detail || 'Failed to load media assets.' });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchHospitals();
  }, []);

  useEffect(() => {
    fetchMedia();
  }, [selectedHospitalId, typeFilter]);

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile) return;
    setIsUploading(true);
    setFeedback(null);
    try {
      const formData = new FormData();
      formData.append('image_type', imageType);
      if (mediaTitle) formData.append('title', mediaTitle);
      if (mediaDesc) formData.append('description', mediaDesc);
      formData.append('file', uploadFile);

      await api.post(`/admin/hospitals/${targetHospId}/media/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      setFeedback({ type: 'success', message: 'Hospital media asset uploaded and registered in clinical gallery.' });
      setUploadModalOpen(false);
      setMediaTitle('');
      setMediaDesc('');
      setUploadFile(null);
      fetchMedia();
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.response?.data?.detail || 'Upload failed.' });
    } finally {
      setIsUploading(false);
    }
  };

  const handleDelete = async () => {
    if (!confirmDeleteId) return;
    setIsDeleting(true);
    try {
      await api.delete(`/admin/hospitals/media/${confirmDeleteId}`);
      setFeedback({ type: 'success', message: 'Media asset deleted successfully.' });
      setConfirmDeleteId(null);
      fetchMedia();
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.response?.data?.detail || 'Delete failed.' });
    } finally {
      setIsDeleting(false);
    }
  };

  const selectedHospitalName = hospitals.find((h) => h.id === selectedHospitalId)?.name || 'Selected Facility';

  return (
    <div className="space-y-6">
      <AdminHeader
        title="Hospital Media & Facility Assets"
        subtitle="Manage verified facility photography, logos, doctor portraits, and clinical infrastructure assets for RAG AI multimodal grounding."
        actions={
          <button
            onClick={() => setUploadModalOpen(true)}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-semibold text-white bg-gradient-to-r from-blue-600 to-purple-600 hover:shadow-lg hover:shadow-blue-500/20 transition-all"
          >
            <span className="material-symbols-outlined text-sm">add_photo_alternate</span>
            <span>Upload Facility Media</span>
          </button>
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

      {/* Hospital Picker & Filter */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-gray-900/60 border border-white/10 rounded-2xl p-4">
        <div className="flex items-center gap-2">
          <span className="material-symbols-outlined text-blue-400 text-lg">local_hospital</span>
          <span className="text-xs font-bold text-white">Facility:</span>
          <select
            value={selectedHospitalId || ''}
            onChange={(e) => {
              const val = parseInt(e.target.value);
              setSelectedHospitalId(val);
              setTargetHospId(val);
            }}
            className="bg-black/50 border border-white/15 rounded-xl px-3 py-1.5 text-xs text-white focus:outline-none focus:border-blue-500"
          >
            {hospitals.map((h) => (
              <option key={h.id} value={h.id} className="bg-gray-900">
                {h.name} {h.location ? `(${h.location})` : ''}
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-400 font-semibold">Asset Type:</span>
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="bg-black/50 border border-white/15 rounded-xl px-3 py-1.5 text-xs text-white focus:outline-none focus:border-blue-500"
          >
            <option value="ALL" className="bg-gray-900">All Asset Types</option>
            <option value="GALLERY" className="bg-gray-900">Gallery & Infrastructure</option>
            <option value="FACILITY" className="bg-gray-900">Medical Facilities & ICU</option>
            <option value="DOCTOR" className="bg-gray-900">Doctor Portraits</option>
            <option value="LOGO" className="bg-gray-900">Logo</option>
            <option value="COVER" className="bg-gray-900">Cover Banner</option>
          </select>
        </div>
      </div>

      {/* Media Grid */}
      {isLoading ? (
        <div className="text-center py-16">
          <span className="material-symbols-outlined text-3xl text-purple-400 animate-spin">
            progress_activity
          </span>
          <p className="text-xs text-gray-400 mt-2">Loading facility media...</p>
        </div>
      ) : mediaList.length === 0 ? (
        <div className="bg-gray-900/40 border border-white/10 rounded-2xl p-12 text-center space-y-3">
          <div className="w-12 h-12 rounded-full bg-white/5 flex items-center justify-center mx-auto text-gray-500">
            <span className="material-symbols-outlined text-2xl">photo_library</span>
          </div>
          <h4 className="text-sm font-bold text-white">No media assets found for {selectedHospitalName}</h4>
          <p className="text-xs text-gray-400 max-w-md mx-auto">
            Upload facility photos, ICU capacity shots, doctor portraits, or clinical certifications to enrich RAG search groundings.
          </p>
          <button
            onClick={() => setUploadModalOpen(true)}
            className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs shadow inline-flex items-center gap-1.5"
          >
            <span className="material-symbols-outlined text-sm">upload</span>
            <span>Upload Photo</span>
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {mediaList.map((m) => (
            <div
              key={m.id}
              className="group bg-gray-900/70 border border-white/10 rounded-2xl overflow-hidden hover:border-purple-500/40 transition-all flex flex-col justify-between"
            >
              <div className="relative h-40 bg-black/50 overflow-hidden flex items-center justify-center">
                <img
                  src={`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/${m.file_path.replace(/^\//, '')}`}
                  alt={m.title || 'Facility Media'}
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                  onError={(e) => {
                    (e.target as HTMLElement).style.display = 'none';
                  }}
                />
                <span className="absolute top-2 left-2 px-2 py-0.5 rounded-md text-[9px] font-extrabold uppercase bg-black/70 backdrop-blur-sm text-purple-300 border border-white/15">
                  {m.image_type}
                </span>
              </div>

              <div className="p-3 space-y-1.5 flex-1 flex flex-col justify-between">
                <div>
                  <h5 className="font-bold text-white text-xs truncate">{m.title || 'Untitled Asset'}</h5>
                  {m.description && <p className="text-[11px] text-gray-400 line-clamp-2 mt-0.5">{m.description}</p>}
                </div>

                <div className="pt-2 border-t border-white/10 flex items-center justify-between">
                  <span className="text-[10px] text-gray-500">
                    {m.created_at ? new Date(m.created_at).toLocaleDateString() : ''}
                  </span>
                  <button
                    onClick={() => setConfirmDeleteId(m.id)}
                    className="p-1 rounded-lg text-gray-500 hover:text-red-400 hover:bg-white/5"
                    title="Delete Media"
                  >
                    <span className="material-symbols-outlined text-sm">delete</span>
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Upload Modal */}
      {uploadModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="fixed inset-0 bg-black/80 backdrop-blur-sm" onClick={() => setUploadModalOpen(false)} />
          <div className="relative bg-gray-900 border border-white/15 rounded-2xl max-w-md w-full p-6 shadow-2xl z-10 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-white/10">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-purple-400">add_photo_alternate</span>
                <h3 className="text-base font-bold text-white font-['Manrope']">Upload Facility Media</h3>
              </div>
              <button onClick={() => setUploadModalOpen(false)} className="text-gray-400 hover:text-white">
                <span className="material-symbols-outlined text-lg">close</span>
              </button>
            </div>

            <form onSubmit={handleUpload} className="space-y-4 text-xs">
              <div>
                <label className="block text-gray-300 font-semibold mb-1">Target Hospital Facility *</label>
                <select
                  value={targetHospId}
                  onChange={(e) => setTargetHospId(parseInt(e.target.value))}
                  className="w-full bg-black/60 border border-white/15 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                >
                  {hospitals.map((h) => (
                    <option key={h.id} value={h.id} className="bg-gray-900">
                      {h.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-gray-300 font-semibold mb-1">Asset Category</label>
                  <select
                    value={imageType}
                    onChange={(e) => setImageType(e.target.value)}
                    className="w-full bg-black/60 border border-white/15 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                  >
                    <option value="GALLERY" className="bg-gray-900">Gallery Image</option>
                    <option value="FACILITY" className="bg-gray-900">Facility / ICU</option>
                    <option value="DOCTOR" className="bg-gray-900">Doctor Portrait</option>
                    <option value="LOGO" className="bg-gray-900">Hospital Logo</option>
                    <option value="COVER" className="bg-gray-900">Cover Banner</option>
                  </select>
                </div>

                <div>
                  <label className="block text-gray-300 font-semibold mb-1">Title / Caption</label>
                  <input
                    type="text"
                    placeholder="e.g. Advanced Cardiac ICU Unit"
                    value={mediaTitle}
                    onChange={(e) => setMediaTitle(e.target.value)}
                    className="w-full bg-black/40 border border-white/15 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-gray-300 font-semibold mb-1">Description / Infrastructure Notes</label>
                <textarea
                  rows={2}
                  placeholder="e.g. 24/7 cardiac monitoring beds with emergency ECMO equipment."
                  value={mediaDesc}
                  onChange={(e) => setMediaDesc(e.target.value)}
                  className="w-full bg-black/40 border border-white/15 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-gray-300 font-semibold mb-1">Image / Photo File *</label>
                <input
                  type="file"
                  required
                  accept="image/*"
                  onChange={(e) => setUploadFile(e.target.files ? e.target.files[0] : null)}
                  className="w-full bg-black/40 border border-white/10 rounded-xl p-2 text-white text-xs file:mr-2 file:py-1 file:px-2 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-purple-600 file:text-white hover:file:bg-purple-700"
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
                  disabled={isUploading || !uploadFile}
                  className="px-4 py-1.5 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 text-white font-bold flex items-center gap-1 shadow"
                >
                  {isUploading && <span className="material-symbols-outlined text-sm animate-spin">progress_activity</span>}
                  <span>Upload & Index Media</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {confirmDeleteId && (
        <ConfirmActionModal
          isOpen={true}
          title="Delete Hospital Media"
          description="Are you sure you want to delete this media asset? It will be removed from the gallery and private multimodal context."
          confirmText="Delete Media"
          isLoading={isDeleting}
          isDestructive={true}
          onConfirm={handleDelete}
          onClose={() => setConfirmDeleteId(null)}
        />
      )}
    </div>
  );
}

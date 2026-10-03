'use client';

import React, { useState, useEffect } from 'react';
import api from '@/lib/api';
import { useAuth } from '@/lib/authContext';
import { AdminHeader } from '@/components/admin/AdminHeader';
import { FilterPanel } from '@/components/admin/FilterPanel';
import { DataTable, Column } from '@/components/admin/DataTable';

interface HospitalRecord {
  id: number;
  name: string;
  location?: string;
  specialization?: string;
  rating: number;
  cost_range?: string;
  schemes?: string;
  insurance_accepted?: string;
  is_available: boolean;
  facilities?: string;
  phone?: string;
  email?: string;
}

export default function AdminHospitalsPage() {
  const { user } = useAuth();
  const [hospitals, setHospitals] = useState<HospitalRecord[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  // Create / Edit Modal State
  const [modalOpen, setModalOpen] = useState(false);
  const [editingHospital, setEditingHospital] = useState<HospitalRecord | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    location: '',
    specialization: '',
    cost_range: '',
    schemes: '',
    insurance_accepted: '',
    facilities: '',
    phone: '',
    email: '',
    rating: 4.5,
    is_available: true,
  });
  const [isSaving, setIsSaving] = useState(false);
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  const fetchHospitals = async () => {
    setIsLoading(true);
    try {
      const params: any = { page, limit: 10 };
      if (search.trim()) params.search = search.trim();
      const res = await api.get('/admin/hospitals', { params });
      setHospitals(res.data.items || []);
      setTotal(res.data.total || 0);
    } catch (err: any) {
      console.error('Error fetching hospitals:', err);
      setFeedback({ type: 'error', message: err.response?.data?.detail || 'Failed to load hospitals.' });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchHospitals();
  }, [page]);

  useEffect(() => {
    const t = setTimeout(fetchHospitals, 400);
    return () => clearTimeout(t);
  }, [search]);

  const openCreateModal = () => {
    setEditingHospital(null);
    setFormData({
      name: '',
      location: 'Bengaluru, Karnataka',
      specialization: 'Cardiology, Multispeciality, Emergency Care',
      cost_range: '₹50,000 - ₹1,20,000',
      schemes: 'Ayushman Bharat, MJPJAY',
      insurance_accepted: 'Care Health, HDFC ERGO, Star Health',
      facilities: 'ICU, 24/7 Emergency, Cath Lab, Radiology',
      phone: '+91 80 2345 6789',
      email: 'contact@hospital.org',
      rating: 4.8,
      is_available: true,
    });
    setModalOpen(true);
  };

  const openEditModal = (h: HospitalRecord) => {
    setEditingHospital(h);
    setFormData({
      name: h.name || '',
      location: h.location || '',
      specialization: h.specialization || '',
      cost_range: h.cost_range || '',
      schemes: h.schemes || '',
      insurance_accepted: h.insurance_accepted || '',
      facilities: h.facilities || '',
      phone: h.phone || '',
      email: h.email || '',
      rating: h.rating || 4.5,
      is_available: h.is_available ?? true,
    });
    setModalOpen(true);
  };

  const handleSaveHospital = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setFeedback(null);
    try {
      if (editingHospital) {
        await api.put(`/admin/hospitals/${editingHospital.id}`, formData);
        setFeedback({ type: 'success', message: `Hospital "${formData.name}" updated successfully.` });
      } else {
        await api.post('/admin/hospitals', formData);
        setFeedback({ type: 'success', message: `Hospital "${formData.name}" created successfully.` });
      }
      setModalOpen(false);
      fetchHospitals();
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.response?.data?.detail || 'Operation failed.' });
    } finally {
      setIsSaving(false);
    }
  };

  const columns: Column<HospitalRecord>[] = [
    {
      key: 'name',
      header: 'Hospital Facility',
      render: (h) => (
        <div>
          <div className="font-bold text-white text-xs">{h.name}</div>
          <div className="text-[11px] text-gray-400 flex items-center gap-1 mt-0.5">
            <span className="material-symbols-outlined text-[13px] text-blue-400">location_on</span>
            <span>{h.location || 'Location unspecified'}</span>
          </div>
        </div>
      ),
    },
    {
      key: 'specialization',
      header: 'Specializations',
      render: (h) => (
        <span className="text-gray-300 text-xs truncate max-w-[200px] block">
          {h.specialization || 'General Healthcare'}
        </span>
      ),
    },
    {
      key: 'rating',
      header: 'Rating',
      render: (h) => (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-extrabold bg-amber-500/20 text-amber-300 border border-amber-500/30">
          <span className="material-symbols-outlined text-xs">star</span>
          {h.rating?.toFixed(1) || '4.5'}
        </span>
      ),
    },
    {
      key: 'is_available',
      header: 'Beds & Triage',
      render: (h) => (
        <span
          className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold border ${
            h.is_available
              ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
              : 'bg-rose-500/20 text-rose-300 border-rose-500/30'
          }`}
        >
          {h.is_available ? 'Available' : 'Full Capacity'}
        </span>
      ),
    },
    {
      key: 'schemes',
      header: 'Schemes / Coverage',
      render: (h) => (
        <span className="text-gray-400 text-[11px] truncate max-w-[150px] block">
          {h.schemes || 'Standard Insurance'}
        </span>
      ),
    },
    {
      key: 'actions',
      header: 'Actions',
      align: 'right',
      render: (h) => (
        <button
          onClick={() => openEditModal(h)}
          className="px-2.5 py-1 rounded-lg bg-white/5 hover:bg-white/10 text-gray-300 hover:text-white border border-white/10 text-xs font-semibold flex items-center gap-1"
        >
          <span className="material-symbols-outlined text-sm">edit</span>
          <span>Edit</span>
        </button>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <AdminHeader
        title="Hospital Network Management"
        subtitle="Maintain accredited medical institutions, clinical specializations, cashless insurance ties, and real-time bed availability."
        actions={
          user?.role === 'SUPER_ADMIN' && (
            <button
              onClick={openCreateModal}
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-semibold text-white bg-gradient-to-r from-blue-600 to-purple-600 hover:shadow-lg hover:shadow-blue-500/20 transition-all"
            >
              <span className="material-symbols-outlined text-sm">add_circle</span>
              <span>Add New Hospital</span>
            </button>
          )
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

      <FilterPanel
        searchQuery={search}
        onSearchChange={(q) => {
          setSearch(q);
          setPage(1);
        }}
        searchPlaceholder="Search hospitals by name, city, or specialization..."
        onReset={() => {
          setSearch('');
          setPage(1);
        }}
      />

      <DataTable
        columns={columns}
        data={hospitals}
        isLoading={isLoading}
        page={page}
        total={total}
        limit={10}
        onPageChange={(p) => setPage(p)}
        emptyMessage="No hospitals found matching your search."
      />

      {/* Hospital Create / Edit Modal */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="fixed inset-0 bg-black/80 backdrop-blur-sm" onClick={() => setModalOpen(false)} />
          <div className="relative bg-gray-900 border border-white/15 rounded-2xl max-w-2xl w-full p-6 shadow-2xl z-10 space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-3 border-b border-white/10">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-blue-400">local_hospital</span>
                <h3 className="text-base font-bold text-white font-['Manrope']">
                  {editingHospital ? `Edit Hospital: ${editingHospital.name}` : 'Create New Hospital Facility'}
                </h3>
              </div>
              <button onClick={() => setModalOpen(false)} className="text-gray-400 hover:text-white">
                <span className="material-symbols-outlined text-lg">close</span>
              </button>
            </div>

            <form onSubmit={handleSaveHospital} className="space-y-4 text-xs">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-gray-300 font-semibold mb-1">Hospital Name *</label>
                  <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full bg-black/40 border border-white/10 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-gray-300 font-semibold mb-1">Location / Address</label>
                  <input
                    type="text"
                    value={formData.location}
                    onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                    className="w-full bg-black/40 border border-white/10 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-gray-300 font-semibold mb-1">Clinical Specializations (comma separated)</label>
                <input
                  type="text"
                  value={formData.specialization}
                  onChange={(e) => setFormData({ ...formData, specialization: e.target.value })}
                  placeholder="e.g. Cardiology, Neurology, Orthopedics, Oncology"
                  className="w-full bg-black/40 border border-white/10 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-gray-300 font-semibold mb-1">Accepted Government Schemes</label>
                  <input
                    type="text"
                    value={formData.schemes}
                    onChange={(e) => setFormData({ ...formData, schemes: e.target.value })}
                    placeholder="e.g. Ayushman Bharat, MJPJAY"
                    className="w-full bg-black/40 border border-white/10 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-gray-300 font-semibold mb-1">Empanelled Insurances</label>
                  <input
                    type="text"
                    value={formData.insurance_accepted}
                    onChange={(e) => setFormData({ ...formData, insurance_accepted: e.target.value })}
                    placeholder="e.g. Care Health, HDFC ERGO, Star Health"
                    className="w-full bg-black/40 border border-white/10 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div>
                  <label className="block text-gray-300 font-semibold mb-1">Cost Range</label>
                  <input
                    type="text"
                    value={formData.cost_range}
                    onChange={(e) => setFormData({ ...formData, cost_range: e.target.value })}
                    className="w-full bg-black/40 border border-white/10 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-gray-300 font-semibold mb-1">Phone</label>
                  <input
                    type="text"
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    className="w-full bg-black/40 border border-white/10 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-gray-300 font-semibold mb-1">Rating (1 - 5)</label>
                  <input
                    type="number"
                    step="0.1"
                    min="1"
                    max="5"
                    value={formData.rating}
                    onChange={(e) => setFormData({ ...formData, rating: parseFloat(e.target.value) || 4.5 })}
                    className="w-full bg-black/40 border border-white/10 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-gray-300 font-semibold mb-1">Facilities / Infrastructure</label>
                <input
                  type="text"
                  value={formData.facilities}
                  onChange={(e) => setFormData({ ...formData, facilities: e.target.value })}
                  placeholder="e.g. ICU, 24/7 Emergency, Cath Lab, MRI"
                  className="w-full bg-black/40 border border-white/10 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              <div className="pt-3 border-t border-white/10 flex items-center justify-between">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.is_available}
                    onChange={(e) => setFormData({ ...formData, is_available: e.target.checked })}
                    className="rounded bg-black/40 border-white/20 text-blue-600 focus:ring-0"
                  />
                  <span className="text-gray-300 font-semibold">Active Bed / Admission Availability</span>
                </label>

                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setModalOpen(false)}
                    className="px-3 py-1.5 rounded-xl border border-white/10 text-gray-300 hover:text-white"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isSaving}
                    className="px-4 py-1.5 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 text-white font-semibold flex items-center gap-1 shadow"
                  >
                    {isSaving && <span className="material-symbols-outlined text-sm animate-spin">progress_activity</span>}
                    <span>{editingHospital ? 'Update Hospital' : 'Save Hospital'}</span>
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

'use client';

import React, { useState, useEffect } from 'react';
import api from '@/lib/api';
import { useAuth } from '@/lib/authContext';
import { AdminHeader } from '@/components/admin/AdminHeader';
import { DataTable, Column } from '@/components/admin/DataTable';

interface SchemeRecord {
  id: number;
  name: string;
  description?: string;
  coverage?: string;
  eligibility?: string;
  benefits?: string;
  category?: string;
  max_income?: string;
  type?: string;
}

export default function AdminSchemesPage() {
  const { user } = useAuth();
  const [schemes, setSchemes] = useState<SchemeRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingScheme, setEditingScheme] = useState<SchemeRecord | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    coverage: '₹5,00,000 / family / year',
    eligibility: 'BPL Card, Low Income Household (< ₹2.5L/year)',
    benefits: 'Secondary and Tertiary Hospitalization, Cashless Treatment',
    category: 'National Government',
    max_income: '₹2,50,000',
    type: 'government',
  });
  const [isSaving, setIsSaving] = useState(false);
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  const fetchSchemes = async () => {
    setIsLoading(true);
    try {
      const res = await api.get('/admin/schemes');
      setSchemes(res.data || []);
    } catch (err: any) {
      console.error('Error fetching schemes:', err);
      setFeedback({ type: 'error', message: err.response?.data?.detail || 'Failed to load schemes.' });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchSchemes();
  }, []);

  const openCreateModal = () => {
    setEditingScheme(null);
    setFormData({
      name: '',
      description: 'National social healthcare protection scheme for economically vulnerable families.',
      coverage: '₹5,00,000 / family / year',
      eligibility: 'BPL Card, Low Income Household (< ₹2.5L/year)',
      benefits: 'Secondary and Tertiary Hospitalization, Cashless Treatment',
      category: 'National Government',
      max_income: '₹2,50,000',
      type: 'government',
    });
    setModalOpen(true);
  };

  const openEditModal = (s: SchemeRecord) => {
    setEditingScheme(s);
    setFormData({
      name: s.name || '',
      description: s.description || '',
      coverage: s.coverage || '',
      eligibility: s.eligibility || '',
      benefits: s.benefits || '',
      category: s.category || 'National Government',
      max_income: s.max_income || '',
      type: s.type || 'government',
    });
    setModalOpen(true);
  };

  const handleSaveScheme = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setFeedback(null);
    try {
      if (editingScheme) {
        await api.put(`/admin/schemes/${editingScheme.id}`, formData);
        setFeedback({ type: 'success', message: `Scheme "${formData.name}" updated successfully.` });
      } else {
        await api.post('/admin/schemes', formData);
        setFeedback({ type: 'success', message: `Scheme "${formData.name}" added to rule engine.` });
      }
      setModalOpen(false);
      fetchSchemes();
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.response?.data?.detail || 'Failed to save scheme.' });
    } finally {
      setIsSaving(false);
    }
  };

  const columns: Column<SchemeRecord>[] = [
    {
      key: 'name',
      header: 'Scheme Name',
      render: (s) => (
        <div>
          <div className="font-bold text-white text-xs">{s.name}</div>
          <div className="text-[11px] text-blue-400 font-medium">{s.category || 'Government Program'}</div>
        </div>
      ),
    },
    {
      key: 'coverage',
      header: 'Financial Coverage',
      render: (s) => (
        <span className="font-extrabold text-emerald-400 text-xs">
          {s.coverage || 'Subsidized Treatment'}
        </span>
      ),
    },
    {
      key: 'eligibility',
      header: 'Authoritative Criteria',
      render: (s) => (
        <span className="text-gray-300 text-xs truncate max-w-[220px] block">
          {s.eligibility || 'Socioeconomic criteria'}
        </span>
      ),
    },
    {
      key: 'max_income',
      header: 'Income Ceiling',
      render: (s) => (
        <span className="text-gray-400 text-xs">
          {s.max_income || 'No upper cap'}
        </span>
      ),
    },
    {
      key: 'actions',
      header: 'Actions',
      align: 'right',
      render: (s) => (
        <button
          onClick={() => openEditModal(s)}
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
        title="Government Healthcare Schemes"
        subtitle="Manage deterministic rule criteria, income thresholds, family coverage caps, and beneficiary qualification rules."
        actions={
          <button
            onClick={openCreateModal}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-semibold text-white bg-gradient-to-r from-blue-600 to-purple-600 hover:shadow-lg hover:shadow-blue-500/20 transition-all"
          >
            <span className="material-symbols-outlined text-sm">add_circle</span>
            <span>Add Government Scheme</span>
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

      <DataTable
        columns={columns}
        data={schemes}
        isLoading={isLoading}
        emptyMessage="No government schemes currently configured."
      />

      {/* Scheme Create / Edit Modal */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="fixed inset-0 bg-black/80 backdrop-blur-sm" onClick={() => setModalOpen(false)} />
          <div className="relative bg-gray-900 border border-white/15 rounded-2xl max-w-xl w-full p-6 shadow-2xl z-10 space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-3 border-b border-white/10">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-blue-400">policy</span>
                <h3 className="text-base font-bold text-white font-['Manrope']">
                  {editingScheme ? `Edit Scheme: ${editingScheme.name}` : 'Create Government Health Scheme'}
                </h3>
              </div>
              <button onClick={() => setModalOpen(false)} className="text-gray-400 hover:text-white">
                <span className="material-symbols-outlined text-lg">close</span>
              </button>
            </div>

            <form onSubmit={handleSaveScheme} className="space-y-4 text-xs">
              <div>
                <label className="block text-gray-300 font-semibold mb-1">Scheme Name *</label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g. Ayushman Bharat (PM-JAY)"
                  className="w-full bg-black/40 border border-white/10 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-gray-300 font-semibold mb-1">Category / Level</label>
                  <input
                    type="text"
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                    placeholder="e.g. National Government or State Government"
                    className="w-full bg-black/40 border border-white/10 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-gray-300 font-semibold mb-1">Coverage Limit</label>
                  <input
                    type="text"
                    value={formData.coverage}
                    onChange={(e) => setFormData({ ...formData, coverage: e.target.value })}
                    placeholder="e.g. ₹5,00,000 / family / year"
                    className="w-full bg-black/40 border border-white/10 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-gray-300 font-semibold mb-1">Authoritative Eligibility Criteria</label>
                <input
                  type="text"
                  value={formData.eligibility}
                  onChange={(e) => setFormData({ ...formData, eligibility: e.target.value })}
                  placeholder="e.g. BPL Card holder or income < ₹2.5L"
                  className="w-full bg-black/40 border border-white/10 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-gray-300 font-semibold mb-1">Maximum Income Ceiling</label>
                  <input
                    type="text"
                    value={formData.max_income}
                    onChange={(e) => setFormData({ ...formData, max_income: e.target.value })}
                    placeholder="e.g. ₹2,50,000 / year"
                    className="w-full bg-black/40 border border-white/10 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-gray-300 font-semibold mb-1">Key Benefits</label>
                  <input
                    type="text"
                    value={formData.benefits}
                    onChange={(e) => setFormData({ ...formData, benefits: e.target.value })}
                    placeholder="e.g. Cashless Surgery & Diagnostic Coverage"
                    className="w-full bg-black/40 border border-white/10 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-gray-300 font-semibold mb-1">Description / Summary</label>
                <textarea
                  rows={2}
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full bg-black/40 border border-white/10 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              <div className="pt-3 border-t border-white/10 flex items-center justify-end gap-2">
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
                  className="px-4 py-1.5 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 text-white font-bold flex items-center gap-1 shadow"
                >
                  {isSaving && <span className="material-symbols-outlined text-sm animate-spin">progress_activity</span>}
                  <span>{editingScheme ? 'Update Scheme' : 'Save Scheme'}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

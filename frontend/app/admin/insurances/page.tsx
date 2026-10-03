'use client';

import React, { useState, useEffect } from 'react';
import api from '@/lib/api';
import { useAuth } from '@/lib/authContext';
import { AdminHeader } from '@/components/admin/AdminHeader';
import { DataTable, Column } from '@/components/admin/DataTable';

interface InsurancePlan {
  id: number;
  name: string;
  provider: string;
  coverage_amount: number;
  premium_monthly: number;
  premium_annual: number;
  cashless_network: number;
  rating: number;
  coverage_type: string;
  total_claims: number;
}

export default function AdminInsurancesPage() {
  const { user } = useAuth();
  const [plans, setPlans] = useState<InsurancePlan[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingPlan, setEditingPlan] = useState<InsurancePlan | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    provider: '',
    coverage_amount: 1000000,
    premium_monthly: 800,
    premium_annual: 9000,
    cashless_network: 15000,
    claim_settlement_days: 2,
    rating: 4.8,
    coverage_type: 'Comprehensive',
    features: 'Zero Copay, Day Care Procedures Covered, Cashless Hospitalization',
    inclusions: 'Pre & Post Hospitalization, ICU Charges, Ambulance Coverage',
    exclusions: 'Cosmetic Surgery, Non-Prescribed Supplements',
    waiting_period_days: 30,
    eligibility_age_min: 18,
    eligibility_age_max: 65,
  });
  const [isSaving, setIsSaving] = useState(false);
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  const fetchPlans = async () => {
    setIsLoading(true);
    try {
      const res = await api.get('/admin/insurances');
      setPlans(res.data || []);
    } catch (err: any) {
      console.error('Error fetching insurances:', err);
      setFeedback({ type: 'error', message: err.response?.data?.detail || 'Failed to load insurance policies.' });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchPlans();
  }, []);

  const openCreateModal = () => {
    setEditingPlan(null);
    setFormData({
      name: '',
      provider: '',
      coverage_amount: 1000000,
      premium_monthly: 800,
      premium_annual: 9000,
      cashless_network: 15000,
      claim_settlement_days: 2,
      rating: 4.8,
      coverage_type: 'Comprehensive',
      features: 'Zero Copay, Day Care Procedures Covered, Cashless Hospitalization',
      inclusions: 'Pre & Post Hospitalization, ICU Charges, Ambulance Coverage',
      exclusions: 'Cosmetic Surgery, Non-Prescribed Supplements',
      waiting_period_days: 30,
      eligibility_age_min: 18,
      eligibility_age_max: 65,
    });
    setModalOpen(true);
  };

  const openEditModal = (p: InsurancePlan) => {
    setEditingPlan(p);
    setFormData({
      name: p.name || '',
      provider: p.provider || '',
      coverage_amount: p.coverage_amount || 1000000,
      premium_monthly: p.premium_monthly || 800,
      premium_annual: p.premium_annual || 9000,
      cashless_network: p.cashless_network || 15000,
      claim_settlement_days: 2,
      rating: p.rating || 4.8,
      coverage_type: p.coverage_type || 'Comprehensive',
      features: 'Zero Copay, Day Care Procedures Covered',
      inclusions: 'Pre & Post Hospitalization, ICU Charges',
      exclusions: 'Cosmetic Surgery',
      waiting_period_days: 30,
      eligibility_age_min: 18,
      eligibility_age_max: 65,
    });
    setModalOpen(true);
  };

  const handleSavePlan = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setFeedback(null);
    try {
      if (editingPlan) {
        await api.put(`/admin/insurances/${editingPlan.id}`, formData);
        setFeedback({ type: 'success', message: `Insurance plan "${formData.name}" updated successfully.` });
      } else {
        await api.post('/admin/insurances', formData);
        setFeedback({ type: 'success', message: `Insurance plan "${formData.name}" created successfully.` });
      }
      setModalOpen(false);
      fetchPlans();
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.response?.data?.detail || 'Operation failed.' });
    } finally {
      setIsSaving(false);
    }
  };

  const columns: Column<InsurancePlan>[] = [
    {
      key: 'name',
      header: 'Policy Name & Provider',
      render: (p) => (
        <div>
          <div className="font-bold text-white text-xs">{p.name}</div>
          <div className="text-[11px] text-purple-400 font-semibold mt-0.5">{p.provider}</div>
        </div>
      ),
    },
    {
      key: 'coverage_amount',
      header: 'Sum Insured',
      render: (p) => (
        <span className="font-extrabold text-white text-xs">
          ₹{p.coverage_amount ? p.coverage_amount.toLocaleString() : '0'}
        </span>
      ),
    },
    {
      key: 'premium_monthly',
      header: 'Monthly / Annual Premium',
      render: (p) => (
        <div className="text-xs">
          <span className="text-emerald-400 font-bold">₹{p.premium_monthly?.toLocaleString()}</span>
          <span className="text-gray-400 text-[10px] block">/mo (₹{p.premium_annual?.toLocaleString()}/yr)</span>
        </div>
      ),
    },
    {
      key: 'cashless_network',
      header: 'Cashless Network',
      render: (p) => (
        <span className="text-gray-300 text-xs">
          {p.cashless_network ? `${p.cashless_network.toLocaleString()} Hospitals` : '—'}
        </span>
      ),
    },
    {
      key: 'total_claims',
      header: 'Claims Filed',
      render: (p) => (
        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-500/20 text-blue-300 border border-blue-500/30">
          {p.total_claims} Claims
        </span>
      ),
    },
    {
      key: 'actions',
      header: 'Actions',
      align: 'right',
      render: (p) => (
        <button
          onClick={() => openEditModal(p)}
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
        title="Insurance Policy Catalog"
        subtitle="Manage underwriting tiers, premium structures, sum insured caps, cashless network sizes, and claim processing metrics."
        actions={
          user?.role === 'SUPER_ADMIN' && (
            <button
              onClick={openCreateModal}
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-semibold text-white bg-gradient-to-r from-blue-600 to-purple-600 hover:shadow-lg hover:shadow-blue-500/20 transition-all"
            >
              <span className="material-symbols-outlined text-sm">add_circle</span>
              <span>Create New Policy Tier</span>
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

      <DataTable
        columns={columns}
        data={plans}
        isLoading={isLoading}
        emptyMessage="No insurance plans currently configured."
      />

      {/* Insurance Create / Edit Modal */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="fixed inset-0 bg-black/80 backdrop-blur-sm" onClick={() => setModalOpen(false)} />
          <div className="relative bg-gray-900 border border-white/15 rounded-2xl max-w-2xl w-full p-6 shadow-2xl z-10 space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-3 border-b border-white/10">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-purple-400">health_and_safety</span>
                <h3 className="text-base font-bold text-white font-['Manrope']">
                  {editingPlan ? `Edit Policy: ${editingPlan.name}` : 'Create New Health Insurance Policy'}
                </h3>
              </div>
              <button onClick={() => setModalOpen(false)} className="text-gray-400 hover:text-white">
                <span className="material-symbols-outlined text-lg">close</span>
              </button>
            </div>

            <form onSubmit={handleSavePlan} className="space-y-4 text-xs">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-gray-300 font-semibold mb-1">Plan / Policy Name *</label>
                  <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="e.g. Care Supreme Elite"
                    className="w-full bg-black/40 border border-white/10 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-gray-300 font-semibold mb-1">Insurance Carrier / Provider *</label>
                  <input
                    type="text"
                    required
                    value={formData.provider}
                    onChange={(e) => setFormData({ ...formData, provider: e.target.value })}
                    placeholder="e.g. Care Health Insurance"
                    className="w-full bg-black/40 border border-white/10 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div>
                  <label className="block text-gray-300 font-semibold mb-1">Coverage / Sum Insured (₹)</label>
                  <input
                    type="number"
                    required
                    value={formData.coverage_amount}
                    onChange={(e) => setFormData({ ...formData, coverage_amount: parseFloat(e.target.value) || 0 })}
                    className="w-full bg-black/40 border border-white/10 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-gray-300 font-semibold mb-1">Monthly Premium (₹)</label>
                  <input
                    type="number"
                    required
                    value={formData.premium_monthly}
                    onChange={(e) => setFormData({ ...formData, premium_monthly: parseFloat(e.target.value) || 0 })}
                    className="w-full bg-black/40 border border-white/10 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-gray-300 font-semibold mb-1">Annual Premium (₹)</label>
                  <input
                    type="number"
                    required
                    value={formData.premium_annual}
                    onChange={(e) => setFormData({ ...formData, premium_annual: parseFloat(e.target.value) || 0 })}
                    className="w-full bg-black/40 border border-white/10 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div>
                  <label className="block text-gray-300 font-semibold mb-1">Cashless Hospital Count</label>
                  <input
                    type="number"
                    value={formData.cashless_network}
                    onChange={(e) => setFormData({ ...formData, cashless_network: parseInt(e.target.value) || 0 })}
                    className="w-full bg-black/40 border border-white/10 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-gray-300 font-semibold mb-1">Claim Settlement (Days)</label>
                  <input
                    type="number"
                    value={formData.claim_settlement_days}
                    onChange={(e) => setFormData({ ...formData, claim_settlement_days: parseInt(e.target.value) || 2 })}
                    className="w-full bg-black/40 border border-white/10 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-gray-300 font-semibold mb-1">Coverage Type</label>
                  <select
                    value={formData.coverage_type}
                    onChange={(e) => setFormData({ ...formData, coverage_type: e.target.value })}
                    className="w-full bg-black/40 border border-white/10 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                  >
                    <option value="Comprehensive" className="bg-gray-900">Comprehensive</option>
                    <option value="Critical Illness" className="bg-gray-900">Critical Illness</option>
                    <option value="Senior Citizen" className="bg-gray-900">Senior Citizen</option>
                    <option value="Family Floater" className="bg-gray-900">Family Floater</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-gray-300 font-semibold mb-1">Key Features & Inclusions</label>
                <textarea
                  rows={2}
                  value={formData.features}
                  onChange={(e) => setFormData({ ...formData, features: e.target.value })}
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
                  className="px-4 py-1.5 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 text-white font-semibold flex items-center gap-1 shadow"
                >
                  {isSaving && <span className="material-symbols-outlined text-sm animate-spin">progress_activity</span>}
                  <span>{editingPlan ? 'Update Policy' : 'Save Policy'}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

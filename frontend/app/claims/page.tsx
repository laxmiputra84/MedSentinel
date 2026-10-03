'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { Insurance, Hospital, InsuranceClaim } from '@/lib/types';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { useAuth } from '@/lib/authContext';
import api from '@/lib/api';

const STATUS_STEPS = [
  { id: 'SUBMITTED', label: 'Submitted' },
  { id: 'UNDER_REVIEW', label: 'Under Review' },
  { id: 'DOCUMENTS_REQUIRED', label: 'Documents Required' },
  { id: 'APPROVED', label: 'Approved' },
  { id: 'COMPLETED', label: 'Completed' },
];

export default function ClaimsPage() {
  return (
    <ProtectedRoute>
      <ClaimsContent />
    </ProtectedRoute>
  );
}

function ClaimsContent() {
  const { user } = useAuth();
  const isAdmin = user?.role === 'INSURANCE_ADMIN' || user?.role === 'SUPER_ADMIN';

  const [insurances, setInsurances] = useState<Insurance[]>([]);
  const [hospitals, setHospitals] = useState<Hospital[]>([]);
  const [userClaims, setUserClaims] = useState<InsuranceClaim[]>([]);
  const [selectedClaim, setSelectedClaim] = useState<InsuranceClaim | null>(null);
  const [loading, setLoading] = useState(true);

  // Form fields
  const [insuranceId, setInsuranceId] = useState<string>('');
  const [hospitalId, setHospitalId] = useState<string>('');
  const [claimAmount, setClaimAmount] = useState<string>('');
  const [description, setDescription] = useState<string>('');

  const [submitting, setSubmitting] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  // Admin status update modal
  const [adminStatus, setAdminStatus] = useState('APPROVED');
  const [adminComment, setAdminComment] = useState('');
  const [updatingStatus, setUpdatingStatus] = useState(false);

  const fetchData = async () => {
    try {
      const [insRes, hospRes, claimsRes] = await Promise.all([
        api.get<Insurance[]>('/insurances'),
        api.get<Hospital[]>('/hospitals'),
        api.get<InsuranceClaim[]>('/insurance-claims'),
      ]);
      setInsurances(insRes.data);
      setHospitals(hospRes.data);
      setUserClaims(claimsRes.data);
      if (claimsRes.data.length > 0 && !selectedClaim) {
        setSelectedClaim(claimsRes.data[0]);
      }
      if (insRes.data.length > 0) setInsuranceId(String(insRes.data[0].id));
      if (hospRes.data.length > 0) setHospitalId(String(hospRes.data[0].id));
    } catch (err) {
      console.error('Error fetching claims data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleClaimSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!claimAmount || parseFloat(claimAmount) <= 0) {
      setErrorMsg('Please enter a valid claim amount.');
      return;
    }

    setSubmitting(true);
    setErrorMsg('');
    setSuccessMsg('');

    try {
      const res = await api.post('/insurance-claims', {
        insurance_id: insuranceId ? parseInt(insuranceId, 10) : null,
        hospital_id: hospitalId ? parseInt(hospitalId, 10) : null,
        claim_amount: parseFloat(claimAmount),
        claim_description: description,
      });

      setSuccessMsg('Insurance claim submitted successfully! Real-time timeline initialized.');
      setClaimAmount('');
      setDescription('');
      setSelectedClaim(res.data);
      fetchData();
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to submit claim.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleAdminStatusUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedClaim) return;
    setUpdatingStatus(true);
    try {
      const res = await api.patch(`/insurance-claims/${selectedClaim.id}/status`, {
        new_status: adminStatus,
        comment: adminComment,
      });
      setSelectedClaim(res.data);
      setAdminComment('');
      fetchData();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to update claim status.');
    } finally {
      setUpdatingStatus(false);
    }
  };

  const getStepStatus = (stepId: string, currentStatus: string) => {
    const order = ['SUBMITTED', 'UNDER_REVIEW', 'DOCUMENTS_REQUIRED', 'APPROVED', 'COMPLETED'];
    const currentIndex = order.indexOf(currentStatus.toUpperCase());
    const stepIndex = order.indexOf(stepId);

    if (currentStatus === 'REJECTED') {
      if (stepId === 'SUBMITTED') return 'completed';
      if (stepId === 'UNDER_REVIEW') return 'completed';
      return 'rejected';
    }

    if (stepIndex < currentIndex) return 'completed';
    if (stepIndex === currentIndex) return 'current';
    return 'upcoming';
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      {/* Header */}
      <div className="mb-10 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <span className="text-blue-400 font-bold uppercase tracking-wider text-xs">Claims Desk</span>
          <h1 className="text-3xl sm:text-4xl font-black text-white font-['Manrope'] mt-1">
            File & Track Insurance Claims
          </h1>
          <p className="text-gray-400 text-sm">
            Cashless and reimbursement claim processing with real-time status audit timeline.
          </p>
        </div>
        <Link
          href="/profile"
          className="px-4 py-2 bg-white/10 hover:bg-white/20 text-white font-semibold rounded-xl text-xs transition-all border border-white/15"
        >
          ← Back to Profile
        </Link>
      </div>

      <div className="grid lg:grid-cols-12 gap-8">
        {/* Left Col: Claim Filing Form */}
        <div className="lg:col-span-5">
          <div className="bg-gray-800/80 backdrop-blur-xl rounded-2xl p-6 sm:p-8 border border-white/10 shadow-2xl space-y-6">
            <h2 className="text-lg font-bold text-white font-['Manrope'] flex items-center gap-2">
              <span className="material-symbols-outlined text-blue-400">description</span>
              Submit New Claim
            </h2>

            {errorMsg && (
              <div className="p-3.5 bg-red-500/20 border border-red-500/40 rounded-xl text-red-300 text-xs">
                {errorMsg}
              </div>
            )}
            {successMsg && (
              <div className="p-3.5 bg-emerald-500/20 border border-emerald-500/40 rounded-xl text-emerald-300 text-xs flex items-center gap-1.5">
                <span className="material-symbols-outlined text-sm">check_circle</span>
                <span>{successMsg}</span>
              </div>
            )}

            <form onSubmit={handleClaimSubmit} className="space-y-4 text-xs">
              <div>
                <label className="block text-gray-300 font-semibold mb-1">Insurance Policy *</label>
                <select
                  value={insuranceId}
                  onChange={(e) => setInsuranceId(e.target.value)}
                  required
                  className="w-full px-3 py-2.5 bg-gray-900 border border-white/15 rounded-xl text-white text-xs"
                >
                  {insurances.map((ins) => (
                    <option key={ins.id} value={ins.id}>
                      {ins.name} ({ins.provider})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-gray-300 font-semibold mb-1">Hospital Treated *</label>
                <select
                  value={hospitalId}
                  onChange={(e) => setHospitalId(e.target.value)}
                  required
                  className="w-full px-3 py-2.5 bg-gray-900 border border-white/15 rounded-xl text-white text-xs"
                >
                  {hospitals.map((hosp) => (
                    <option key={hosp.id} value={hosp.id}>
                      {hosp.name} ({hosp.location})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-gray-300 font-semibold mb-1">Claim Amount (₹) *</label>
                <input
                  type="number"
                  value={claimAmount}
                  onChange={(e) => setClaimAmount(e.target.value)}
                  placeholder="e.g. 65000"
                  required
                  className="w-full px-3 py-2.5 bg-black/40 border border-white/15 rounded-xl text-white font-bold"
                />
              </div>

              <div>
                <label className="block text-gray-300 font-semibold mb-1">Diagnosis & Treatment Summary</label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Describe illness, date of admission, and procedures..."
                  rows={3}
                  className="w-full px-3 py-2 bg-black/40 border border-white/15 rounded-xl text-white"
                />
              </div>

              <button
                type="submit"
                disabled={submitting}
                className="w-full py-3 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 text-white font-bold rounded-xl text-xs shadow-lg transition-all disabled:opacity-50"
              >
                {submitting ? 'Submitting Claim...' : 'Submit Claim for Review →'}
              </button>
            </form>
          </div>
        </div>

        {/* Right Col: Interactive Timeline & Claim List */}
        <div className="lg:col-span-7 space-y-6">
          {/* Claim Status Timeline Card */}
          {selectedClaim ? (
            <div className="bg-gray-800/80 backdrop-blur-xl rounded-2xl p-6 sm:p-8 border border-white/10 shadow-2xl space-y-6">
              <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-2 pb-4 border-b border-white/10">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-extrabold text-white text-lg font-['Manrope']">
                      Claim #{selectedClaim.id}
                    </span>
                    <span
                      className={`px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase ${
                        selectedClaim.claim_status === 'APPROVED' || selectedClaim.claim_status === 'COMPLETED'
                          ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                          : selectedClaim.claim_status === 'REJECTED'
                          ? 'bg-red-500/20 text-red-300 border border-red-500/30'
                          : 'bg-yellow-500/20 text-yellow-300 border border-yellow-500/30'
                      }`}
                    >
                      {selectedClaim.claim_status}
                    </span>
                  </div>
                  <p className="text-xs text-gray-400 mt-0.5">
                    Amount: <strong className="text-emerald-400 font-bold">₹{selectedClaim.claim_amount?.toLocaleString()}</strong>
                  </p>
                </div>

                {/* Claim Selector if multiple */}
                {userClaims.length > 1 && (
                  <select
                    value={selectedClaim.id}
                    onChange={(e) => {
                      const found = userClaims.find((c) => c.id === parseInt(e.target.value, 10));
                      if (found) setSelectedClaim(found);
                    }}
                    className="px-3 py-1.5 bg-gray-900 border border-white/15 rounded-lg text-white text-xs"
                  >
                    {userClaims.map((c) => (
                      <option key={c.id} value={c.id}>
                        Claim #{c.id} (₹{c.claim_amount?.toLocaleString()})
                      </option>
                    ))}
                  </select>
                )}
              </div>

              {/* Status Timeline */}
              <div>
                <h3 className="text-xs font-bold uppercase tracking-wider text-gray-400 mb-6">
                  Real-Time Claim Timeline
                </h3>

                <div className="relative pl-6 space-y-6 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-white/15">
                  {STATUS_STEPS.map((step) => {
                    const stepState = getStepStatus(step.id, selectedClaim.claim_status);
                    return (
                      <div key={step.id} className="relative flex items-start gap-4 text-xs">
                        {/* Node Icon */}
                        <div
                          className={`absolute -left-6 top-0.5 w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold shadow ${
                            stepState === 'completed'
                              ? 'bg-emerald-500 text-white'
                              : stepState === 'current'
                              ? 'bg-blue-500 text-white ring-4 ring-blue-500/30 animate-pulse'
                              : 'bg-gray-800 text-gray-500 border border-white/20'
                          }`}
                        >
                          {stepState === 'completed' ? '✓' : stepState === 'current' ? '●' : '○'}
                        </div>

                        <div>
                          <span
                            className={`font-bold block ${
                              stepState === 'completed'
                                ? 'text-emerald-300'
                                : stepState === 'current'
                                ? 'text-blue-400 font-extrabold text-sm'
                                : 'text-gray-500'
                            }`}
                          >
                            {step.label}
                          </span>
                          <span className="text-gray-400 text-[11px]">
                            {stepState === 'completed'
                              ? 'Stage verified and archived'
                              : stepState === 'current'
                              ? 'In active verification'
                              : 'Pending prior stage resolution'}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Status History Audit Trail */}
              {selectedClaim.status_history && selectedClaim.status_history.length > 0 && (
                <div className="pt-4 border-t border-white/10 space-y-2">
                  <h4 className="text-xs font-bold text-gray-400">Activity Log</h4>
                  <div className="space-y-1.5">
                    {selectedClaim.status_history.map((hist, idx) => (
                      <div key={idx} className="p-2.5 bg-black/30 rounded-xl text-[11px] flex justify-between items-center">
                        <span className="text-gray-300">{hist.comment || `Moved to ${hist.new_status}`}</span>
                        <span className="text-gray-500 font-mono text-[10px]">
                          {hist.created_at ? new Date(hist.created_at).toLocaleDateString() : 'Recent'}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Admin Status Transition Panel (If user is Admin) */}
              {isAdmin && (
                <form onSubmit={handleAdminStatusUpdate} className="pt-4 border-t border-purple-500/30 space-y-3">
                  <span className="text-purple-300 font-bold text-xs uppercase tracking-wider block">
                    Admin Status Control
                  </span>
                  <div className="grid grid-cols-2 gap-3 text-xs">
                    <select
                      value={adminStatus}
                      onChange={(e) => setAdminStatus(e.target.value)}
                      className="px-3 py-2 bg-gray-900 border border-white/15 rounded-xl text-white"
                    >
                      <option value="UNDER_REVIEW">UNDER_REVIEW</option>
                      <option value="DOCUMENTS_REQUIRED">DOCUMENTS_REQUIRED</option>
                      <option value="APPROVED">APPROVED</option>
                      <option value="REJECTED">REJECTED</option>
                      <option value="COMPLETED">COMPLETED</option>
                    </select>
                    <input
                      type="text"
                      value={adminComment}
                      onChange={(e) => setAdminComment(e.target.value)}
                      placeholder="Audit comment / note..."
                      className="px-3 py-2 bg-black/40 border border-white/15 rounded-xl text-white text-xs"
                    />
                  </div>
                  <button
                    type="submit"
                    disabled={updatingStatus}
                    className="w-full py-2 bg-purple-600 hover:bg-purple-700 text-white font-bold rounded-xl text-xs transition-all shadow"
                  >
                    {updatingStatus ? 'Updating...' : 'Update Status & Notify Patient'}
                  </button>
                </form>
              )}
            </div>
          ) : (
            <div className="bg-gray-800/80 rounded-2xl p-12 text-center border border-white/10">
              <span className="material-symbols-outlined text-gray-500 text-4xl mb-2">receipt_long</span>
              <p className="text-gray-300 font-bold text-sm">No Claims Submitted</p>
              <p className="text-gray-500 text-xs mt-1">Submit your first medical claim using the form on the left.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

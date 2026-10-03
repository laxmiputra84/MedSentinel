'use client';

import React, { useState, useEffect, Suspense } from 'react';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { Insurance } from '@/lib/types';
import { useAuth } from '@/lib/authContext';
import api from '@/lib/api';

export default function InsuranceDetailsPage() {
  return (
    <Suspense
      fallback={
        <div className="max-w-7xl mx-auto px-4 py-16 text-center text-gray-400 text-sm">
          <div className="w-10 h-10 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
          Loading Policy Details...
        </div>
      }
    >
      <InsuranceDetailsContent />
    </Suspense>
  );
}

function InsuranceDetailsContent() {
  const params = useParams();
  const searchParams = useSearchParams();
  const router = useRouter();
  const { isAuthenticated } = useAuth();
  const insuranceId = params?.id;

  const [insurance, setInsurance] = useState<Insurance | null>(null);
  const [loading, setLoading] = useState(true);
  const [enrolling, setEnrolling] = useState(false);
  const [enrollSuccess, setEnrollSuccess] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  // Enrollment modal
  const [showModal, setShowModal] = useState(searchParams.get('enroll') === 'true');
  const [dependents, setDependents] = useState('Self');

  useEffect(() => {
    if (!insuranceId) return;

    const fetchInsurance = async () => {
      try {
        const res = await api.get<Insurance>(`/insurances/${insuranceId}`);
        setInsurance(res.data);
      } catch (err) {
        setErrorMsg('Insurance policy not found.');
      } finally {
        setLoading(false);
      }
    };
    fetchInsurance();
  }, [insuranceId]);

  const handleEnrollSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }

    setEnrolling(true);
    setErrorMsg('');
    try {
      await api.post('/user-insurances', {
        insurance_id: insurance?.id,
        dependents: dependents,
        sum_insured: insurance?.coverage_amount,
      });
      setEnrollSuccess(true);
      setTimeout(() => {
        router.push('/profile');
      }, 1500);
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to enroll in insurance policy.');
    } finally {
      setEnrolling(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-16 text-center">
        <div className="w-12 h-12 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
        <p className="text-gray-400 text-sm">Loading Policy Details...</p>
      </div>
    );
  }

  if (!insurance) {
    return (
      <div className="max-w-xl mx-auto px-4 py-16 text-center">
        <div className="bg-gray-800/80 rounded-2xl p-8 border border-white/10">
          <h2 className="text-xl font-bold text-white mb-2">Policy Not Found</h2>
          <p className="text-gray-400 text-sm mb-6">The requested insurance policy is unavailable.</p>
          <Link href="/insurances" className="px-6 py-2.5 bg-emerald-600 text-white font-bold rounded-xl text-xs">
            ← Back to Insurance Catalog
          </Link>
        </div>
      </div>
    );
  }

  const inclusions = insurance.inclusions ? insurance.inclusions.split(',').map((i) => i.trim()) : [];
  const exclusions = insurance.exclusions ? insurance.exclusions.split(',').map((e) => e.trim()) : [];
  const features = insurance.features ? insurance.features.split(',').map((f) => f.trim()) : [];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Breadcrumb */}
      <div className="mb-6 flex items-center space-x-2 text-xs text-gray-400">
        <Link href="/" className="hover:text-white">Home</Link>
        <span>/</span>
        <Link href="/insurances" className="hover:text-white">Insurance</Link>
        <span>/</span>
        <span className="text-white font-medium">{insurance.name}</span>
      </div>

      {/* Hero Header */}
      <div className="bg-gray-800/80 backdrop-blur-xl rounded-3xl p-8 sm:p-12 border border-white/10 shadow-2xl mb-8 flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
        <div>
          <div className="flex items-center gap-2 mb-3">
            <span className="px-3 py-1 bg-emerald-500/20 text-emerald-300 text-xs font-bold rounded-full uppercase">
              {insurance.coverage_type || 'Comprehensive'}
            </span>
            <span className="text-xs text-gray-400">{insurance.provider}</span>
            <span className="flex items-center gap-1 text-yellow-400 text-xs font-bold ml-2">
              <span className="material-symbols-outlined text-sm">star</span>
              <span>{insurance.rating}</span>
            </span>
          </div>

          <h1 className="text-3xl sm:text-4xl font-extrabold text-white font-['Manrope'] mb-2">
            {insurance.name}
          </h1>
          <p className="text-gray-300 text-sm max-w-xl">
            Cashless coverage at over {insurance.cashless_network.toLocaleString()} partner hospitals across the country.
          </p>
        </div>

        <div className="bg-black/40 p-6 rounded-2xl border border-white/10 text-center min-w-[240px]">
          <div className="text-xs text-gray-400">Monthly Premium</div>
          <div className="text-3xl font-black text-emerald-400 font-['Manrope'] my-1">
            ₹{insurance.premium_monthly.toLocaleString()}/mo
          </div>
          <div className="text-xs text-gray-400 mb-4">₹{insurance.premium_annual.toLocaleString()} billed annually</div>
          <button
            onClick={() => setShowModal(true)}
            className="w-full py-3 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 text-white font-bold rounded-xl text-sm shadow-lg transition-all"
          >
            Enroll in Policy Now
          </button>
        </div>
      </div>

      {/* Details Grid */}
      <div className="grid lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-8">
          {/* Key Benefits */}
          <div className="bg-gray-800/80 backdrop-blur-xl rounded-2xl p-6 sm:p-8 border border-white/10 shadow-xl">
            <h2 className="text-2xl font-bold mb-6 text-white font-['Manrope'] flex items-center gap-2">
              <span className="material-symbols-outlined text-emerald-400">verified</span>
              Policy Coverage Highlights
            </h2>
            <div className="grid sm:grid-cols-2 gap-4">
              {features.map((feature, idx) => (
                <div key={idx} className="flex items-start gap-3 p-4 bg-black/30 rounded-xl border border-white/5">
                  <span className="material-symbols-outlined text-emerald-400 text-xl">check_circle</span>
                  <span className="text-sm text-gray-200">{feature}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Inclusions & Exclusions */}
          <div className="grid sm:grid-cols-2 gap-6">
            <div className="bg-gray-800/80 backdrop-blur-xl rounded-2xl p-6 border border-white/10 shadow-xl">
              <h3 className="text-lg font-bold text-emerald-400 font-['Manrope'] mb-4 flex items-center gap-2">
                <span className="material-symbols-outlined">add_task</span>
                What is Covered
              </h3>
              <ul className="space-y-2 text-sm text-gray-300">
                {inclusions.map((item, idx) => (
                  <li key={idx} className="flex items-center gap-2">
                    <span className="text-emerald-400 font-bold">✓</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="bg-gray-800/80 backdrop-blur-xl rounded-2xl p-6 border border-white/10 shadow-xl">
              <h3 className="text-lg font-bold text-red-400 font-['Manrope'] mb-4 flex items-center gap-2">
                <span className="material-symbols-outlined">block</span>
                Exclusions & Waiting Period
              </h3>
              <ul className="space-y-2 text-sm text-gray-300">
                {exclusions.map((item, idx) => (
                  <li key={idx} className="flex items-center gap-2">
                    <span className="text-red-400 font-bold">✕</span>
                    <span>{item}</span>
                  </li>
                ))}
                <li className="flex items-center gap-2 text-xs text-gray-400 pt-2">
                  <span>Pre-existing waiting period: {insurance.waiting_period_days} Days</span>
                </li>
              </ul>
            </div>
          </div>
        </div>

        {/* Sidebar Summary */}
        <div className="space-y-6">
          <div className="bg-gray-800/80 backdrop-blur-xl rounded-2xl p-6 border border-white/10 shadow-xl space-y-4">
            <h3 className="text-lg font-bold text-white font-['Manrope']">Policy Specifications</h3>

            <div className="space-y-3 text-xs">
              <div className="flex justify-between py-2 border-b border-white/5">
                <span className="text-gray-400">Sum Insured</span>
                <span className="text-white font-bold">₹{insurance.coverage_amount.toLocaleString()}</span>
              </div>
              <div className="flex justify-between py-2 border-b border-white/5">
                <span className="text-gray-400">Eligibility Age</span>
                <span className="text-white font-bold">{insurance.eligibility_age_min} - {insurance.eligibility_age_max} Years</span>
              </div>
              <div className="flex justify-between py-2 border-b border-white/5">
                <span className="text-gray-400">Cashless Network</span>
                <span className="text-white font-bold">{insurance.cashless_network.toLocaleString()}+ Hospitals</span>
              </div>
              <div className="flex justify-between py-2 border-b border-white/5">
                <span className="text-gray-400">Claim Settlement TAT</span>
                <span className="text-white font-bold">{insurance.claim_settlement_days} Days Avg</span>
              </div>
            </div>

            <button
              onClick={() => setShowModal(true)}
              className="w-full py-3 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-xl text-xs transition-all shadow"
            >
              Enroll Now
            </button>
          </div>
        </div>
      </div>

      {/* Enrollment Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-gray-800 rounded-2xl border border-white/20 p-8 max-w-md w-full shadow-2xl space-y-6">
            <div className="flex justify-between items-center pb-3 border-b border-white/10">
              <h3 className="text-xl font-bold text-white font-['Manrope']">Confirm Policy Enrollment</h3>
              <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-white">
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>

            {errorMsg && (
              <div className="p-3 bg-red-500/20 border border-red-500/40 rounded-xl text-red-300 text-xs">
                {errorMsg}
              </div>
            )}
            {enrollSuccess && (
              <div className="p-3 bg-emerald-500/20 border border-emerald-500/40 rounded-xl text-emerald-300 text-xs flex items-center gap-2">
                <span className="material-symbols-outlined text-sm">check_circle</span>
                <span>Enrolled successfully! Redirecting to your dashboard...</span>
              </div>
            )}

            <form onSubmit={handleEnrollSubmit} className="space-y-4 text-xs">
              <div>
                <label className="block text-gray-300 font-semibold mb-1">Selected Plan</label>
                <div className="p-3 bg-black/40 rounded-xl text-white font-bold">{insurance.name}</div>
              </div>

              <div>
                <label className="block text-gray-300 font-semibold mb-1">Covered Beneficiary</label>
                <select
                  value={dependents}
                  onChange={(e) => setDependents(e.target.value)}
                  className="w-full px-3 py-2.5 bg-gray-900 border border-white/15 rounded-xl text-white"
                >
                  <option value="Self">Self Only</option>
                  <option value="Self + Spouse">Self + Spouse</option>
                  <option value="Self + Spouse + Children">Self + Spouse + 2 Children</option>
                  <option value="Parents">Parents Only</option>
                </select>
              </div>

              <div className="p-3 bg-emerald-950/40 border border-emerald-500/30 rounded-xl text-emerald-300">
                Sum Insured: <strong>₹{(insurance.coverage_amount / 100000).toFixed(1)} Lakhs</strong> (Cashless Network)
              </div>

              <button
                type="submit"
                disabled={enrolling || enrollSuccess}
                className="w-full py-3.5 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 text-white font-bold rounded-xl text-sm transition-all shadow disabled:opacity-50"
              >
                {enrolling ? 'Enrolling...' : 'Confirm & Activate Coverage'}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

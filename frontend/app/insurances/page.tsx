'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Insurance } from '@/lib/types';
import { InsuranceCard } from '@/components/InsuranceCard';
import api from '@/lib/api';

export default function InsurancesPage() {
  const router = useRouter();
  const [insurances, setInsurances] = useState<Insurance[]>([]);
  const [search, setSearch] = useState('');
  const [coverageType, setCoverageType] = useState('');
  const [maxPremium, setMaxPremium] = useState('');
  const [provider, setProvider] = useState('');
  const [loading, setLoading] = useState(true);

  // Quick eligibility modal state
  const [age, setAge] = useState<number>(30);
  const [hasPreExisting, setHasPreExisting] = useState(false);
  const [eligibilityResults, setEligibilityResults] = useState<any[] | null>(null);
  const [calculating, setCalculating] = useState(false);

  const fetchInsurances = async () => {
    setLoading(true);
    try {
      const params: Record<string, string> = {};
      if (search.trim()) params.search = search.trim();
      if (coverageType) params.coverage_type = coverageType;
      if (maxPremium) params.maxPremium = maxPremium;
      if (provider) params.provider = provider;

      const res = await api.get<Insurance[]>('/insurances', { params });
      setInsurances(res.data);
    } catch (err) {
      console.error('Error fetching insurances:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      fetchInsurances();
    }, 250);
    return () => clearTimeout(timer);
  }, [search, coverageType, maxPremium, provider]);

  const handleRunEligibility = async (e: React.FormEvent) => {
    e.preventDefault();
    setCalculating(true);
    try {
      const res = await api.post('/insurance-eligibility', {
        age: age,
        pre_existing_conditions: hasPreExisting,
      });
      setEligibilityResults(res.data.eligible);
    } catch (err) {
      console.error('Insurance eligibility error:', err);
    } finally {
      setCalculating(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-emerald-900/60 via-teal-900/60 to-blue-900/60 backdrop-blur-xl rounded-3xl p-8 sm:p-12 border border-emerald-500/20 shadow-2xl mb-12">
        <div className="max-w-3xl">
          <span className="text-emerald-300 font-bold uppercase tracking-wider text-xs">Health Protection</span>
          <h1 className="text-3xl sm:text-5xl font-extrabold text-white font-['Manrope'] mt-1 mb-3">
            Health Insurance Marketplace
          </h1>
          <p className="text-emerald-100 text-sm max-w-2xl mb-6">
            Compare premium rates, cashless hospital networks, critical illness inclusions, and pre-existing waiting periods.
          </p>

          <div className="relative">
            <span className="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-emerald-400 text-xl">
              search
            </span>
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by plan name, insurer, features, or maternity/dental benefits..."
              className="w-full pl-12 pr-4 py-3.5 bg-black/40 border border-white/15 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-emerald-500 text-sm transition-all"
            />
          </div>
        </div>
      </div>

      <div className="grid lg:grid-cols-4 gap-8">
        {/* Sidebar Filters */}
        <aside className="lg:col-span-1 space-y-6">
          <div className="bg-gray-800/80 backdrop-blur-xl rounded-2xl p-6 border border-white/10 shadow-xl space-y-6">
            <h2 className="text-lg font-bold text-white font-['Manrope'] flex items-center gap-1.5 pb-3 border-b border-white/10">
              <span className="material-symbols-outlined text-emerald-400 text-xl">tune</span>
              <span>Filter Plans</span>
            </h2>

            {/* Coverage Type */}
            <div>
              <label className="block text-xs font-semibold text-gray-300 mb-2">Coverage Type</label>
              <select
                value={coverageType}
                onChange={(e) => setCoverageType(e.target.value)}
                className="w-full px-3 py-2.5 bg-gray-900 border border-white/15 rounded-xl text-white text-xs focus:outline-none focus:border-emerald-500"
              >
                <option value="">All Coverage Types</option>
                <option value="Comprehensive">Comprehensive</option>
                <option value="Family Floater">Family Floater</option>
                <option value="Individual">Individual</option>
                <option value="Budget Friendly">Budget Friendly</option>
              </select>
            </div>

            {/* Max Monthly Premium */}
            <div>
              <label className="block text-xs font-semibold text-gray-300 mb-2">Max Monthly Premium</label>
              <select
                value={maxPremium}
                onChange={(e) => setMaxPremium(e.target.value)}
                className="w-full px-3 py-2.5 bg-gray-900 border border-white/15 rounded-xl text-white text-xs focus:outline-none focus:border-emerald-500"
              >
                <option value="">Any Premium</option>
                <option value="1200">Under ₹1,200 / month</option>
                <option value="1800">Under ₹1,800 / month</option>
                <option value="2500">Under ₹2,500 / month</option>
              </select>
            </div>

            {/* Insurer / Provider */}
            <div>
              <label className="block text-xs font-semibold text-gray-300 mb-2">Insurance Provider</label>
              <select
                value={provider}
                onChange={(e) => setProvider(e.target.value)}
                className="w-full px-3 py-2.5 bg-gray-900 border border-white/15 rounded-xl text-white text-xs focus:outline-none focus:border-emerald-500"
              >
                <option value="">All Providers</option>
                <option value="Apollo">Apollo Insurance</option>
                <option value="Max Bupa">Max Bupa</option>
                <option value="HDFC Ergo">HDFC Ergo</option>
                <option value="ICICI Lombard">ICICI Lombard</option>
                <option value="Bajaj Allianz">Bajaj Allianz</option>
                <option value="Star Health">Star Health</option>
              </select>
            </div>
          </div>

          {/* Quick Eligibility Evaluator Widget */}
          <div className="bg-emerald-950/40 backdrop-blur-xl rounded-2xl p-6 border border-emerald-500/30 shadow-xl space-y-4">
            <h3 className="text-sm font-bold text-white font-['Manrope'] flex items-center gap-1.5">
              <span className="material-symbols-outlined text-emerald-400 text-lg">psychology</span>
              <span>Quick Plan Matcher</span>
            </h3>

            <form onSubmit={handleRunEligibility} className="space-y-3">
              <div>
                <label className="block text-xs text-gray-300 mb-1">Your Age</label>
                <input
                  type="number"
                  value={age}
                  onChange={(e) => setAge(parseInt(e.target.value, 10))}
                  min={18}
                  max={80}
                  className="w-full px-3 py-2 bg-black/40 border border-white/15 rounded-lg text-white text-xs"
                />
              </div>

              <label className="flex items-center gap-2 cursor-pointer pt-1">
                <input
                  type="checkbox"
                  checked={hasPreExisting}
                  onChange={(e) => setHasPreExisting(e.target.checked)}
                  className="rounded bg-black/40 border-white/20 text-emerald-500"
                />
                <span className="text-xs text-gray-300">Pre-existing illness</span>
              </label>

              <button
                type="submit"
                disabled={calculating}
                className="w-full py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-xl text-xs transition-all shadow"
              >
                {calculating ? 'Matching...' : 'Match Suitable Plans'}
              </button>
            </form>

            {eligibilityResults && (
              <div className="space-y-2 pt-2 border-t border-emerald-500/20">
                <div className="text-xs text-emerald-300 font-bold">Top Recommended:</div>
                {eligibilityResults.slice(0, 3).map((item) => (
                  <div key={item.id} className="p-2 bg-black/30 rounded-lg text-xs flex justify-between items-center">
                    <span className="text-gray-200 font-medium truncate max-w-[130px]">{item.name}</span>
                    <span className="text-emerald-400 font-bold">{item.eligibility_score}%</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </aside>

        {/* Insurance Plans Listing */}
        <main className="lg:col-span-3">
          <div className="flex justify-between items-center mb-6">
            <span className="text-sm text-gray-400">
              Showing <strong className="text-white">{insurances.length}</strong> insurance plans
            </span>
          </div>

          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="bg-gray-800/40 rounded-2xl h-80 animate-pulse border border-white/5"></div>
              ))}
            </div>
          ) : insurances.length === 0 ? (
            <div className="bg-gray-800/60 rounded-2xl p-12 text-center border border-white/10">
              <span className="material-symbols-outlined text-emerald-400 text-4xl mb-2">shield</span>
              <h3 className="text-xl font-bold text-white mb-2">No Plans Match Criteria</h3>
              <p className="text-gray-400 text-sm mb-6">Try resetting filters to explore all available coverages.</p>
              <button
                onClick={() => {
                  setSearch('');
                  setCoverageType('');
                  setMaxPremium('');
                  setProvider('');
                }}
                className="px-6 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-xl text-xs transition-all"
              >
                Reset Filters
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {insurances.map((ins) => (
                <InsuranceCard
                  key={ins.id}
                  insurance={ins}
                  onEnrollClick={(selected) => {
                    router.push(`/insurance-details/${selected.id}?enroll=true`);
                  }}
                />
              ))}
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { SchemeEligibilityResult } from '@/lib/types';
import api from '@/lib/api';

export default function EligibilityPage() {
  const [familySize, setFamilySize] = useState<string>('3-5');
  const [locationType, setLocationType] = useState<string>('urban');
  const [income, setIncome] = useState<string>('low');
  const [conditions, setConditions] = useState<string[]>([]);
  const [results, setResults] = useState<SchemeEligibilityResult[] | null>(null);
  const [loading, setLoading] = useState(false);

  const toggleCondition = (cond: string) => {
    if (conditions.includes(cond)) {
      setConditions(conditions.filter((c) => c !== cond));
    } else {
      setConditions([...conditions, cond]);
    }
  };

  const handleCheckEligibility = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await api.post('/eligibility-check', {
        familySize: familySize === '1-2' ? 2 : familySize === '3-5' ? 4 : 6,
        location: locationType,
        income: income,
        conditions: conditions,
      });
      setResults(res.data.eligible);
    } catch (err) {
      console.error('Eligibility check error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      {/* Progress & AI Status Banner */}
      <div className="text-center mb-10">
        <div className="inline-flex items-center gap-2 px-4 py-2 bg-blue-500/20 border border-blue-500/30 rounded-full mb-6 backdrop-blur-xl">
          <span className="relative flex h-2.5 w-2.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-blue-500"></span>
          </span>
          <span className="text-xs font-bold text-blue-300 tracking-wider uppercase">
            Government Scheme Eligibility Engine
          </span>
        </div>

        <h1 className="text-4xl sm:text-5xl font-extrabold mb-4 bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent font-['Manrope']">
          Tell us about your household
        </h1>
        <p className="text-gray-300 text-sm sm:text-base max-w-xl mx-auto">
          We cross-check criteria for Ayushman Bharat PM-JAY, ESIC, MJPJAY, and state healthcare funds to calculate your qualification match.
        </p>
      </div>

      <form onSubmit={handleCheckEligibility} className="space-y-6">
        <div className="grid md:grid-cols-2 gap-6">
          {/* Family Size */}
          <div className="bg-gray-800/80 backdrop-blur-xl p-6 sm:p-8 rounded-2xl border border-white/10 shadow-xl">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                <span className="material-symbols-outlined text-white text-xl">groups</span>
              </div>
              <h3 className="text-lg font-bold text-white font-['Manrope']">Family Members</h3>
            </div>
            <div className="grid grid-cols-3 gap-2.5">
              {[
                { label: '1 - 2', sub: 'Small' },
                { label: '3 - 5', sub: 'Medium' },
                { label: '6+', sub: 'Large' },
              ].map((f) => (
                <button
                  type="button"
                  key={f.label}
                  onClick={() => setFamilySize(f.label)}
                  className={`p-3 rounded-xl border text-center transition-all ${
                    familySize === f.label
                      ? 'bg-blue-600/30 border-blue-500 text-white font-bold'
                      : 'bg-black/30 border-white/10 text-gray-400 hover:border-white/20'
                  }`}
                >
                  <span className="text-base font-bold block">{f.label}</span>
                  <span className="text-xs text-gray-400">{f.sub}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Location Type */}
          <div className="bg-gray-800/80 backdrop-blur-xl p-6 sm:p-8 rounded-2xl border border-white/10 shadow-xl">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center">
                <span className="material-symbols-outlined text-white text-xl">location_city</span>
              </div>
              <h3 className="text-lg font-bold text-white font-['Manrope']">Area Type</h3>
            </div>
            <div className="grid grid-cols-2 gap-3">
              {[
                { id: 'urban', label: 'Urban / Metro', icon: 'apartment' },
                { id: 'rural', label: 'Rural / Village', icon: 'cottage' },
              ].map((l) => (
                <button
                  type="button"
                  key={l.id}
                  onClick={() => setLocationType(l.id)}
                  className={`p-3 rounded-xl border text-center transition-all ${
                    locationType === l.id
                      ? 'bg-emerald-600/30 border-emerald-500 text-white font-bold'
                      : 'bg-black/30 border-white/10 text-gray-400 hover:border-white/20'
                  }`}
                >
                  <span className="material-symbols-outlined text-xl block mb-1">{l.icon}</span>
                  <span className="text-xs font-bold block">{l.label}</span>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Income Category */}
        <div className="bg-gray-800/80 backdrop-blur-xl p-6 sm:p-8 rounded-2xl border border-white/10 shadow-xl">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-yellow-500 to-amber-600 flex items-center justify-center">
              <span className="material-symbols-outlined text-white text-xl">account_balance_wallet</span>
            </div>
            <div>
              <h3 className="text-lg font-bold text-white font-['Manrope']">Annual Household Income</h3>
              <p className="text-xs text-gray-400">Determines qualification for government-funded free healthcare</p>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {[
              { id: 'low', label: 'Low Income / BPL', range: '< ₹2.5 Lakh / yr' },
              { id: 'medium', label: 'Middle Income', range: '₹2.5L - ₹8.0L / yr' },
              { id: 'high', label: 'Higher Income', range: '> ₹8.0 Lakh / yr' },
            ].map((inc) => (
              <button
                type="button"
                key={inc.id}
                onClick={() => setIncome(inc.id)}
                className={`p-4 rounded-xl border text-left transition-all ${
                  income === inc.id
                    ? 'bg-amber-500/20 border-amber-500 text-white'
                    : 'bg-black/30 border-white/10 text-gray-400 hover:border-white/20'
                }`}
              >
                <span className="text-sm font-bold text-white block">{inc.label}</span>
                <span className="text-xs text-amber-300 font-medium">{inc.range}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Special Health Condition Tags */}
        <div className="bg-gray-800/80 backdrop-blur-xl p-6 sm:p-8 rounded-2xl border border-white/10 shadow-xl">
          <h3 className="text-base font-bold text-white font-['Manrope'] mb-3">
            Special Beneficiary Categories (Optional)
          </h3>
          <div className="flex flex-wrap gap-2.5">
            {[
              'Senior Citizen (60+)',
              'BPL Ration Card Holder',
              'Critical Illness / Cardiology',
              'Formally Employed (ESIC Eligible)',
              'Maternity / Infant Care',
            ].map((cond) => (
              <button
                type="button"
                key={cond}
                onClick={() => toggleCondition(cond)}
                className={`px-3.5 py-2 rounded-xl text-xs font-semibold border transition-all ${
                  conditions.includes(cond)
                    ? 'bg-purple-600 text-white border-purple-500'
                    : 'bg-black/30 border-white/10 text-gray-300 hover:bg-white/5'
                }`}
              >
                {conditions.includes(cond) ? '✓ ' : '+ '} {cond}
              </button>
            ))}
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full py-4 bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 text-white font-extrabold rounded-2xl hover:shadow-xl hover:shadow-blue-500/30 transition-all text-base transform hover:scale-[1.01] disabled:opacity-50"
        >
          {loading ? 'Evaluating Scheme Match Algorithms...' : 'Calculate Scheme Match Score →'}
        </button>
      </form>

      {/* Results Display */}
      {results && (
        <div className="mt-12 bg-gray-800/90 backdrop-blur-xl p-8 rounded-3xl border border-purple-500/30 shadow-2xl space-y-6">
          <div className="flex items-center gap-3 pb-4 border-b border-white/10">
            <span className="material-symbols-outlined text-emerald-400 text-3xl">verified</span>
            <div>
              <h2 className="text-2xl font-bold text-white font-['Manrope']">
                Your Calculated Scheme Qualifications
              </h2>
              <p className="text-xs text-gray-300">Based on your household demographic profile</p>
            </div>
          </div>

          <div className="space-y-4">
            {results.map((res, idx) => (
              <div
                key={idx}
                className="bg-black/40 p-5 rounded-2xl border border-white/10 flex flex-col sm:flex-row sm:items-center justify-between gap-4"
              >
                <div className="space-y-1">
                  <div className="text-lg font-bold text-white font-['Manrope']">{res.scheme}</div>
                  <div className="text-xs text-gray-400">Cashless coverage & empanelled hospitalization</div>
                </div>

                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <div className="text-xs text-gray-400">Match Probability</div>
                    <div className="text-2xl font-black text-emerald-400">{res.probability}%</div>
                  </div>
                  <Link
                    href={`/hospitals?scheme=${encodeURIComponent(res.scheme)}`}
                    className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white font-bold rounded-xl text-xs transition-all shadow whitespace-nowrap"
                  >
                    View Empanelled Hospitals →
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

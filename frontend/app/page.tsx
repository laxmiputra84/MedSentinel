'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Hospital, Scheme, Insurance } from '@/lib/types';
import { HospitalCard } from '@/components/HospitalCard';
import { SchemeCard } from '@/components/SchemeCard';
import { InsuranceCard } from '@/components/InsuranceCard';
import api from '@/lib/api';

export default function HomePage() {
  const router = useRouter();
  const [searchTerm, setSearchTerm] = useState('');
  const [hospitals, setHospitals] = useState<Hospital[]>([]);
  const [schemes, setSchemes] = useState<Scheme[]>([]);
  const [insurances, setInsurances] = useState<Insurance[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [hospRes, schemeRes, insRes] = await Promise.all([
          api.get<Hospital[]>('/hospitals'),
          api.get<Scheme[]>('/schemes'),
          api.get<Insurance[]>('/insurances'),
        ]);
        setHospitals(hospRes.data.slice(0, 3));
        setSchemes(schemeRes.data.slice(0, 3));
        setInsurances(insRes.data.slice(0, 3));
      } catch (err) {
        console.error('Error loading initial landing data:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchTerm.trim()) {
      router.push(`/hospitals?search=${encodeURIComponent(searchTerm.trim())}`);
    } else {
      router.push('/hospitals');
    }
  };

  const handleQuickSearch = (keyword: string) => {
    router.push(`/hospitals?search=${encodeURIComponent(keyword)}`);
  };

  return (
    <div className="overflow-hidden">
      {/* Hero Section */}
      <section className="relative pt-16 pb-28 px-4 sm:px-6 bg-gradient-to-br from-blue-700 via-purple-700 to-indigo-900 text-white overflow-hidden">
        {/* Decorative Background Elements */}
        <div className="absolute top-0 right-0 w-96 h-96 bg-white/10 rounded-full blur-3xl pointer-events-none"></div>
        <div className="absolute bottom-0 left-0 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl pointer-events-none"></div>

        <div className="max-w-7xl mx-auto grid lg:grid-cols-2 gap-12 items-center relative z-10">
          <div>
            <span className="inline-flex items-center px-4 py-2 rounded-full bg-white/10 text-sm font-semibold mb-6 backdrop-blur-sm border border-white/20">
              <span className="material-symbols-outlined mr-2 text-sm text-emerald-300">verified</span>
              Government Verified Healthcare Intelligence
            </span>

            <h1 className="text-4xl sm:text-6xl font-extrabold mb-6 font-['Manrope'] leading-tight tracking-tight">
              Find Affordable Healthcare Instantly
            </h1>

            <p className="text-lg sm:text-xl text-blue-100 mb-10 leading-relaxed max-w-xl">
              Compare transparent treatment costs across verified hospitals, unlock PM-JAY and state healthcare scheme benefits, and secure top health insurance.
            </p>

            {/* Search Bar */}
            <form onSubmit={handleSearch} className="relative max-w-xl mb-8">
              <div className="flex items-center bg-white rounded-2xl p-2 shadow-2xl hover:shadow-3xl transition-shadow">
                <span className="material-symbols-outlined ml-3 text-blue-600">search</span>
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="Search treatments (e.g. Cardiology, Cataract, Diabetes)"
                  className="w-full bg-transparent border-none focus:outline-none text-gray-900 px-3 py-3 text-base placeholder-gray-500"
                />
                <button
                  type="submit"
                  className="bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white px-6 py-3 rounded-xl font-bold shadow-lg hover:shadow-xl transition-all whitespace-nowrap text-sm"
                >
                  Compare
                </button>
              </div>
            </form>

            {/* Quick Keyword Buttons */}
            <div className="flex flex-wrap gap-2.5">
              <button
                onClick={() => handleQuickSearch('Emergency')}
                className="px-4 py-2 rounded-xl bg-white/10 hover:bg-white/20 font-semibold text-xs flex items-center gap-1.5 border border-white/20 backdrop-blur-sm transition-all hover:scale-105"
              >
                <span className="material-symbols-outlined text-sm">emergency</span> Emergency Care
              </button>
              <button
                onClick={() => handleQuickSearch('Cardiology')}
                className="px-4 py-2 rounded-xl bg-white/10 hover:bg-white/20 font-semibold text-xs flex items-center gap-1.5 border border-white/20 backdrop-blur-sm transition-all hover:scale-105"
              >
                <span className="material-symbols-outlined text-sm">favorite</span> Cardiology
              </button>
              <button
                onClick={() => handleQuickSearch('Surgery')}
                className="px-4 py-2 rounded-xl bg-white/10 hover:bg-white/20 font-semibold text-xs flex items-center gap-1.5 border border-white/20 backdrop-blur-sm transition-all hover:scale-105"
              >
                <span className="material-symbols-outlined text-sm">medical_services</span> Surgery
              </button>
              <button
                onClick={() => handleQuickSearch('Orthopedics')}
                className="px-4 py-2 rounded-xl bg-white/10 hover:bg-white/20 font-semibold text-xs flex items-center gap-1.5 border border-white/20 backdrop-blur-sm transition-all hover:scale-105"
              >
                <span className="material-symbols-outlined text-sm">healing</span> Orthopedics
              </button>
            </div>
          </div>

          {/* Hero Side Infographics */}
          <div className="bg-white/10 backdrop-blur-xl rounded-3xl p-8 border border-white/20 shadow-2xl space-y-6">
            <h3 className="text-xl font-bold text-white font-['Manrope'] flex items-center gap-2">
              <span className="material-symbols-outlined text-blue-300">insights</span>
              Live Healthcare Cost Transparency
            </h3>

            <div className="space-y-4">
              <div className="bg-black/30 rounded-2xl p-4 border border-white/10 flex justify-between items-center">
                <div>
                  <div className="text-sm font-semibold text-white">Angioplasty / Stent</div>
                  <div className="text-xs text-gray-400">Comparing 9 Top Hospitals</div>
                </div>
                <div className="text-right">
                  <div className="text-emerald-400 font-black text-lg">Save up to 42%</div>
                  <div className="text-xs text-gray-300">PMJAY Covered</div>
                </div>
              </div>

              <div className="bg-black/30 rounded-2xl p-4 border border-white/10 flex justify-between items-center">
                <div>
                  <div className="text-sm font-semibold text-white">Knee Replacement</div>
                  <div className="text-xs text-gray-400">Apollo vs Manipal vs Fortis</div>
                </div>
                <div className="text-right">
                  <div className="text-emerald-400 font-black text-lg">₹68,000 avg</div>
                  <div className="text-xs text-gray-300">CGHS Empanelled</div>
                </div>
              </div>

              <div className="bg-black/30 rounded-2xl p-4 border border-white/10 flex justify-between items-center">
                <div>
                  <div className="text-sm font-semibold text-white">Ayushman Bharat Coverage</div>
                  <div className="text-xs text-gray-400">Per eligible family/year</div>
                </div>
                <div className="text-right">
                  <div className="text-purple-300 font-black text-lg">₹5,00,000</div>
                  <div className="text-xs text-gray-300">100% Cashless</div>
                </div>
              </div>
            </div>

            <div className="pt-2 flex justify-between gap-3">
              <Link
                href="/search-flow"
                className="flex-1 py-3 bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 text-white font-bold rounded-xl text-center text-sm shadow-lg transition-all"
              >
                Guided Search Wizard
              </Link>
              <Link
                href="/comparison"
                className="flex-1 py-3 bg-white/10 hover:bg-white/20 text-white font-bold rounded-xl text-center text-sm border border-white/20 transition-all"
              >
                Compare Matrix
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Key Features Grid */}
      <section className="py-20 px-4 sm:px-6 max-w-7xl mx-auto">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <span className="text-blue-400 font-bold uppercase tracking-wider text-xs">Why MedSentinel</span>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-white font-['Manrope'] mt-2 mb-4">
            Democratizing Hospital Pricing & Benefits
          </h2>
          <p className="text-gray-400 text-base">
            Everything you need to make confident, cost-effective healthcare decisions for yourself and your loved ones.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="bg-gray-800/60 rounded-2xl p-8 border border-white/10 shadow-xl card-hover">
            <div className="w-14 h-14 bg-blue-500/20 text-blue-400 rounded-2xl flex items-center justify-center mb-6">
              <span className="material-symbols-outlined text-3xl">account_balance_wallet</span>
            </div>
            <h3 className="text-xl font-bold text-white font-['Manrope'] mb-3">Cost Transparency</h3>
            <p className="text-gray-400 text-sm leading-relaxed mb-4">
              Access real, verified procedure costs and hospital tariffs across major multi-specialty and specialized medical centers.
            </p>
            <Link href="/hospitals" className="text-blue-400 font-semibold text-sm hover:text-blue-300 inline-flex items-center gap-1">
              <span>Browse Hospitals</span>
              <span className="material-symbols-outlined text-sm">arrow_forward</span>
            </Link>
          </div>

          <div className="bg-gray-800/60 rounded-2xl p-8 border border-white/10 shadow-xl card-hover">
            <div className="w-14 h-14 bg-purple-500/20 text-purple-400 rounded-2xl flex items-center justify-center mb-6">
              <span className="material-symbols-outlined text-3xl">verified</span>
            </div>
            <h3 className="text-xl font-bold text-white font-['Manrope'] mb-3">Scheme Eligibility</h3>
            <p className="text-gray-400 text-sm leading-relaxed mb-4">
              Instantly check your qualification for PM-JAY, MJPJAY, ESIC, and CGHS using our algorithmic eligibility evaluator.
            </p>
            <Link href="/eligibility" className="text-purple-400 font-semibold text-sm hover:text-purple-300 inline-flex items-center gap-1">
              <span>Check Eligibility</span>
              <span className="material-symbols-outlined text-sm">arrow_forward</span>
            </Link>
          </div>

          <div className="bg-gray-800/60 rounded-2xl p-8 border border-white/10 shadow-xl card-hover">
            <div className="w-14 h-14 bg-emerald-500/20 text-emerald-400 rounded-2xl flex items-center justify-center mb-6">
              <span className="material-symbols-outlined text-3xl">health_and_safety</span>
            </div>
            <h3 className="text-xl font-bold text-white font-['Manrope'] mb-3">Insurance & Claims</h3>
            <p className="text-gray-400 text-sm leading-relaxed mb-4">
              Compare comprehensive health policies, enroll with ease, track active coverages, and submit cashless insurance claims.
            </p>
            <Link href="/insurances" className="text-emerald-400 font-semibold text-sm hover:text-emerald-300 inline-flex items-center gap-1">
              <span>Explore Plans</span>
              <span className="material-symbols-outlined text-sm">arrow_forward</span>
            </Link>
          </div>
        </div>
      </section>

      {/* Featured Hospitals Section */}
      <section className="py-16 px-4 sm:px-6 bg-black/40 border-y border-white/10">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-end mb-10">
            <div>
              <span className="text-blue-400 font-bold uppercase tracking-wider text-xs">Top Healthcare Providers</span>
              <h2 className="text-3xl font-extrabold text-white font-['Manrope'] mt-1">Featured Hospitals</h2>
            </div>
            <Link
              href="/hospitals"
              className="mt-4 sm:mt-0 text-blue-400 font-semibold hover:text-blue-300 flex items-center gap-1 text-sm"
            >
              <span>View All Hospitals</span>
              <span className="material-symbols-outlined text-sm">arrow_forward</span>
            </Link>
          </div>

          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {[1, 2, 3].map((i) => (
                <div key={i} className="bg-gray-800/40 rounded-2xl h-80 animate-pulse border border-white/5"></div>
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {hospitals.map((hospital) => (
                <HospitalCard key={hospital.id} hospital={hospital} />
              ))}
            </div>
          )}
        </div>
      </section>

      {/* Featured Government Schemes */}
      <section className="py-20 px-4 sm:px-6 max-w-7xl mx-auto">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-end mb-10">
          <div>
            <span className="text-purple-400 font-bold uppercase tracking-wider text-xs">Financial Assistance</span>
            <h2 className="text-3xl font-extrabold text-white font-['Manrope'] mt-1">Government Healthcare Schemes</h2>
          </div>
          <Link
            href="/schemes"
            className="mt-4 sm:mt-0 text-purple-400 font-semibold hover:text-purple-300 flex items-center gap-1 text-sm"
          >
            <span>Explore All Schemes</span>
            <span className="material-symbols-outlined text-sm">arrow_forward</span>
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {schemes.map((scheme) => (
            <SchemeCard key={scheme.id} scheme={scheme} />
          ))}
        </div>
      </section>

      {/* Featured Health Insurance Plans */}
      <section className="py-16 px-4 sm:px-6 bg-black/40 border-t border-white/10">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-end mb-10">
            <div>
              <span className="text-emerald-400 font-bold uppercase tracking-wider text-xs">Protection & Peace of Mind</span>
              <h2 className="text-3xl font-extrabold text-white font-['Manrope'] mt-1">Recommended Insurance Plans</h2>
            </div>
            <Link
              href="/insurances"
              className="mt-4 sm:mt-0 text-emerald-400 font-semibold hover:text-emerald-300 flex items-center gap-1 text-sm"
            >
              <span>Compare All Plans</span>
              <span className="material-symbols-outlined text-sm">arrow_forward</span>
            </Link>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {insurances.map((insurance) => (
              <InsuranceCard key={insurance.id} insurance={insurance} />
            ))}
          </div>
        </div>
      </section>

      {/* Call to Action Banner */}
      <section className="py-20 px-4 sm:px-6 max-w-7xl mx-auto text-center">
        <div className="bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 rounded-3xl p-10 sm:p-14 shadow-2xl relative overflow-hidden">
          <div className="relative z-10 max-w-2xl mx-auto">
            <h2 className="text-3xl sm:text-4xl font-extrabold text-white font-['Manrope'] mb-4">
              Take Control of Your Medical Expenses Today
            </h2>
            <p className="text-blue-100 text-base mb-8">
              Join thousands of families utilizing MedSentinel to discover quality healthcare, cut hospitalization costs, and navigate health schemes with certainty.
            </p>
            <div className="flex flex-col sm:flex-row justify-center gap-4">
              <Link
                href="/login"
                className="px-8 py-4 bg-white text-blue-700 font-bold rounded-xl shadow-xl hover:bg-gray-100 transition-all text-sm"
              >
                Create Free Account
              </Link>
              <Link
                href="/appointments"
                className="px-8 py-4 bg-black/30 hover:bg-black/40 text-white font-bold rounded-xl border border-white/20 transition-all text-sm"
              >
                Book a Consultation
              </Link>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

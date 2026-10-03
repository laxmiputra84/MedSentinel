'use client';

import React, { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { Hospital } from '@/lib/types';
import api from '@/lib/api';

export default function HospitalDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const hospitalId = params?.id;

  const [hospital, setHospital] = useState<Hospital | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!hospitalId) return;

    const fetchHospital = async () => {
      try {
        const res = await api.get<Hospital>(`/hospitals/${hospitalId}`);
        setHospital(res.data);
      } catch (err: any) {
        setError('Hospital details could not be found.');
      } finally {
        setLoading(false);
      }
    };
    fetchHospital();
  }, [hospitalId]);

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-16 text-center">
        <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
        <p className="text-gray-400 text-sm">Loading Hospital Profile...</p>
      </div>
    );
  }

  if (error || !hospital) {
    return (
      <div className="max-w-xl mx-auto px-4 py-16 text-center">
        <div className="bg-gray-800/80 rounded-2xl p-8 border border-white/10">
          <span className="material-symbols-outlined text-red-400 text-4xl mb-2">error</span>
          <h2 className="text-xl font-bold text-white mb-2">Hospital Not Found</h2>
          <p className="text-gray-400 text-sm mb-6">{error || 'Invalid hospital ID.'}</p>
          <Link
            href="/hospitals"
            className="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl text-xs transition-all inline-block"
          >
            ← Back to Hospitals
          </Link>
        </div>
      </div>
    );
  }

  const schemeList = hospital.schemes ? hospital.schemes.split(',').map((s) => s.trim()) : [];
  const facilityList = hospital.facilities ? hospital.facilities.split(',').map((f) => f.trim()) : [];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Breadcrumb */}
      <div className="mb-6 flex items-center space-x-2 text-xs text-gray-400">
        <Link href="/" className="hover:text-white">Home</Link>
        <span>/</span>
        <Link href="/hospitals" className="hover:text-white">Hospitals</Link>
        <span>/</span>
        <span className="text-white font-medium">{hospital.name}</span>
      </div>

      {/* Hero Banner Grid */}
      <div className="grid lg:grid-cols-3 gap-8 mb-8">
        <div className="lg:col-span-2">
          <div className="relative h-96 rounded-3xl overflow-hidden group shadow-2xl border border-white/10 bg-gray-800">
            <img
              src="https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?w=1200&h=600&fit=crop"
              alt={hospital.name}
              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700 opacity-70"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-black via-black/60 to-transparent"></div>
            <div className="absolute bottom-0 left-0 right-0 p-6 sm:p-8">
              <div className="flex flex-wrap gap-2 mb-3">
                <span className="px-3 py-1 bg-emerald-500/90 backdrop-blur-sm text-white text-xs font-semibold rounded-lg shadow">
                  NABH Accredited
                </span>
                <span className="px-3 py-1 bg-blue-500/90 backdrop-blur-sm text-white text-xs font-semibold rounded-lg shadow">
                  {hospital.specialization || 'Multispecialty Center'}
                </span>
              </div>
              <h1 className="text-3xl sm:text-4xl font-black text-white font-['Manrope'] mb-2">
                {hospital.name}
              </h1>
              <p className="text-gray-300 text-sm sm:text-base flex items-center gap-1.5">
                <span className="material-symbols-outlined text-blue-400">location_on</span>
                <span>{hospital.location || 'Central City'}</span>
                <span className="text-gray-500">•</span>
                <span className="text-emerald-400 font-semibold">{hospital.distance} km from your area</span>
              </p>
            </div>
          </div>
        </div>

        {/* Pricing & Booking Card */}
        <div className="space-y-4">
          <div className="bg-gray-800/90 backdrop-blur-xl rounded-2xl p-6 border border-white/10 shadow-xl space-y-6">
            <div>
              <span className="text-xs text-gray-400">Estimated Procedure Cost</span>
              <div className="text-3xl font-black bg-gradient-to-r from-emerald-400 to-teal-300 bg-clip-text text-transparent font-['Manrope'] mt-1">
                {hospital.cost_range || '₹75,000 - ₹1,20,000'}
              </div>
              <span className="text-xs text-gray-400">Average tariff across common procedures</span>
            </div>

            <div className="space-y-3">
              <Link
                href={`/appointments?hospitalId=${hospital.id}&hospitalName=${encodeURIComponent(hospital.name)}`}
                className="w-full py-3.5 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-bold rounded-xl text-center text-sm shadow-lg transition-all block"
              >
                Book Doctor Consultation
              </Link>
              <Link
                href={`/eligibility?scheme=${encodeURIComponent(schemeList[0] || 'Ayushman Bharat')}`}
                className="w-full py-3.5 bg-white/10 hover:bg-white/20 text-white font-bold rounded-xl text-center text-sm border border-white/15 transition-all block"
              >
                Check Scheme Coverage
              </Link>
            </div>
          </div>

          <div className="bg-emerald-950/40 backdrop-blur-xl rounded-2xl p-6 border border-emerald-500/30 shadow-xl">
            <div className="flex items-center space-x-3 mb-2">
              <span className="material-symbols-outlined text-emerald-400 text-3xl">savings</span>
              <div>
                <div className="text-xs text-gray-300">Potential Scheme Benefit</div>
                <div className="text-2xl font-bold text-emerald-400 font-['Manrope']">Up to 100% Cashless</div>
              </div>
            </div>
            <p className="text-xs text-gray-300">
              Eligible patients with PM-JAY or state ration cards receive cashless hospitalization.
            </p>
          </div>
        </div>
      </div>

      {/* Main Details Grid */}
      <div className="grid lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-8">
          {/* Overview & Description */}
          <div className="bg-gray-800/80 backdrop-blur-xl rounded-2xl p-6 sm:p-8 border border-white/10 shadow-xl">
            <h2 className="text-2xl font-bold mb-4 text-white font-['Manrope'] flex items-center gap-2">
              <span className="material-symbols-outlined text-blue-400">info</span>
              About {hospital.name}
            </h2>
            <p className="text-gray-300 text-sm leading-relaxed mb-6">
              {hospital.description ||
                'Equipped with state-of-the-art diagnostic imaging, 24/7 intensive care units, and a dedicated team of super-specialist doctors catering to both elective and critical emergency treatments.'}
            </p>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-center">
              <div className="bg-black/30 p-4 rounded-xl border border-white/5">
                <div className="text-2xl font-bold text-yellow-400 flex items-center justify-center gap-1">
                  <span className="material-symbols-outlined text-lg">star</span>
                  <span>{hospital.rating?.toFixed(1) || '4.8'}</span>
                </div>
                <span className="text-xs text-gray-400 mt-1 block">Patient Rating</span>
              </div>

              <div className="bg-black/30 p-4 rounded-xl border border-white/5">
                <div className="text-2xl font-bold text-blue-400">24/7</div>
                <span className="text-xs text-gray-400 mt-1 block">Emergency Services</span>
              </div>

              <div className="bg-black/30 p-4 rounded-xl border border-white/5">
                <div className="text-2xl font-bold text-purple-400">{schemeList.length} Schemes</div>
                <span className="text-xs text-gray-400 mt-1 block">Government Empanelled</span>
              </div>
            </div>
          </div>

          {/* Key Facilities */}
          <div className="bg-gray-800/80 backdrop-blur-xl rounded-2xl p-6 sm:p-8 border border-white/10 shadow-xl">
            <h2 className="text-2xl font-bold mb-6 text-white font-['Manrope'] flex items-center gap-2">
              <span className="material-symbols-outlined text-purple-400">local_hospital</span>
              Facilities & Infrastructure
            </h2>
            <div className="grid sm:grid-cols-2 gap-3">
              {facilityList.map((facility, idx) => (
                <div key={idx} className="flex items-center gap-3 p-3.5 bg-black/30 rounded-xl border border-white/5">
                  <span className="material-symbols-outlined text-blue-400 text-xl">check_circle</span>
                  <span className="text-sm text-gray-200 font-medium">{facility}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Sidebar: Schemes & Contact Info */}
        <div className="space-y-6">
          <div className="bg-gray-800/80 backdrop-blur-xl rounded-2xl p-6 border border-white/10 shadow-xl">
            <h3 className="text-lg font-bold text-white font-['Manrope'] mb-4 flex items-center gap-2">
              <span className="material-symbols-outlined text-purple-400">verified</span>
              Accepted Health Schemes
            </h3>
            <div className="space-y-2.5">
              {schemeList.map((scheme, idx) => (
                <div key={idx} className="p-3 bg-black/30 rounded-xl border border-white/5 flex items-center justify-between">
                  <span className="text-xs font-semibold text-white">{scheme}</span>
                  <span className="text-xs text-emerald-400 font-bold">Empanelled</span>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-gray-800/80 backdrop-blur-xl rounded-2xl p-6 border border-white/10 shadow-xl space-y-4">
            <h3 className="text-lg font-bold text-white font-['Manrope'] flex items-center gap-2">
              <span className="material-symbols-outlined text-blue-400">contacts</span>
              Hospital Helpdesk
            </h3>
            <div className="space-y-3 text-xs text-gray-300">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-base text-blue-400">phone</span>
                <span>{hospital.phone || '+91-1800-SENTINEL'}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-base text-blue-400">mail</span>
                <span>{hospital.email || 'admissions@medsentinel.in'}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-base text-blue-400">location_on</span>
                <span>{hospital.location}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

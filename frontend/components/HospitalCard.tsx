'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { Hospital } from '@/lib/types';
import api from '@/lib/api';
import { useAuth } from '@/lib/authContext';

interface HospitalCardProps {
  hospital: Hospital;
  isSaved?: boolean;
  onSaveToggle?: (hospitalId: number, saved: boolean) => void;
  onCompareToggle?: (hospital: Hospital) => void;
  isCompared?: boolean;
}

export const HospitalCard: React.FC<HospitalCardProps> = ({
  hospital,
  isSaved = false,
  onSaveToggle,
  onCompareToggle,
  isCompared = false,
}) => {
  const { isAuthenticated } = useAuth();
  const [saved, setSaved] = useState(isSaved);
  const [saving, setSaving] = useState(false);

  const handleBookmark = async (e: React.MouseEvent) => {
    e.preventDefault();
    if (!isAuthenticated) {
      window.location.href = '/login';
      return;
    }

    setSaving(true);
    try {
      if (saved) {
        await api.delete(`/saved-items/${hospital.id}`);
        setSaved(false);
        onSaveToggle?.(hospital.id, false);
      } else {
        await api.post('/saved-items', { hospital_id: hospital.id });
        setSaved(true);
        onSaveToggle?.(hospital.id, true);
      }
    } catch (err) {
      console.error('Failed to update bookmark:', err);
    } finally {
      setSaving(false);
    }
  };

  const schemeList = hospital.schemes ? hospital.schemes.split(',').map((s) => s.trim()) : [];
  const facilityList = hospital.facilities ? hospital.facilities.split(',').map((f) => f.trim()) : [];

  return (
    <div className="bg-gray-800/80 backdrop-blur-md rounded-2xl border border-white/10 p-6 shadow-xl card-hover flex flex-col justify-between transition-all">
      <div>
        {/* Top bar: specialization badge + verification + rating & bookmark */}
        <div className="flex justify-between items-start mb-4 gap-2 flex-wrap">
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="px-3 py-1 bg-blue-500/20 border border-blue-500/30 text-blue-300 text-xs font-semibold rounded-full uppercase tracking-wider">
              {hospital.specialization || 'Multispecialty'}
            </span>
            <span className="px-2 py-0.5 bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 text-xs font-medium rounded-md flex items-center gap-1">
              <span className="material-symbols-outlined text-xs text-emerald-400">verified</span>
              <span>Verified</span>
            </span>
            {hospital.is_available !== undefined && hospital.is_available !== null && (
              <span className={`px-2 py-0.5 text-xs font-medium rounded-md border flex items-center gap-1 ${
                hospital.is_available
                  ? 'bg-green-500/15 border-green-500/30 text-green-300'
                  : 'bg-amber-500/15 border-amber-500/30 text-amber-300'
              }`}>
                <span className={`w-1.5 h-1.5 rounded-full ${hospital.is_available ? 'bg-green-400 animate-pulse' : 'bg-amber-400'}`}></span>
                <span>{hospital.is_available ? 'Available' : 'Occupied'}</span>
              </span>
            )}
          </div>
          <div className="flex items-center space-x-2">
            <span className="flex items-center space-x-1 bg-yellow-500/20 border border-yellow-500/30 text-yellow-300 px-2 py-0.5 rounded-lg text-xs font-bold">
              <span className="material-symbols-outlined text-sm text-yellow-400">star</span>
              <span>{hospital.rating ? hospital.rating.toFixed(1) : '4.5'}</span>
            </span>
            <button
              onClick={handleBookmark}
              disabled={saving}
              className={`p-1.5 rounded-lg border transition-all ${
                saved
                  ? 'bg-red-500/20 border-red-500/40 text-red-400 hover:bg-red-500/30'
                  : 'bg-white/5 border-white/10 text-gray-400 hover:text-white hover:bg-white/10'
              }`}
              title={saved ? 'Remove from saved' : 'Save hospital'}
            >
              <span className="material-symbols-outlined text-lg">
                {saved ? 'favorite' : 'favorite_border'}
              </span>
            </button>
          </div>
        </div>

        {/* Hospital Name & Location */}
        <h3 className="text-xl font-bold text-white font-['Manrope'] mb-1 hover:text-blue-400 transition-colors">
          <Link href={`/hospitals/${hospital.id}`}>{hospital.name}</Link>
        </h3>
        <p className="text-gray-400 text-sm flex items-center gap-1 mb-4 flex-wrap">
          <span className="material-symbols-outlined text-base text-gray-400">location_on</span>
          <span>{hospital.location || 'Central Location'}</span>
          {hospital.distance_km != null ? (
            <>
              <span className="text-gray-600">•</span>
              <span className="text-emerald-400 font-semibold flex items-center gap-0.5">
                <span className="material-symbols-outlined text-xs">near_me</span>
                <span>{hospital.distance_km} km away</span>
              </span>
            </>
          ) : (
            <>
              <span className="text-gray-600">•</span>
              <span className="text-gray-500 text-xs font-normal flex items-center gap-0.5">
                <span className="material-symbols-outlined text-xs">location_off</span>
                <span>Distance uncalculated (Enable GPS)</span>
              </span>
            </>
          )}
        </p>

        {/* Estimated Treatment Cost */}
        <div className="bg-black/30 rounded-xl p-3.5 border border-white/5 mb-4">
          <div className="text-xs text-gray-400 mb-0.5">Average Treatment Cost</div>
          <div className="text-2xl font-black text-emerald-400 font-['Manrope']">
            {hospital.cost_range || '₹75,000 - ₹1,20,000'}
          </div>
        </div>

        {/* Supported Government Schemes */}
        {schemeList.length > 0 && (
          <div className="mb-4">
            <div className="text-xs text-gray-400 mb-1.5 flex items-center gap-1">
              <span className="material-symbols-outlined text-xs text-purple-400">verified</span>
              <span>Accepted Schemes:</span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {schemeList.map((s, idx) => (
                <span
                  key={idx}
                  className="px-2 py-0.5 bg-purple-500/15 border border-purple-500/25 text-purple-300 text-xs rounded-md"
                >
                  {s}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Facilities */}
        {facilityList.length > 0 && (
          <div className="mb-4">
            <div className="text-xs text-gray-400 mb-1.5">Key Facilities:</div>
            <div className="flex flex-wrap gap-1.5 text-xs text-gray-300">
              {facilityList.slice(0, 3).map((f, idx) => (
                <span key={idx} className="bg-white/5 px-2 py-0.5 rounded border border-white/10">
                  {f}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="pt-4 border-t border-white/10 flex items-center gap-2">
        <Link
          href={`/hospitals/${hospital.id}`}
          className="flex-1 py-2.5 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white font-semibold rounded-xl text-center text-sm shadow-md transition-all flex items-center justify-center gap-1"
        >
          <span>View Details</span>
          <span className="material-symbols-outlined text-sm">arrow_forward</span>
        </Link>
        {onCompareToggle && (
          <button
            onClick={() => onCompareToggle(hospital)}
            className={`px-3 py-2.5 rounded-xl border text-sm font-semibold transition-all flex items-center gap-1 ${
              isCompared
                ? 'bg-purple-600 text-white border-purple-500'
                : 'bg-white/5 border-white/10 text-gray-300 hover:bg-white/10 hover:text-white'
            }`}
            title="Compare with other hospitals"
          >
            <span className="material-symbols-outlined text-base">
              {isCompared ? 'check' : 'compare_arrows'}
            </span>
            <span className="hidden sm:inline">{isCompared ? 'Added' : 'Compare'}</span>
          </button>
        )}
      </div>
    </div>
  );
};

'use client';

import React from 'react';
import Link from 'next/link';
import { Insurance } from '@/lib/types';

interface InsuranceCardProps {
  insurance: Insurance;
  onEnrollClick?: (insurance: Insurance) => void;
}

export const InsuranceCard: React.FC<InsuranceCardProps> = ({ insurance, onEnrollClick }) => {
  const inclusionList = insurance.inclusions ? insurance.inclusions.split(',').map((i) => i.trim()) : [];

  return (
    <div className="bg-gray-800/80 backdrop-blur-md rounded-2xl border border-white/10 p-6 shadow-xl card-hover flex flex-col justify-between">
      <div>
        <div className="flex justify-between items-start mb-4">
          <div>
            <span className="px-3 py-1 bg-emerald-500/20 border border-emerald-500/30 text-emerald-300 text-xs font-semibold rounded-full uppercase tracking-wider">
              {insurance.coverage_type || 'Comprehensive'}
            </span>
            <div className="text-xs text-gray-400 mt-1 font-medium">{insurance.provider}</div>
          </div>
          <span className="flex items-center space-x-1 bg-yellow-500/20 border border-yellow-500/30 text-yellow-300 px-2 py-0.5 rounded-lg text-xs font-bold">
            <span className="material-symbols-outlined text-sm text-yellow-400">star</span>
            <span>{insurance.rating?.toFixed(1) || '4.6'}</span>
          </span>
        </div>

        <h3 className="text-xl font-bold text-white font-['Manrope'] mb-3 hover:text-blue-400 transition-colors">
          <Link href={`/insurance-details/${insurance.id}`}>{insurance.name}</Link>
        </h3>

        {/* Pricing Matrix */}
        <div className="grid grid-cols-2 gap-2 bg-black/30 rounded-xl p-3 border border-white/5 mb-4">
          <div>
            <div className="text-xs text-gray-400">Sum Insured</div>
            <div className="text-lg font-bold text-emerald-400 font-['Manrope']">
              ₹{(insurance.coverage_amount / 100000).toFixed(1)} Lakhs
            </div>
          </div>
          <div>
            <div className="text-xs text-gray-400">Monthly Premium</div>
            <div className="text-lg font-bold text-blue-400 font-['Manrope']">
              ₹{insurance.premium_monthly.toLocaleString()}/mo
            </div>
          </div>
        </div>

        {/* Key Features */}
        <div className="space-y-2 mb-4 text-xs text-gray-300">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-sm text-emerald-400">domain</span>
            <span>Cashless at <strong className="text-white">{insurance.cashless_network.toLocaleString()}+</strong> hospitals</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-sm text-blue-400">hourglass_top</span>
            <span>Waiting Period: <strong className="text-white">{insurance.waiting_period_days} Days</strong></span>
          </div>
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-sm text-purple-400">speed</span>
            <span>Settlement: <strong className="text-white">{insurance.claim_settlement_days} Days TAT</strong></span>
          </div>
        </div>

        {/* Inclusions */}
        {inclusionList.length > 0 && (
          <div className="mb-4">
            <div className="text-xs text-gray-400 mb-1.5">Includes:</div>
            <div className="flex flex-wrap gap-1.5">
              {inclusionList.slice(0, 3).map((item, idx) => (
                <span
                  key={idx}
                  className="px-2 py-0.5 bg-white/5 border border-white/10 text-gray-300 text-xs rounded-md"
                >
                  ✓ {item}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="pt-4 border-t border-white/10 flex items-center gap-2">
        <Link
          href={`/insurance-details/${insurance.id}`}
          className="flex-1 py-2.5 bg-white/10 hover:bg-white/20 text-white font-semibold rounded-xl text-center text-sm transition-all"
        >
          View Details
        </Link>
        <button
          onClick={() => onEnrollClick?.(insurance)}
          className="py-2.5 px-4 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 text-white font-semibold rounded-xl text-sm shadow-md transition-all flex items-center gap-1"
        >
          <span>Enroll</span>
          <span className="material-symbols-outlined text-sm">arrow_forward</span>
        </button>
      </div>
    </div>
  );
};

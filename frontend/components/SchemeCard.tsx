'use client';

import React from 'react';
import Link from 'next/link';
import { Scheme } from '@/lib/types';

export const SchemeCard: React.FC<{ scheme: Scheme }> = ({ scheme }) => {
  return (
    <div className="bg-gray-800/80 backdrop-blur-md rounded-2xl border border-white/10 p-6 shadow-xl card-hover flex flex-col justify-between">
      <div>
        <div className="flex justify-between items-start mb-4">
          <span className="px-3 py-1 bg-purple-500/20 border border-purple-500/30 text-purple-300 text-xs font-semibold rounded-full uppercase tracking-wider">
            {scheme.type || 'National Scheme'}
          </span>
          <span className="w-8 h-8 bg-emerald-500/20 rounded-lg flex items-center justify-center text-emerald-400">
            <span className="material-symbols-outlined text-lg">shield_with_heart</span>
          </span>
        </div>

        <h3 className="text-xl font-bold text-white font-['Manrope'] mb-2">{scheme.name}</h3>
        <p className="text-gray-300 text-sm leading-relaxed mb-6">{scheme.description}</p>

        <div className="space-y-3 mb-6">
          <div className="bg-black/30 rounded-xl p-3 border border-white/5 flex items-center justify-between">
            <span className="text-xs text-gray-400">Annual Max Coverage:</span>
            <span className="text-emerald-400 font-bold font-['Manrope']">{scheme.coverage || '₹5,00,000 / Family'}</span>
          </div>

          <div className="bg-black/30 rounded-xl p-3 border border-white/5">
            <span className="text-xs text-gray-400 block mb-1">Target Eligibility:</span>
            <span className="text-xs text-gray-300">{scheme.eligibility || 'Low income households and vulnerable families'}</span>
          </div>
        </div>
      </div>

      <div className="pt-4 border-t border-white/10 flex items-center gap-3">
        <Link
          href={`/eligibility?scheme=${encodeURIComponent(scheme.name)}`}
          className="flex-1 py-2.5 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white font-semibold rounded-xl text-center text-sm shadow-md transition-all flex items-center justify-center gap-1.5"
        >
          <span>Check Eligibility</span>
          <span className="material-symbols-outlined text-sm">checklist</span>
        </Link>
        <Link
          href={`/hospitals?scheme=${encodeURIComponent(scheme.name)}`}
          className="px-4 py-2.5 bg-white/5 border border-white/10 hover:bg-white/10 text-gray-200 text-sm font-semibold rounded-xl transition-all"
        >
          Hospitals
        </Link>
      </div>
    </div>
  );
};

'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { Scheme } from '@/lib/types';
import { SchemeCard } from '@/components/SchemeCard';
import api from '@/lib/api';

export default function SchemesPage() {
  const [schemes, setSchemes] = useState<Scheme[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSchemes = async () => {
      try {
        const res = await api.get<Scheme[]>('/schemes');
        setSchemes(res.data);
      } catch (err) {
        console.error('Error fetching schemes:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchSchemes();
  }, []);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-purple-900/60 via-indigo-900/60 to-blue-900/60 backdrop-blur-xl rounded-3xl p-8 sm:p-12 border border-purple-500/20 shadow-2xl mb-12 flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
        <div>
          <span className="text-purple-300 font-bold uppercase tracking-wider text-xs">Public Healthcare Assistance</span>
          <h1 className="text-3xl sm:text-5xl font-extrabold text-white font-['Manrope'] mt-1 mb-3">
            Government Healthcare Schemes
          </h1>
          <p className="text-purple-100 text-sm max-w-xl">
            Learn about national and state-backed health coverage programs providing cashless treatments up to ₹5 Lakhs per family.
          </p>
        </div>

        <Link
          href="/eligibility"
          className="px-8 py-4 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white font-bold rounded-xl text-sm shadow-xl transition-all whitespace-nowrap transform hover:scale-105"
        >
          Check My Eligibility →
        </Link>
      </div>

      {/* Schemes Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="bg-gray-800/40 rounded-2xl h-72 animate-pulse border border-white/5"></div>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {schemes.map((scheme) => (
            <SchemeCard key={scheme.id} scheme={scheme} />
          ))}
        </div>
      )}
    </div>
  );
}

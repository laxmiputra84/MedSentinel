'use client';

import React, { useState, useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { Hospital } from '@/lib/types';
import api from '@/lib/api';

export default function ComparisonPage() {
  return (
    <Suspense
      fallback={
        <div className="max-w-7xl mx-auto px-4 py-16 text-center text-gray-400 text-sm">
          <div className="w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
          Loading Comparison Dashboard...
        </div>
      }
    >
      <ComparisonContent />
    </Suspense>
  );
}

function ComparisonContent() {
  const searchParams = useSearchParams();
  const [allHospitals, setAllHospitals] = useState<Hospital[]>([]);
  const [selectedHospitals, setSelectedHospitals] = useState<Hospital[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchHospitals = async () => {
      try {
        const res = await api.get<Hospital[]>('/hospitals');
        setAllHospitals(res.data);

        // Check if query params have ids
        const idString = searchParams.get('ids');
        if (idString) {
          const ids = idString.split(',').map((id) => parseInt(id.trim(), 10));
          const matched = res.data.filter((h) => ids.includes(h.id));
          setSelectedHospitals(matched.length > 0 ? matched : res.data.slice(0, 3));
        } else {
          setSelectedHospitals(res.data.slice(0, 3));
        }
      } catch (err) {
        console.error('Error fetching hospitals for comparison:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchHospitals();
  }, [searchParams]);

  const handleAddHospital = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const id = parseInt(e.target.value, 10);
    if (!id) return;
    const target = allHospitals.find((h) => h.id === id);
    if (target && !selectedHospitals.some((h) => h.id === id)) {
      if (selectedHospitals.length >= 4) {
        alert('You can compare a maximum of 4 hospitals simultaneously.');
        return;
      }
      setSelectedHospitals([...selectedHospitals, target]);
    }
  };

  const handleRemoveHospital = (id: number) => {
    if (selectedHospitals.length <= 1) {
      alert('Keep at least 1 hospital in comparison.');
      return;
    }
    setSelectedHospitals(selectedHospitals.filter((h) => h.id !== id));
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-16 text-center">
        <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
        <p className="text-gray-400 text-sm">Loading Comparison Intelligence Dashboard...</p>
      </div>
    );
  }

  const bestValueHospital = selectedHospitals[0] || allHospitals[0];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      {/* Header */}
      <header className="mb-12">
        <span className="text-blue-400 font-bold uppercase tracking-wider text-xs">Precision Analytics</span>
        <h1 className="text-4xl sm:text-5xl font-extrabold mb-4 bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent font-['Manrope']">
          Hospital Cost Intelligence Matrix
        </h1>
        <p className="text-gray-300 text-base max-w-2xl">
          Side-by-side comparative analysis of treatment tariffs, patient ratings, empanelled healthcare schemes, and facilities.
        </p>

        {/* Add Hospital selector */}
        <div className="mt-6 flex flex-wrap items-center gap-3">
          <span className="text-xs text-gray-400 font-semibold">Add Hospital to Matrix:</span>
          <select
            onChange={handleAddHospital}
            value=""
            className="px-4 py-2 bg-gray-800 border border-white/20 rounded-xl text-white text-xs focus:outline-none focus:border-blue-500"
          >
            <option value="">Select hospital to add...</option>
            {allHospitals
              .filter((h) => !selectedHospitals.some((s) => s.id === h.id))
              .map((h) => (
                <option key={h.id} value={h.id}>
                  {h.name} ({h.location})
                </option>
              ))}
          </select>
        </div>
      </header>

      {/* Highlights Bar */}
      <div className="grid md:grid-cols-3 gap-6 mb-8">
        <div className="md:col-span-2 bg-gray-800/80 backdrop-blur-xl p-6 sm:p-8 rounded-2xl border border-white/10 shadow-xl">
          <h4 className="font-bold text-base text-white mb-4 flex items-center gap-2">
            <span className="material-symbols-outlined text-blue-400">bar_chart</span>
            <span>Comparative Cost Distribution</span>
          </h4>
          <div className="space-y-4">
            {selectedHospitals.map((h) => (
              <div key={h.id}>
                <div className="flex justify-between text-xs mb-1">
                  <span className="font-semibold text-gray-200">{h.name}</span>
                  <span className="text-emerald-400 font-bold">{h.cost_range || '₹85,000'}</span>
                </div>
                <div className="w-full h-3 bg-black/40 rounded-full overflow-hidden border border-white/5">
                  <div
                    className="h-full bg-gradient-to-r from-blue-500 to-purple-600 rounded-full"
                    style={{
                      width: `${Math.min(100, Math.max(30, (h.rating / 5) * 100))}%`,
                    }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Best Value Highlight */}
        <div className="bg-emerald-950/40 backdrop-blur-xl p-6 sm:p-8 rounded-2xl border border-emerald-500/30 shadow-xl flex flex-col justify-between">
          <div>
            <span className="bg-emerald-500/90 text-white text-xs font-bold px-2.5 py-1 rounded-lg uppercase tracking-wider">
              Top Value Pick
            </span>
            <h4 className="text-2xl font-bold text-white font-['Manrope'] mt-4">
              {bestValueHospital?.name}
            </h4>
            <p className="text-xs text-gray-300 mt-2">
              Optimal balance between high clinical rating ({bestValueHospital?.rating}★) and affordable treatment pricing.
            </p>
          </div>

          <div className="mt-6 pt-4 border-t border-emerald-500/20 flex justify-between items-end">
            <div>
              <p className="text-xs uppercase text-gray-400 font-bold">Estimated Cost</p>
              <p className="text-emerald-400 text-2xl font-black">{bestValueHospital?.cost_range}</p>
            </div>
            <Link
              href={`/hospitals/${bestValueHospital?.id}`}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-lg shadow transition-all"
            >
              View →
            </Link>
          </div>
        </div>
      </div>

      {/* Comparison Table */}
      <div className="bg-gray-800/80 backdrop-blur-xl rounded-2xl overflow-hidden border border-white/10 shadow-2xl mb-8">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-black/40 border-b border-white/10">
                <th className="p-5 font-bold text-gray-400 text-xs uppercase tracking-wider w-48">
                  Criteria / Feature
                </th>
                {selectedHospitals.map((h) => (
                  <th key={h.id} className="p-5 font-bold text-white text-sm min-w-[220px]">
                    <div className="flex justify-between items-start">
                      <div>
                        <div className="font-extrabold text-base text-white">{h.name}</div>
                        <div className="text-xs text-gray-400 font-normal">{h.location}</div>
                      </div>
                      <button
                        onClick={() => handleRemoveHospital(h.id)}
                        className="text-gray-400 hover:text-red-400 p-1 rounded transition-colors"
                        title="Remove hospital"
                      >
                        <span className="material-symbols-outlined text-base">close</span>
                      </button>
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-white/10 text-sm">
              {/* Average Tariff */}
              <tr>
                <td className="p-5 font-semibold text-gray-300 text-xs">Estimated Cost</td>
                {selectedHospitals.map((h) => (
                  <td key={h.id} className="p-5">
                    <span className="text-lg font-black text-emerald-400 font-['Manrope']">
                      {h.cost_range || '₹85,000'}
                    </span>
                    <p className="text-xs text-gray-400 mt-0.5">Average procedure tariff</p>
                  </td>
                ))}
              </tr>

              {/* Specialization */}
              <tr>
                <td className="p-5 font-semibold text-gray-300 text-xs">Specialization</td>
                {selectedHospitals.map((h) => (
                  <td key={h.id} className="p-5 font-medium text-gray-200">
                    <span className="px-2.5 py-1 bg-blue-500/20 border border-blue-500/30 text-blue-300 rounded-md text-xs font-semibold">
                      {h.specialization || 'Multispecialty'}
                    </span>
                  </td>
                ))}
              </tr>

              {/* Patient Rating */}
              <tr>
                <td className="p-5 font-semibold text-gray-300 text-xs">Patient Rating</td>
                {selectedHospitals.map((h) => (
                  <td key={h.id} className="p-5">
                    <div className="flex items-center gap-1 text-yellow-400 font-bold">
                      <span className="material-symbols-outlined text-base">star</span>
                      <span>{h.rating?.toFixed(1) || '4.8'} / 5.0</span>
                    </div>
                  </td>
                ))}
              </tr>

              {/* Distance */}
              <tr>
                <td className="p-5 font-semibold text-gray-300 text-xs">Distance</td>
                {selectedHospitals.map((h) => (
                  <td key={h.id} className="p-5 text-gray-300 font-medium">
                    {h.distance} km from center
                  </td>
                ))}
              </tr>

              {/* Government Schemes */}
              <tr>
                <td className="p-5 font-semibold text-gray-300 text-xs">Empanelled Schemes</td>
                {selectedHospitals.map((h) => (
                  <td key={h.id} className="p-5">
                    <div className="flex flex-wrap gap-1.5">
                      {h.schemes ? (
                        h.schemes.split(',').map((s, idx) => (
                          <span
                            key={idx}
                            className="px-2 py-0.5 bg-purple-500/20 text-purple-300 text-xs rounded border border-purple-500/30 font-medium"
                          >
                            {s.trim()}
                          </span>
                        ))
                      ) : (
                        <span className="text-gray-500 text-xs">None listed</span>
                      )}
                    </div>
                  </td>
                ))}
              </tr>

              {/* Facilities */}
              <tr>
                <td className="p-5 font-semibold text-gray-300 text-xs">Infrastructure & Facilities</td>
                {selectedHospitals.map((h) => (
                  <td key={h.id} className="p-5 text-xs text-gray-300">
                    <ul className="space-y-1">
                      {h.facilities
                        ? h.facilities.split(',').map((f, idx) => (
                            <li key={idx} className="flex items-center gap-1.5">
                              <span className="material-symbols-outlined text-xs text-emerald-400">check</span>
                              <span>{f.trim()}</span>
                            </li>
                          ))
                        : 'Standard Hospital Care'}
                    </ul>
                  </td>
                ))}
              </tr>

              {/* Actions */}
              <tr className="bg-black/20">
                <td className="p-5 font-semibold text-gray-300 text-xs">Action</td>
                {selectedHospitals.map((h) => (
                  <td key={h.id} className="p-5">
                    <div className="space-y-2">
                      <Link
                        href={`/hospitals/${h.id}`}
                        className="block w-full py-2 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-lg text-center text-xs shadow transition-all"
                      >
                        Hospital Details
                      </Link>
                      <Link
                        href={`/appointments?hospitalId=${h.id}&hospitalName=${encodeURIComponent(h.name)}`}
                        className="block w-full py-2 bg-white/10 hover:bg-white/20 text-white font-semibold rounded-lg text-center text-xs border border-white/15 transition-all"
                      >
                        Book Visit
                      </Link>
                    </div>
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

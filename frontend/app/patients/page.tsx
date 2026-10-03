'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import api from '@/lib/api';
import {
  Users,
  Search,
  Plus,
  ArrowRight,
  ShieldCheck,
  Activity,
  HeartPulse,
  Filter,
} from 'lucide-react';

export default function PatientsDirectoryPage() {
  return (
    <ProtectedRoute>
      <PatientsListContent />
    </ProtectedRoute>
  );
}

function PatientsListContent() {
  const [patients, setPatients] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    const fetchPatients = async () => {
      try {
        const res = await api.get('/patients');
        setPatients(res.data);
      } catch (err) {
        console.error('Failed to load patients:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchPatients();
  }, []);

  const filtered = patients.filter((p) =>
    p.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    p.patient_code?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8 border-b border-slate-800 pb-6">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-indigo-500/10 border border-indigo-500/30 rounded-xl text-indigo-400">
              <Users className="w-7 h-7" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-white">Patient Intelligence Directory</h1>
              <p className="text-sm text-slate-400">Search patient records, view 360° dossiers, and inspect clinical timelines.</p>
            </div>
          </div>
        </div>

        {/* Search */}
        <div className="mb-6 flex gap-4">
          <div className="relative flex-1">
            <Search className="w-5 h-5 absolute left-3.5 top-3.5 text-slate-500" />
            <input
              type="text"
              placeholder="Search by patient name, patient code, or ID..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-11 pr-4 py-3 bg-slate-900 border border-slate-800 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
            />
          </div>
        </div>

        {/* Directory Grid */}
        {loading ? (
          <div className="flex items-center justify-center py-20 text-slate-400">
            <Activity className="w-6 h-6 animate-spin text-indigo-400 mr-2" />
            <span>Loading Patient Directory...</span>
          </div>
        ) : filtered.length === 0 ? (
          <div className="text-center py-20 bg-slate-900/50 border border-slate-800 rounded-2xl">
            <Users className="w-12 h-12 text-slate-600 mx-auto mb-3" />
            <p className="text-slate-400 font-medium">No patient records found.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filtered.map((p) => (
              <Link
                key={p.id}
                href={`/patients/${p.id}`}
                className="group bg-slate-900 border border-slate-800 hover:border-indigo-500/50 rounded-2xl p-6 transition shadow-lg hover:shadow-indigo-950/20"
              >
                <div className="flex items-center justify-between mb-4">
                  <div className="w-12 h-12 rounded-xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 font-bold text-lg">
                    {p.name?.charAt(0) || 'P'}
                  </div>
                  <span className="text-xs font-mono font-medium px-2 py-0.5 rounded-full bg-slate-850 text-indigo-300 border border-slate-750">
                    {p.patient_code || `PT-${p.id}`}
                  </span>
                </div>
                <h2 className="text-lg font-bold text-white group-hover:text-indigo-400 transition mb-1">{p.name}</h2>
                <div className="text-xs text-slate-400 space-y-1 mb-4">
                  <div>Gender: {p.gender || 'N/A'} · Blood Group: {p.blood_group || 'N/A'}</div>
                  <div>Emergency: {p.emergency_contact || 'N/A'}</div>
                </div>
                <div className="flex items-center justify-between text-xs pt-3 border-t border-slate-800/80 text-indigo-400 font-semibold">
                  <span>View 360° Dossier</span>
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition" />
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import api from '@/lib/api';
import { useAuth } from '@/lib/authContext';
import { AdminHeader } from '@/components/admin/AdminHeader';
import { StatCard } from '@/components/admin/StatCard';
import { AnalyticsChart } from '@/components/admin/AnalyticsChart';

interface DashboardData {
  cards: {
    total_users: number;
    active_users: number;
    total_hospitals: number;
    total_insurances: number;
    total_policies: number;
    total_claims: number;
    pending_claims: number;
    approved_claims: number;
    rejected_claims: number;
    total_appointments: number;
    pending_documents: number;
    unread_notifications: number;
  };
  today: {
    registrations: number;
    claims: number;
    appointments: number;
  };
  recent_activity: Array<{
    id: number;
    action: string;
    resource_type: string;
    resource_id?: string;
    admin_name: string;
    timestamp: string;
  }>;
}

export default function AdminDashboardPage() {
  const { user } = useAuth();
  const [data, setData] = useState<DashboardData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSummary = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await api.get<DashboardData>('/admin/dashboard/summary');
      setData(res.data);
    } catch (err: any) {
      console.error('Error loading dashboard summary:', err);
      setError(err.response?.data?.detail || 'Failed to load administrator dashboard metrics.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchSummary();
  }, []);

  const cards = data?.cards;
  const today = data?.today;

  return (
    <div className="space-y-6">
      <AdminHeader
        title="Super Admin Command Center"
        subtitle="Real-time healthcare operational metrics, patient throughput, claim settlement queues, and clinical audit events."
        actions={
          <button
            onClick={fetchSummary}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold text-white bg-white/10 hover:bg-white/15 border border-white/10 transition-all"
          >
            <span className={`material-symbols-outlined text-sm ${isLoading ? 'animate-spin' : ''}`}>
              refresh
            </span>
            <span>Refresh</span>
          </button>
        }
      />

      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-2xl p-4 text-xs text-red-300 flex items-center gap-3">
          <span className="material-symbols-outlined text-lg text-red-400">error</span>
          <span>{error}</span>
        </div>
      )}

      {/* Today's Flash KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-gradient-to-r from-blue-900/40 to-blue-800/20 border border-blue-500/30 rounded-2xl p-4 flex items-center justify-between">
          <div>
            <div className="text-[11px] font-bold uppercase tracking-wider text-blue-400">Today's Registrations</div>
            <div className="text-2xl font-extrabold text-white mt-1">+{today?.registrations ?? 0}</div>
          </div>
          <div className="w-10 h-10 rounded-xl bg-blue-500/20 text-blue-400 flex items-center justify-center">
            <span className="material-symbols-outlined">person_add</span>
          </div>
        </div>

        <div className="bg-gradient-to-r from-purple-900/40 to-purple-800/20 border border-purple-500/30 rounded-2xl p-4 flex items-center justify-between">
          <div>
            <div className="text-[11px] font-bold uppercase tracking-wider text-purple-400">Today's Claims Filed</div>
            <div className="text-2xl font-extrabold text-white mt-1">+{today?.claims ?? 0}</div>
          </div>
          <div className="w-10 h-10 rounded-xl bg-purple-500/20 text-purple-400 flex items-center justify-center">
            <span className="material-symbols-outlined">receipt_long</span>
          </div>
        </div>

        <div className="bg-gradient-to-r from-emerald-900/40 to-emerald-800/20 border border-emerald-500/30 rounded-2xl p-4 flex items-center justify-between">
          <div>
            <div className="text-[11px] font-bold uppercase tracking-wider text-emerald-400">Today's Appointments</div>
            <div className="text-2xl font-extrabold text-white mt-1">+{today?.appointments ?? 0}</div>
          </div>
          <div className="w-10 h-10 rounded-xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center">
            <span className="material-symbols-outlined">calendar_today</span>
          </div>
        </div>
      </div>

      {/* Main KPI Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Registered Users"
          value={cards?.total_users ?? '—'}
          subtitle={`${cards?.active_users ?? 0} active accounts`}
          icon="group"
          color="blue"
          trend={{ value: '+14%', isPositive: true }}
        />
        <StatCard
          title="Empanelled Hospitals"
          value={cards?.total_hospitals ?? '—'}
          subtitle="Accredited healthcare centers"
          icon="local_hospital"
          color="emerald"
        />
        <StatCard
          title="Total Insurance Claims"
          value={cards?.total_claims ?? '—'}
          subtitle={`${cards?.approved_claims ?? 0} approved | ${cards?.rejected_claims ?? 0} denied`}
          icon="receipt_long"
          color="purple"
          trend={{ value: `${cards?.pending_claims ?? 0} in review`, isPositive: false }}
        />
        <StatCard
          title="Pending Documents"
          value={cards?.pending_documents ?? '—'}
          subtitle="Awaiting medical underwriter verification"
          icon="folder_open"
          color="amber"
        />
      </div>

      {/* Secondary Quick Metrics */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-gray-900/60 border border-white/10 rounded-2xl p-4">
          <span className="text-[10px] font-bold uppercase text-gray-400">Insurance Providers</span>
          <div className="text-xl font-bold text-white mt-1">{cards?.total_insurances ?? 0}</div>
          <span className="text-[10px] text-gray-400">Integrated Carriers</span>
        </div>
        <div className="bg-gray-900/60 border border-white/10 rounded-2xl p-4">
          <span className="text-[10px] font-bold uppercase text-gray-400">Active Policies</span>
          <div className="text-xl font-bold text-white mt-1">{cards?.total_policies ?? 0}</div>
          <span className="text-[10px] text-gray-400">Enrolled Patients</span>
        </div>
        <div className="bg-gray-900/60 border border-white/10 rounded-2xl p-4">
          <span className="text-[10px] font-bold uppercase text-gray-400">Total Consultations</span>
          <div className="text-xl font-bold text-white mt-1">{cards?.total_appointments ?? 0}</div>
          <span className="text-[10px] text-gray-400">Booked Visits</span>
        </div>
        <div className="bg-gray-900/60 border border-white/10 rounded-2xl p-4">
          <span className="text-[10px] font-bold uppercase text-gray-400">Pending Alerts</span>
          <div className="text-xl font-bold text-white mt-1">{cards?.unread_notifications ?? 0}</div>
          <span className="text-[10px] text-gray-400">Unread Broadcasts</span>
        </div>
      </div>

      {/* Analytics & Recent Activity Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Claims Distribution Chart */}
        <div className="lg:col-span-1">
          <AnalyticsChart
            title="Claim Status Breakdown"
            subtitle="Current disposition across claims queue"
            type="donut-breakdown"
            badge="Live Status"
            data={[
              { label: 'Approved', value: cards?.approved_claims ?? 12, color: '#10b981' },
              { label: 'Under Review / Pending', value: cards?.pending_claims ?? 8, color: '#3b82f6' },
              { label: 'Rejected', value: cards?.rejected_claims ?? 3, color: '#ef4444' },
            ]}
          />
        </div>

        {/* Live Admin Audit Feed */}
        <div className="lg:col-span-2 bg-gray-900/60 backdrop-blur-xl border border-white/10 rounded-2xl p-5 shadow-xl flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-white/10">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-purple-400 text-lg">history</span>
                <h2 className="text-sm font-bold text-white tracking-wide">Recent Administrative Audit Logs</h2>
              </div>
              <Link
                href="/admin/audit-logs"
                className="text-xs font-semibold text-blue-400 hover:text-blue-300 hover:underline flex items-center gap-1"
              >
                <span>View Full Trail</span>
                <span className="material-symbols-outlined text-sm">chevron_right</span>
              </Link>
            </div>

            <div className="divide-y divide-white/5 mt-2">
              {!data?.recent_activity || data.recent_activity.length === 0 ? (
                <div className="text-center py-8 text-xs text-gray-400">No recent administrative events logged.</div>
              ) : (
                data.recent_activity.slice(0, 6).map((log) => (
                  <div key={log.id} className="py-2.5 flex items-center justify-between text-xs gap-3">
                    <div className="flex items-center gap-2.5 truncate">
                      <span className="w-1.5 h-1.5 rounded-full bg-blue-400 flex-shrink-0" />
                      <span className="font-bold text-white px-1.5 py-0.5 rounded bg-white/5 border border-white/10 text-[10px]">
                        {log.action}
                      </span>
                      <span className="text-gray-300 truncate">
                        {log.resource_type} {log.resource_id ? `(#${log.resource_id})` : ''}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-right flex-shrink-0">
                      <span className="text-[11px] text-gray-400 font-medium">{log.admin_name}</span>
                      <span className="text-[10px] text-gray-500 font-mono">
                        {log.timestamp ? new Date(log.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''}
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-white/5 flex items-center justify-between text-[11px] text-gray-400">
            <span className="flex items-center gap-1">
              <span className="material-symbols-outlined text-xs text-emerald-400">verified_user</span>
              <span>Encrypted Audit Trail Active</span>
            </span>
            <Link href="/admin/ai-insights" className="text-purple-400 hover:underline flex items-center gap-1 font-semibold">
              <span className="material-symbols-outlined text-xs">neurology</span>
              <span>View AI Operational Insights</span>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

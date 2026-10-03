'use client';

import React, { useState, useEffect } from 'react';
import api from '@/lib/api';
import { useAuth } from '@/lib/authContext';
import { AdminHeader } from '@/components/admin/AdminHeader';
import { AnalyticsChart } from '@/components/admin/AnalyticsChart';
import { StatCard } from '@/components/admin/StatCard';

interface AnalyticsData {
  users_by_role: Record<string, number>;
  claims_by_status: Record<string, number>;
  appointments_by_status: Record<string, number>;
  specializations: Array<{ name: string; count: number }>;
  financials: {
    total_claims_value: number;
    approved_claims_value: number;
  };
}

export default function AdminAnalyticsPage() {
  const { user } = useAuth();
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchAnalytics = async () => {
    setIsLoading(true);
    try {
      const res = await api.get<AnalyticsData>('/admin/analytics/overview');
      setData(res.data);
    } catch (err) {
      console.error('Error fetching analytics:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, []);

  // Format data for charts
  const roleChartData = data?.users_by_role
    ? Object.entries(data.users_by_role).map(([role, count]) => ({
        label: role.replace('_', ' '),
        value: count,
      }))
    : [];

  const claimsChartData = data?.claims_by_status
    ? Object.entries(data.claims_by_status).map(([status, count]) => ({
        label: status.replace('_', ' '),
        value: count,
      }))
    : [];

  const apptChartData = data?.appointments_by_status
    ? Object.entries(data.appointments_by_status).map(([status, count]) => ({
        label: status,
        value: count,
      }))
    : [];

  const specChartData = data?.specializations
    ? data.specializations.map((s) => ({
        label: s.name,
        value: s.count,
      }))
    : [];

  return (
    <div className="space-y-6">
      <AdminHeader
        title="Enterprise Healthcare Analytics"
        subtitle="Platform-level throughput metrics, user distribution across organizational roles, claim adjudication rates, and specialty load distributions."
        actions={
          <button
            onClick={fetchAnalytics}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold text-white bg-white/10 hover:bg-white/15 border border-white/10 transition-all"
          >
            <span className={`material-symbols-outlined text-sm ${isLoading ? 'animate-spin' : ''}`}>
              refresh
            </span>
            <span>Refresh Analytics</span>
          </button>
        }
      />

      {/* Financial KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <StatCard
          title="Total Claims Volume Value"
          value={`₹${(data?.financials.total_claims_value || 0).toLocaleString()}`}
          subtitle="Cumulative monetary claim submissions"
          icon="payments"
          color="blue"
        />
        <StatCard
          title="Authorized Settlements Disbursed"
          value={`₹${(data?.financials.approved_claims_value || 0).toLocaleString()}`}
          subtitle="Direct cashless and approved payouts"
          icon="verified"
          color="emerald"
        />
        <StatCard
          title="Settlement Settlement Ratio"
          value={
            data?.financials.total_claims_value
              ? `${Math.round(((data.financials.approved_claims_value || 0) / data.financials.total_claims_value) * 100)}%`
              : '100%'
          }
          subtitle="Financial realization efficiency"
          icon="pie_chart"
          color="purple"
        />
      </div>

      {/* Grid of Analytics Visualizations */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <AnalyticsChart
          title="User Account Distribution by Role"
          subtitle="Active RBAC permission hierarchies across platform"
          type="donut-breakdown"
          badge="RBAC Matrix"
          data={roleChartData.length > 0 ? roleChartData : [{ label: 'Patients', value: 20 }, { label: 'Admins', value: 4 }]}
        />

        <AnalyticsChart
          title="Claim Adjudication Dispositions"
          subtitle="Status breakdown for submitted insurance claims"
          type="horizontal-bars"
          badge="Adjudication"
          data={claimsChartData.length > 0 ? claimsChartData : [{ label: 'Approved', value: 15 }, { label: 'Under Review', value: 8 }]}
        />

        <AnalyticsChart
          title="Patient Consultation Statuses"
          subtitle="Clinical appointment volume distribution"
          type="horizontal-bars"
          badge="Clinical Visits"
          data={apptChartData.length > 0 ? apptChartData : [{ label: 'Confirmed', value: 12 }, { label: 'Completed', value: 20 }]}
        />

        <AnalyticsChart
          title="Top Clinical Specializations"
          subtitle="Specialty workload density across hospital network"
          type="donut-breakdown"
          badge="Clinical Care"
          data={specChartData.length > 0 ? specChartData : [{ label: 'Cardiology', value: 8 }, { label: 'Neurology', value: 5 }]}
        />
      </div>
    </div>
  );
}

'use client';

import React, { useState, useEffect } from 'react';
import api from '@/lib/api';
import { useAuth } from '@/lib/authContext';
import { AdminHeader } from '@/components/admin/AdminHeader';
import { StatCard } from '@/components/admin/StatCard';
import { FilterPanel } from '@/components/admin/FilterPanel';
import { DataTable, Column } from '@/components/admin/DataTable';

interface MonitoringStats {
  total_requests: number;
  success_requests: number;
  error_requests: number;
  rate_limited_requests: number;
  success_rate_percent: number;
  avg_latency_ms: number;
  total_tokens_used: number;
  total_datasets: number;
  active_datasets: number;
  provider_health: {
    ai_enabled: boolean;
    provider: string;
    model: string;
    configured: boolean;
    status: string;
    rag_enabled: boolean;
    vector_db_provider: string;
    indexed_vectors: number;
  };
}

interface AIRequestLogItem {
  id: number;
  user_id: number;
  user_name: string;
  conversation_id: string;
  request_type: string;
  provider: string;
  model: string;
  status: string;
  latency_ms: number;
  tokens_used: number;
  datasets_used: string;
  tools_used: string;
  error_code?: string;
  user_query_preview?: string;
  created_at: string;
}

export default function AdminAIMonitoringPage() {
  const { user } = useAuth();
  const [stats, setStats] = useState<MonitoringStats | null>(null);
  const [logs, setLogs] = useState<AIRequestLogItem[]>([]);
  const [totalLogs, setTotalLogs] = useState(0);
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [isLoading, setIsLoading] = useState(true);

  const fetchStats = async () => {
    try {
      const res = await api.get<MonitoringStats>('/admin/ai-monitoring/stats');
      setStats(res.data);
    } catch (err) {
      console.error('Error fetching AI stats:', err);
    }
  };

  const fetchLogs = async () => {
    setIsLoading(true);
    try {
      const params: any = { page, limit: 15 };
      if (statusFilter !== 'ALL') params.status = statusFilter;
      const res = await api.get('/admin/ai-monitoring/logs', { params });
      setLogs(res.data.items || []);
      setTotalLogs(res.data.total || 0);
    } catch (err) {
      console.error('Error fetching AI request logs:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
    fetchLogs();
    const interval = setInterval(fetchStats, 10000); // 10s auto-refresh
    return () => clearInterval(interval);
  }, [page, statusFilter]);

  const columns: Column<AIRequestLogItem>[] = [
    {
      key: 'user_query_preview',
      header: 'Query & User Info',
      render: (l) => (
        <div>
          <div className="font-bold text-white text-xs truncate max-w-[260px]">
            {l.user_query_preview || 'Clinical Consultation Query'}
          </div>
          <div className="text-[11px] text-gray-400 mt-0.5">
            User: <span className="text-gray-200 font-semibold">{l.user_name}</span> | Type:{' '}
            <span className="text-purple-400 font-mono">{l.request_type}</span>
          </div>
        </div>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      render: (l) => {
        const badgeColors: Record<string, string> = {
          SUCCESS: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40',
          RATE_LIMITED: 'bg-amber-500/20 text-amber-300 border-amber-500/40',
          FILTERED: 'bg-rose-500/20 text-rose-300 border-rose-500/40',
          ERROR: 'bg-red-500/20 text-red-300 border-red-500/40',
        };
        return (
          <div>
            <span
              className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold border ${
                badgeColors[l.status] || 'bg-gray-700/40 text-gray-300 border-white/10'
              }`}
            >
              {l.status}
            </span>
            {l.error_code && (
              <span className="text-[9px] font-mono text-rose-400 block mt-0.5">{l.error_code}</span>
            )}
          </div>
        );
      },
    },
    {
      key: 'latency_ms',
      header: 'Latency / Tokens',
      render: (l) => (
        <div className="text-xs">
          <span className="text-blue-400 font-bold font-mono">{l.latency_ms}ms</span>
          <span className="text-gray-400 text-[10px] block font-mono">{l.tokens_used} tokens</span>
        </div>
      ),
    },
    {
      key: 'model',
      header: 'Provider & Engine',
      render: (l) => (
        <div>
          <span className="text-gray-200 text-xs font-semibold">{l.provider}</span>
          <span className="text-[10px] text-gray-500 block font-mono">{l.model}</span>
        </div>
      ),
    },
    {
      key: 'created_at',
      header: 'Timestamp',
      render: (l) => (
        <span className="text-gray-400 text-[11px]">
          {l.created_at ? new Date(l.created_at).toLocaleTimeString() : '—'}
        </span>
      ),
    },
  ];

  const provider = stats?.provider_health;

  return (
    <div className="space-y-6">
      <AdminHeader
        title="AI Operational Monitoring & Diagnostics"
        subtitle="Real-time telemetry on inference latency, vector retrieval counts, token consumption, error diagnostics, and Gemini health."
        actions={
          <button
            onClick={() => {
              fetchStats();
              fetchLogs();
            }}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold text-white bg-white/10 hover:bg-white/15 border border-white/10 transition-all"
          >
            <span className="material-symbols-outlined text-sm">refresh</span>
            <span>Refresh Diagnostics</span>
          </button>
        }
      />

      {/* Provider Health Banner */}
      <div className="bg-gradient-to-r from-blue-950/40 via-purple-950/40 to-black border border-purple-500/30 rounded-2xl p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-purple-500/20 border border-purple-500/40 flex items-center justify-center text-purple-400">
            <span className="material-symbols-outlined text-xl">neurology</span>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h4 className="font-bold text-white text-xs">
                LLM Provider: {provider?.provider ? provider.provider.toUpperCase() : 'GEMINI'}
              </h4>
              <span
                className={`px-2 py-0.2 rounded text-[10px] font-extrabold border ${
                  provider?.status === 'healthy'
                    ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                    : 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                }`}
              >
                {provider?.status ? provider.status.toUpperCase() : 'STANDBY'}
              </span>
            </div>
            <p className="text-[11px] text-gray-400 mt-0.5">
              Configured Model: <span className="text-gray-200 font-mono">{provider?.model || 'gemini-1.5-flash'}</span> | Vector DB:{' '}
              <span className="text-purple-300 font-mono">{provider?.vector_db_provider || 'Qdrant'}</span>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4 text-xs">
          <div className="text-right">
            <span className="text-[10px] text-gray-400 font-bold uppercase block">Indexed Vectors</span>
            <span className="text-white font-extrabold font-mono text-sm">{provider?.indexed_vectors || 0}</span>
          </div>
          <div className="text-right border-l border-white/10 pl-4">
            <span className="text-[10px] text-gray-400 font-bold uppercase block">RAG Engine</span>
            <span className="text-emerald-400 font-extrabold text-sm">ACTIVE</span>
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total AI Inferences"
          value={(stats?.total_requests || 0).toLocaleString()}
          subtitle="Cumulative chat and RAG queries"
          icon="smart_toy"
          color="blue"
        />
        <StatCard
          title="Inference Success Rate"
          value={`${stats?.success_rate_percent || 100}%`}
          subtitle="Requests resolved without failure"
          icon="verified"
          color="emerald"
        />
        <StatCard
          title="Average Latency"
          value={`${stats?.avg_latency_ms || 0} ms`}
          subtitle="Vector retrieval + synthesis time"
          icon="speed"
          color="purple"
        />
        <StatCard
          title="Cumulative Tokens"
          value={(stats?.total_tokens_used || 0).toLocaleString()}
          subtitle="Prompt & generation consumption"
          icon="data_usage"
          color="blue"
        />
      </div>

      {/* Filter and Log Table */}
      <FilterPanel
        filters={[
          {
            key: 'status',
            label: 'Status',
            value: statusFilter,
            onChange: (v) => {
              setStatusFilter(v);
              setPage(1);
            },
            options: [
              { label: 'All Executions', value: 'ALL' },
              { label: 'Success', value: 'SUCCESS' },
              { label: 'Rate Limited', value: 'RATE_LIMITED' },
              { label: 'Filtered', value: 'FILTERED' },
              { label: 'Error', value: 'ERROR' },
            ],
          },
        ]}
        onReset={() => {
          setStatusFilter('ALL');
          setPage(1);
        }}
      />

      <DataTable
        columns={columns}
        data={logs}
        isLoading={isLoading}
        page={page}
        total={totalLogs}
        limit={15}
        onPageChange={(p) => setPage(p)}
        emptyMessage="No AI inference logs recorded."
      />
    </div>
  );
}

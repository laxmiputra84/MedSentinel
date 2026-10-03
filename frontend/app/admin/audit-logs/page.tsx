'use client';

import React, { useState, useEffect } from 'react';
import api from '@/lib/api';
import { useAuth } from '@/lib/authContext';
import { AdminHeader } from '@/components/admin/AdminHeader';
import { FilterPanel } from '@/components/admin/FilterPanel';
import { DataTable, Column } from '@/components/admin/DataTable';

interface AuditLogRecord {
  id: number;
  admin_name: string;
  admin_email: string;
  action: string;
  resource_type: string;
  resource_id?: string;
  old_value?: string;
  new_value?: string;
  ip_address?: string;
  created_at?: string;
}

export default function AdminAuditLogsPage() {
  const { user } = useAuth();
  const [logs, setLogs] = useState<AuditLogRecord[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [actionSearch, setActionSearch] = useState('');
  const [resourceFilter, setResourceFilter] = useState('ALL');
  const [isLoading, setIsLoading] = useState(true);

  // Detail Modal
  const [selectedLog, setSelectedLog] = useState<AuditLogRecord | null>(null);

  const fetchLogs = async () => {
    setIsLoading(true);
    try {
      const params: any = { page, limit: 15 };
      if (actionSearch.trim()) params.action = actionSearch.trim();
      if (resourceFilter !== 'ALL') params.resource_type = resourceFilter;

      const res = await api.get('/admin/audit-logs', { params });
      setLogs(res.data.items || []);
      setTotal(res.data.total || 0);
    } catch (err) {
      console.error('Error loading audit logs:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [page, resourceFilter]);

  useEffect(() => {
    const t = setTimeout(fetchLogs, 400);
    return () => clearTimeout(t);
  }, [actionSearch]);

  const columns: Column<AuditLogRecord>[] = [
    {
      key: 'action',
      header: 'Security Action & Event',
      render: (l) => (
        <div>
          <span className="font-extrabold text-white text-xs font-mono px-2 py-0.5 rounded bg-white/5 border border-white/10">
            {l.action}
          </span>
          <div className="text-[11px] text-gray-400 mt-1">
            Target: <span className="text-gray-200 font-semibold">{l.resource_type}</span>{' '}
            {l.resource_id ? `(#${l.resource_id})` : ''}
          </div>
        </div>
      ),
    },
    {
      key: 'admin_name',
      header: 'Performed By',
      render: (l) => (
        <div>
          <div className="font-semibold text-gray-200 text-xs">{l.admin_name}</div>
          <div className="text-[10px] text-gray-400">{l.admin_email}</div>
        </div>
      ),
    },
    {
      key: 'ip_address',
      header: 'Origin IP',
      render: (l) => (
        <span className="text-gray-400 font-mono text-[11px]">{l.ip_address || '127.0.0.1'}</span>
      ),
    },
    {
      key: 'created_at',
      header: 'Timestamp (UTC)',
      render: (l) => (
        <span className="text-gray-400 text-[11px]">
          {l.created_at ? new Date(l.created_at).toLocaleString() : '—'}
        </span>
      ),
    },
    {
      key: 'actions',
      header: 'Inspection',
      align: 'right',
      render: (l) => (
        <button
          onClick={() => setSelectedLog(l)}
          className="px-2.5 py-1 rounded-lg bg-white/5 hover:bg-white/10 text-gray-300 hover:text-white border border-white/10 text-xs font-semibold flex items-center gap-1"
        >
          <span className="material-symbols-outlined text-sm">data_object</span>
          <span>Payload</span>
        </button>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <AdminHeader
        title="Administrative Security & Audit Log"
        subtitle="Tamper-evident historical event record of all user permission modifications, claim adjudications, document verifications, and policy updates."
      />

      <FilterPanel
        searchQuery={actionSearch}
        onSearchChange={(q) => {
          setActionSearch(q);
          setPage(1);
        }}
        searchPlaceholder="Filter by action code (e.g. USER_UPDATED, CLAIM_STATUS)..."
        filters={[
          {
            key: 'resource',
            label: 'Resource',
            value: resourceFilter,
            onChange: (v) => {
              setResourceFilter(v);
              setPage(1);
            },
            options: [
              { label: 'All Resources', value: 'ALL' },
              { label: 'User Record', value: 'User' },
              { label: 'Insurance Claim', value: 'InsuranceClaim' },
              { label: 'Hospital Facility', value: 'Hospital' },
              { label: 'Medical Document', value: 'Document' },
              { label: 'Appointment', value: 'Appointment' },
              { label: 'Government Scheme', value: 'Scheme' },
              { label: 'Insurance Policy', value: 'Insurance' },
            ],
          },
        ]}
        onReset={() => {
          setActionSearch('');
          setResourceFilter('ALL');
          setPage(1);
        }}
      />

      <DataTable
        columns={columns}
        data={logs}
        isLoading={isLoading}
        page={page}
        total={total}
        limit={15}
        onPageChange={(p) => setPage(p)}
        emptyMessage="No audit logs match the selected parameters."
      />

      {/* Payload Modal */}
      {selectedLog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="fixed inset-0 bg-black/80 backdrop-blur-sm" onClick={() => setSelectedLog(null)} />
          <div className="relative bg-gray-900 border border-white/15 rounded-2xl max-w-lg w-full p-6 shadow-2xl z-10 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-white/10">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-purple-400">history</span>
                <h3 className="text-base font-bold text-white font-['Manrope']">
                  Audit Entry: {selectedLog.action}
                </h3>
              </div>
              <button onClick={() => setSelectedLog(null)} className="text-gray-400 hover:text-white">
                <span className="material-symbols-outlined text-lg">close</span>
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div className="bg-black/40 border border-white/10 rounded-xl p-3 grid grid-cols-2 gap-2 text-gray-300">
                <div>
                  <span className="text-[10px] text-gray-400 font-bold uppercase block">Administrator</span>
                  <span className="text-white font-semibold">{selectedLog.admin_name}</span>
                </div>
                <div>
                  <span className="text-[10px] text-gray-400 font-bold uppercase block">Resource Type</span>
                  <span className="text-white font-semibold">{selectedLog.resource_type} (#{selectedLog.resource_id})</span>
                </div>
              </div>

              {selectedLog.old_value && (
                <div>
                  <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider block mb-1">
                    Previous State (Before Modification)
                  </span>
                  <pre className="bg-black/60 border border-white/10 rounded-xl p-3 text-[11px] font-mono text-gray-300 overflow-x-auto">
                    {typeof selectedLog.old_value === 'string'
                      ? selectedLog.old_value
                      : JSON.stringify(selectedLog.old_value, null, 2)}
                  </pre>
                </div>
              )}

              {selectedLog.new_value && (
                <div>
                  <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider block mb-1">
                    Committed State (New Value)
                  </span>
                  <pre className="bg-black/60 border border-white/10 rounded-xl p-3 text-[11px] font-mono text-emerald-400 overflow-x-auto">
                    {typeof selectedLog.new_value === 'string'
                      ? selectedLog.new_value
                      : JSON.stringify(selectedLog.new_value, null, 2)}
                  </pre>
                </div>
              )}
            </div>

            <div className="pt-3 border-t border-white/10 flex justify-end">
              <button
                onClick={() => setSelectedLog(null)}
                className="px-4 py-2 rounded-xl bg-white/10 hover:bg-white/20 text-white font-semibold text-xs transition-all"
              >
                Close Audit Dossier
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

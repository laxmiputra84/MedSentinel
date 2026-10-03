'use client';

import React, { useState, useEffect } from 'react';
import api from '@/lib/api';
import { useAuth } from '@/lib/authContext';
import { AdminHeader } from '@/components/admin/AdminHeader';
import { FilterPanel } from '@/components/admin/FilterPanel';
import { DataTable, Column } from '@/components/admin/DataTable';

interface AppointmentRecord {
  id: number;
  patient_name: string;
  phone: string;
  email: string;
  hospital_name: string;
  department: string;
  preferred_date: string;
  preferred_time: string;
  status: string;
  reason?: string;
  created_at?: string;
}

export default function AdminAppointmentsPage() {
  const { user } = useAuth();
  const [appointments, setAppointments] = useState<AppointmentRecord[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [isLoading, setIsLoading] = useState(true);

  // Status Change Modal State
  const [selectedAppt, setSelectedAppt] = useState<AppointmentRecord | null>(null);
  const [newStatus, setNewStatus] = useState('CONFIRMED');
  const [statusNotes, setStatusNotes] = useState('');
  const [isUpdating, setIsUpdating] = useState(false);
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  const fetchAppointments = async () => {
    setIsLoading(true);
    try {
      const params: any = { page, limit: 12 };
      if (statusFilter !== 'ALL') params.status = statusFilter;
      const res = await api.get('/admin/appointments', { params });
      setAppointments(res.data.items || []);
      setTotal(res.data.total || 0);
    } catch (err: any) {
      console.error('Error fetching appointments:', err);
      setFeedback({ type: 'error', message: err.response?.data?.detail || 'Failed to load appointments.' });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAppointments();
  }, [page, statusFilter]);

  const openStatusModal = (a: AppointmentRecord) => {
    setSelectedAppt(a);
    setNewStatus(a.status);
    setStatusNotes('');
  };

  const handleUpdateStatus = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedAppt) return;
    setIsUpdating(true);
    setFeedback(null);
    try {
      await api.patch(`/admin/appointments/${selectedAppt.id}/status`, {
        status: newStatus,
        notes: statusNotes || undefined,
      });
      setFeedback({
        type: 'success',
        message: `Appointment #${selectedAppt.id} status changed to ${newStatus}.`,
      });
      setSelectedAppt(null);
      fetchAppointments();
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.response?.data?.detail || 'Update failed.' });
    } finally {
      setIsUpdating(false);
    }
  };

  const getStatusBadge = (st: string) => {
    const map: Record<string, string> = {
      CONFIRMED: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40',
      PENDING: 'bg-amber-500/20 text-amber-300 border-amber-500/40',
      COMPLETED: 'bg-blue-500/20 text-blue-300 border-blue-500/40',
      CANCELLED: 'bg-rose-500/20 text-rose-300 border-rose-500/40',
    };
    return (
      <span
        className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold border ${
          map[st] || 'bg-gray-700/40 text-gray-300 border-white/10'
        }`}
      >
        {st}
      </span>
    );
  };

  const columns: Column<AppointmentRecord>[] = [
    {
      key: 'patient_name',
      header: 'Patient & Contact',
      render: (a) => (
        <div>
          <div className="font-bold text-white text-xs">{a.patient_name}</div>
          <div className="text-[11px] text-gray-400 mt-0.5">{a.phone || a.email}</div>
        </div>
      ),
    },
    {
      key: 'hospital_name',
      header: 'Hospital & Department',
      render: (a) => (
        <div>
          <div className="text-gray-200 text-xs font-semibold">{a.hospital_name}</div>
          <div className="text-[11px] text-blue-400 font-medium">{a.department}</div>
        </div>
      ),
    },
    {
      key: 'preferred_date',
      header: 'Schedule Slot',
      render: (a) => (
        <div>
          <div className="text-white text-xs font-bold">{a.preferred_date}</div>
          <div className="text-[11px] text-gray-400">{a.preferred_time}</div>
        </div>
      ),
    },
    {
      key: 'status',
      header: 'Consultation Status',
      render: (a) => getStatusBadge(a.status),
    },
    {
      key: 'reason',
      header: 'Chief Complaint',
      render: (a) => (
        <span className="text-gray-400 text-[11px] truncate max-w-[170px] block">
          {a.reason || 'General Consultation'}
        </span>
      ),
    },
    {
      key: 'actions',
      header: 'Actions',
      align: 'right',
      render: (a) => (
        <button
          onClick={() => openStatusModal(a)}
          className="px-2.5 py-1 rounded-lg bg-white/5 hover:bg-white/10 text-gray-300 hover:text-white border border-white/10 text-xs font-semibold flex items-center gap-1"
        >
          <span className="material-symbols-outlined text-sm">tune</span>
          <span>Manage</span>
        </button>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <AdminHeader
        title="Patient Consultations & Triage"
        subtitle="Review clinical appointment queues, adjust consultation statuses, schedule triage slots, and manage patient notifications."
      />

      {feedback && (
        <div
          className={`p-4 rounded-2xl border text-xs flex items-center justify-between gap-3 ${
            feedback.type === 'success'
              ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
              : 'bg-red-500/10 border-red-500/30 text-red-300'
          }`}
        >
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-base">
              {feedback.type === 'success' ? 'check_circle' : 'error'}
            </span>
            <span>{feedback.message}</span>
          </div>
          <button onClick={() => setFeedback(null)} className="text-gray-400 hover:text-white">
            <span className="material-symbols-outlined text-sm">close</span>
          </button>
        </div>
      )}

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
              { label: 'All Statuses', value: 'ALL' },
              { label: 'Confirmed', value: 'CONFIRMED' },
              { label: 'Pending', value: 'PENDING' },
              { label: 'Completed', value: 'COMPLETED' },
              { label: 'Cancelled', value: 'CANCELLED' },
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
        data={appointments}
        isLoading={isLoading}
        page={page}
        total={total}
        limit={12}
        onPageChange={(p) => setPage(p)}
        emptyMessage="No patient consultations found."
      />

      {/* Appointment Status Modal */}
      {selectedAppt && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="fixed inset-0 bg-black/80 backdrop-blur-sm" onClick={() => setSelectedAppt(null)} />
          <div className="relative bg-gray-900 border border-white/15 rounded-2xl max-w-md w-full p-6 shadow-2xl z-10 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-white/10">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-blue-400">event</span>
                <h3 className="text-base font-bold text-white font-['Manrope']">
                  Manage Appointment #{selectedAppt.id}
                </h3>
              </div>
              <button onClick={() => setSelectedAppt(null)} className="text-gray-400 hover:text-white">
                <span className="material-symbols-outlined text-lg">close</span>
              </button>
            </div>

            <form onSubmit={handleUpdateStatus} className="space-y-4 text-xs">
              <div className="bg-black/40 border border-white/10 rounded-xl p-3 space-y-1">
                <div className="text-white font-bold">{selectedAppt.patient_name}</div>
                <div className="text-gray-400 text-[11px]">
                  {selectedAppt.department} @ {selectedAppt.hospital_name}
                </div>
                <div className="text-blue-400 text-[11px] font-semibold">
                  {selectedAppt.preferred_date} at {selectedAppt.preferred_time}
                </div>
              </div>

              <div>
                <label className="block text-gray-300 font-semibold mb-1">Update Status</label>
                <select
                  value={newStatus}
                  onChange={(e) => setNewStatus(e.target.value)}
                  className="w-full bg-black/60 border border-white/15 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                >
                  <option value="CONFIRMED" className="bg-gray-900">CONFIRMED (Scheduled & Physician Assigned)</option>
                  <option value="COMPLETED" className="bg-gray-900">COMPLETED (Consultation Attended)</option>
                  <option value="CANCELLED" className="bg-gray-900">CANCELLED (Patient / Clinic Cancelled)</option>
                  <option value="PENDING" className="bg-gray-900">PENDING (Awaiting Confirmation)</option>
                </select>
              </div>

              <div>
                <label className="block text-gray-300 font-semibold mb-1">Administrative / Clinical Notes</label>
                <textarea
                  rows={2}
                  placeholder="e.g. Patient advised to carry recent blood work results."
                  value={statusNotes}
                  onChange={(e) => setStatusNotes(e.target.value)}
                  className="w-full bg-black/60 border border-white/15 rounded-xl p-2.5 text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              <div className="pt-3 border-t border-white/10 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setSelectedAppt(null)}
                  className="px-3 py-1.5 rounded-xl border border-white/10 text-gray-300 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isUpdating}
                  className="px-4 py-1.5 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 text-white font-bold flex items-center gap-1 shadow"
                >
                  {isUpdating && <span className="material-symbols-outlined text-sm animate-spin">progress_activity</span>}
                  <span>Save Status</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

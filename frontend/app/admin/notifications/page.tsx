'use client';

import React, { useState, useEffect } from 'react';
import api from '@/lib/api';
import { useAuth } from '@/lib/authContext';
import { AdminHeader } from '@/components/admin/AdminHeader';
import { DataTable, Column } from '@/components/admin/DataTable';

interface NotificationLog {
  id: number;
  user_id: number;
  recipient_name: string;
  recipient_email: string;
  title: string;
  message: string;
  type: string;
  is_read: boolean;
  created_at?: string;
}

export default function AdminNotificationsPage() {
  const { user } = useAuth();
  const [notifications, setNotifications] = useState<NotificationLog[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [isLoading, setIsLoading] = useState(true);

  // Broadcast Modal State
  const [modalOpen, setModalOpen] = useState(false);
  const [broadcastForm, setBroadcastForm] = useState({
    title: '',
    message: '',
    type: 'alert',
    target_user_id: '' as string | number,
  });
  const [isBroadcasting, setIsBroadcasting] = useState(false);
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  const fetchNotifications = async () => {
    setIsLoading(true);
    try {
      const res = await api.get('/admin/notifications', { params: { page, limit: 12 } });
      setNotifications(res.data.items || []);
      setTotal(res.data.total || 0);
    } catch (err: any) {
      console.error('Error loading notifications:', err);
      setFeedback({ type: 'error', message: err.response?.data?.detail || 'Failed to load notifications.' });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchNotifications();
  }, [page]);

  const handleBroadcast = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsBroadcasting(true);
    setFeedback(null);
    try {
      const payload: any = {
        title: broadcastForm.title,
        message: broadcastForm.message,
        type: broadcastForm.type,
      };
      if (broadcastForm.target_user_id) {
        payload.target_user_id = parseInt(String(broadcastForm.target_user_id));
      }

      const res = await api.post('/admin/notifications/broadcast', payload);
      setFeedback({ type: 'success', message: res.data.message || 'Notification broadcast successfully.' });
      setModalOpen(false);
      setBroadcastForm({ title: '', message: '', type: 'alert', target_user_id: '' });
      fetchNotifications();
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.response?.data?.detail || 'Broadcast failed.' });
    } finally {
      setIsBroadcasting(false);
    }
  };

  const columns: Column<NotificationLog>[] = [
    {
      key: 'title',
      header: 'Alert & Title',
      render: (n) => (
        <div>
          <div className="font-bold text-white text-xs flex items-center gap-1.5">
            <span className="material-symbols-outlined text-sm text-purple-400">notifications</span>
            <span>{n.title}</span>
          </div>
          <p className="text-[11px] text-gray-300 mt-0.5 truncate max-w-[280px]">{n.message}</p>
        </div>
      ),
    },
    {
      key: 'recipient_name',
      header: 'Recipient',
      render: (n) => (
        <div>
          <div className="text-gray-200 text-xs font-semibold">{n.recipient_name}</div>
          <div className="text-[10px] text-gray-400">{n.recipient_email}</div>
        </div>
      ),
    },
    {
      key: 'type',
      header: 'Category',
      render: (n) => (
        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-white/5 border border-white/10 text-gray-300 uppercase">
          {n.type}
        </span>
      ),
    },
    {
      key: 'is_read',
      header: 'Read Status',
      render: (n) => (
        <span
          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold border ${
            n.is_read
              ? 'bg-white/5 text-gray-400 border-white/10'
              : 'bg-blue-500/20 text-blue-300 border-blue-500/30'
          }`}
        >
          {!n.is_read && <span className="w-1.5 h-1.5 rounded-full bg-blue-400" />}
          {n.is_read ? 'Read' : 'Unread'}
        </span>
      ),
    },
    {
      key: 'created_at',
      header: 'Delivered',
      render: (n) => (
        <span className="text-gray-400 text-[11px]">
          {n.created_at ? new Date(n.created_at).toLocaleString() : '—'}
        </span>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <AdminHeader
        title="Platform Notifications Center"
        subtitle="Broadcast system alerts, insurance settlement updates, document requirement reminders, and health advisory broadcasts."
        actions={
          <button
            onClick={() => setModalOpen(true)}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-semibold text-white bg-gradient-to-r from-blue-600 to-purple-600 hover:shadow-lg hover:shadow-blue-500/20 transition-all"
          >
            <span className="material-symbols-outlined text-sm">campaign</span>
            <span>Broadcast Notification</span>
          </button>
        }
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

      <DataTable
        columns={columns}
        data={notifications}
        isLoading={isLoading}
        page={page}
        total={total}
        limit={12}
        onPageChange={(p) => setPage(p)}
        emptyMessage="No notification logs available."
      />

      {/* Broadcast Modal */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="fixed inset-0 bg-black/80 backdrop-blur-sm" onClick={() => setModalOpen(false)} />
          <div className="relative bg-gray-900 border border-white/15 rounded-2xl max-w-lg w-full p-6 shadow-2xl z-10 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-white/10">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-purple-400">campaign</span>
                <h3 className="text-base font-bold text-white font-['Manrope']">Dispatch Platform Alert</h3>
              </div>
              <button onClick={() => setModalOpen(false)} className="text-gray-400 hover:text-white">
                <span className="material-symbols-outlined text-lg">close</span>
              </button>
            </div>

            <form onSubmit={handleBroadcast} className="space-y-4 text-xs">
              <div>
                <label className="block text-gray-300 font-semibold mb-1">Notification Title *</label>
                <input
                  type="text"
                  required
                  value={broadcastForm.title}
                  onChange={(e) => setBroadcastForm({ ...broadcastForm, title: e.target.value })}
                  placeholder="e.g. System Maintenance Notice / Scheme Eligibility Update"
                  className="w-full bg-black/40 border border-white/10 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-gray-300 font-semibold mb-1">Notification Message / Body *</label>
                <textarea
                  required
                  rows={3}
                  value={broadcastForm.message}
                  onChange={(e) => setBroadcastForm({ ...broadcastForm, message: e.target.value })}
                  placeholder="Type the message content that will appear in user notification bells..."
                  className="w-full bg-black/40 border border-white/10 rounded-xl p-2.5 text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-gray-300 font-semibold mb-1">Alert Category</label>
                  <select
                    value={broadcastForm.type}
                    onChange={(e) => setBroadcastForm({ ...broadcastForm, type: e.target.value })}
                    className="w-full bg-black/40 border border-white/10 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                  >
                    <option value="alert" className="bg-gray-900">Alert (Priority)</option>
                    <option value="info" className="bg-gray-900">Informational</option>
                    <option value="claim" className="bg-gray-900">Insurance Claim</option>
                    <option value="appointment" className="bg-gray-900">Appointment</option>
                  </select>
                </div>

                <div>
                  <label className="block text-gray-300 font-semibold mb-1">Target User ID (Leave blank for all)</label>
                  <input
                    type="number"
                    value={broadcastForm.target_user_id}
                    onChange={(e) => setBroadcastForm({ ...broadcastForm, target_user_id: e.target.value })}
                    placeholder="All Active Users"
                    className="w-full bg-black/40 border border-white/10 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
              </div>

              <div className="pt-3 border-t border-white/10 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setModalOpen(false)}
                  className="px-3 py-1.5 rounded-xl border border-white/10 text-gray-300 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isBroadcasting}
                  className="px-4 py-1.5 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 text-white font-bold flex items-center gap-1 shadow"
                >
                  {isBroadcasting && <span className="material-symbols-outlined text-sm animate-spin">progress_activity</span>}
                  <span>Dispatch Broadcast</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

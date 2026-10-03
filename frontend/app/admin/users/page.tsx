'use client';

import React, { useState, useEffect } from 'react';
import api from '@/lib/api';
import { useAuth } from '@/lib/authContext';
import { AdminHeader } from '@/components/admin/AdminHeader';
import { FilterPanel } from '@/components/admin/FilterPanel';
import { DataTable, Column } from '@/components/admin/DataTable';
import { ConfirmActionModal } from '@/components/admin/ConfirmActionModal';

interface UserRecord {
  id: number;
  name: string;
  email: string;
  phone?: string;
  role: string;
  is_active: boolean;
  hospital_id?: number;
  insurance_id?: number;
  blood_group?: string;
  created_at?: string;
}

export default function AdminUsersPage() {
  const { user: currentAdmin } = useAuth();
  const [users, setUsers] = useState<UserRecord[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('ALL');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [isLoading, setIsLoading] = useState(true);

  // Edit / Details Modal State
  const [selectedUser, setSelectedUser] = useState<UserRecord | null>(null);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [editForm, setEditForm] = useState({
    name: '',
    phone: '',
    role: 'USER',
    is_active: true,
    blood_group: '',
  });
  const [isSaving, setIsSaving] = useState(false);
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  // Status Toggle Modal
  const [statusToggleTarget, setStatusToggleTarget] = useState<UserRecord | null>(null);

  const fetchUsers = async () => {
    setIsLoading(true);
    try {
      const params: any = { page, limit: 12 };
      if (search.trim()) params.search = search.trim();
      if (roleFilter !== 'ALL') params.role = roleFilter;
      if (statusFilter !== 'ALL') params.is_active = statusFilter === 'ACTIVE';

      const res = await api.get('/admin/users', { params });
      setUsers(res.data.items || []);
      setTotal(res.data.total || 0);
    } catch (err: any) {
      console.error('Error fetching users:', err);
      setFeedback({ type: 'error', message: err.response?.data?.detail || 'Failed to load users.' });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, [page, roleFilter, statusFilter]);

  const handleSearchSubmit = (q: string) => {
    setSearch(q);
    setPage(1);
  };

  useEffect(() => {
    const delayDebounce = setTimeout(() => {
      fetchUsers();
    }, 400);
    return () => clearTimeout(delayDebounce);
  }, [search]);

  const openEditModal = (u: UserRecord) => {
    setSelectedUser(u);
    setEditForm({
      name: u.name || '',
      phone: u.phone || '',
      role: u.role || 'USER',
      is_active: u.is_active,
      blood_group: u.blood_group || '',
    });
    setIsEditOpen(true);
  };

  const handleSaveUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedUser) return;
    setIsSaving(true);
    setFeedback(null);
    try {
      await api.put(`/admin/users/${selectedUser.id}`, editForm);
      setFeedback({ type: 'success', message: 'User updated successfully.' });
      setIsEditOpen(false);
      fetchUsers();
    } catch (err: any) {
      setFeedback({
        type: 'error',
        message: err.response?.data?.detail || 'Failed to update user.',
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleToggleStatusConfirm = async () => {
    if (!statusToggleTarget) return;
    setIsSaving(true);
    try {
      await api.patch(`/admin/users/${statusToggleTarget.id}/toggle-status`);
      setFeedback({
        type: 'success',
        message: `User ${statusToggleTarget.name} account is now ${statusToggleTarget.is_active ? 'deactivated' : 'activated'}.`,
      });
      setStatusToggleTarget(null);
      fetchUsers();
    } catch (err: any) {
      setFeedback({
        type: 'error',
        message: err.response?.data?.detail || 'Action rejected.',
      });
    } finally {
      setIsSaving(false);
    }
  };

  const columns: Column<UserRecord>[] = [
    {
      key: 'name',
      header: 'User Profile',
      render: (u) => (
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center font-bold text-white text-xs flex-shrink-0">
            {u.name ? u.name.charAt(0).toUpperCase() : 'U'}
          </div>
          <div>
            <div className="font-bold text-white truncate max-w-[180px]">{u.name}</div>
            <div className="text-[11px] text-gray-400 truncate max-w-[180px]">{u.email}</div>
          </div>
        </div>
      ),
    },
    {
      key: 'role',
      header: 'Role',
      render: (u) => {
        const badgeColors: Record<string, string> = {
          SUPER_ADMIN: 'bg-purple-500/20 text-purple-300 border-purple-500/40',
          HOSPITAL_ADMIN: 'bg-blue-500/20 text-blue-300 border-blue-500/40',
          INSURANCE_ADMIN: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40',
          USER: 'bg-gray-700/40 text-gray-300 border-white/10',
        };
        return (
          <span
            className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold border ${
              badgeColors[u.role] || badgeColors.USER
            }`}
          >
            {u.role.replace('_', ' ')}
          </span>
        );
      },
    },
    {
      key: 'phone',
      header: 'Phone / Contact',
      render: (u) => <span className="text-gray-300 text-xs">{u.phone || '—'}</span>,
    },
    {
      key: 'is_active',
      header: 'Account Status',
      render: (u) => (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${
            u.is_active
              ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
              : 'bg-red-500/20 text-red-300 border-red-500/30'
          }`}
        >
          <span className={`w-1.5 h-1.5 rounded-full ${u.is_active ? 'bg-emerald-400' : 'bg-red-400'}`} />
          {u.is_active ? 'Active' : 'Deactivated'}
        </span>
      ),
    },
    {
      key: 'created_at',
      header: 'Registered',
      render: (u) => (
        <span className="text-gray-400 text-[11px]">
          {u.created_at ? new Date(u.created_at).toLocaleDateString() : '—'}
        </span>
      ),
    },
    {
      key: 'actions',
      header: 'Actions',
      align: 'right',
      render: (u) => {
        const isSelf = currentAdmin?.id === u.id;
        return (
          <div className="flex items-center justify-end gap-2">
            <button
              onClick={() => openEditModal(u)}
              title="Edit Profile & Role"
              className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-gray-300 hover:text-white border border-white/10 transition-all text-xs"
            >
              <span className="material-symbols-outlined text-sm">edit</span>
            </button>
            <button
              onClick={() => setStatusToggleTarget(u)}
              disabled={isSelf}
              title={isSelf ? 'Cannot deactivate self' : u.is_active ? 'Deactivate User' : 'Reactivate User'}
              className={`p-1.5 rounded-lg border transition-all text-xs ${
                isSelf
                  ? 'opacity-30 cursor-not-allowed border-white/5'
                  : u.is_active
                  ? 'bg-red-500/10 hover:bg-red-500/20 text-red-400 border-red-500/30'
                  : 'bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
              }`}
            >
              <span className="material-symbols-outlined text-sm">
                {u.is_active ? 'block' : 'check_circle'}
              </span>
            </button>
          </div>
        );
      },
    },
  ];

  return (
    <div className="space-y-6">
      <AdminHeader
        title="User & RBAC Directory"
        subtitle="Manage platform users, assign organizational roles, and enforce security policies with automated audit logging."
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
        searchQuery={search}
        onSearchChange={handleSearchSubmit}
        searchPlaceholder="Search by name, email address, or phone..."
        filters={[
          {
            key: 'role',
            label: 'Role',
            value: roleFilter,
            onChange: (v) => {
              setRoleFilter(v);
              setPage(1);
            },
            options: [
              { label: 'All Roles', value: 'ALL' },
              { label: 'Patient (USER)', value: 'USER' },
              { label: 'Hospital Admin', value: 'HOSPITAL_ADMIN' },
              { label: 'Insurance Admin', value: 'INSURANCE_ADMIN' },
              { label: 'Super Admin', value: 'SUPER_ADMIN' },
            ],
          },
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
              { label: 'Active Only', value: 'ACTIVE' },
              { label: 'Deactivated Only', value: 'INACTIVE' },
            ],
          },
        ]}
        onReset={() => {
          setSearch('');
          setRoleFilter('ALL');
          setStatusFilter('ALL');
          setPage(1);
        }}
      />

      <DataTable
        columns={columns}
        data={users}
        isLoading={isLoading}
        page={page}
        total={total}
        limit={12}
        onPageChange={(p) => setPage(p)}
        emptyMessage="No users found matching the selected criteria."
      />

      {/* Edit User Modal */}
      {isEditOpen && selectedUser && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="fixed inset-0 bg-black/80 backdrop-blur-sm" onClick={() => setIsEditOpen(false)} />
          <div className="relative bg-gray-900 border border-white/15 rounded-2xl max-w-lg w-full p-6 shadow-2xl z-10 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-white/10">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-blue-400">manage_accounts</span>
                <h3 className="text-base font-bold text-white font-['Manrope']">Edit User: {selectedUser.email}</h3>
              </div>
              <button onClick={() => setIsEditOpen(false)} className="text-gray-400 hover:text-white">
                <span className="material-symbols-outlined text-lg">close</span>
              </button>
            </div>

            <form onSubmit={handleSaveUser} className="space-y-4 text-xs">
              <div>
                <label className="block text-gray-300 font-semibold mb-1">Full Name</label>
                <input
                  type="text"
                  required
                  value={editForm.name}
                  onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                  className="w-full bg-black/40 border border-white/10 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-gray-300 font-semibold mb-1">Phone Number</label>
                <input
                  type="text"
                  value={editForm.phone}
                  onChange={(e) => setEditForm({ ...editForm, phone: e.target.value })}
                  className="w-full bg-black/40 border border-white/10 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-gray-300 font-semibold mb-1">Assigned Role</label>
                  <select
                    value={editForm.role}
                    disabled={currentAdmin?.id === selectedUser.id}
                    onChange={(e) => setEditForm({ ...editForm, role: e.target.value })}
                    className="w-full bg-black/40 border border-white/10 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                  >
                    <option value="USER" className="bg-gray-900">Patient (USER)</option>
                    <option value="HOSPITAL_ADMIN" className="bg-gray-900">Hospital Admin</option>
                    <option value="INSURANCE_ADMIN" className="bg-gray-900">Insurance Admin</option>
                    <option value="SUPER_ADMIN" className="bg-gray-900">Super Admin</option>
                  </select>
                  {currentAdmin?.id === selectedUser.id && (
                    <p className="text-[10px] text-amber-400 mt-1">Super admin self-role locked.</p>
                  )}
                </div>

                <div>
                  <label className="block text-gray-300 font-semibold mb-1">Blood Group</label>
                  <input
                    type="text"
                    placeholder="e.g. O+, A-, B+"
                    value={editForm.blood_group}
                    onChange={(e) => setEditForm({ ...editForm, blood_group: e.target.value })}
                    className="w-full bg-black/40 border border-white/10 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
              </div>

              <div className="pt-3 border-t border-white/10 flex items-center justify-between">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    disabled={currentAdmin?.id === selectedUser.id}
                    checked={editForm.is_active}
                    onChange={(e) => setEditForm({ ...editForm, is_active: e.target.checked })}
                    className="rounded bg-black/40 border-white/20 text-blue-600 focus:ring-0"
                  />
                  <span className="text-gray-300 font-semibold">Active Account</span>
                </label>

                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setIsEditOpen(false)}
                    className="px-3 py-1.5 rounded-xl border border-white/10 text-gray-300 hover:text-white"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isSaving}
                    className="px-4 py-1.5 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 text-white font-semibold flex items-center gap-1 shadow"
                  >
                    {isSaving && <span className="material-symbols-outlined text-sm animate-spin">progress_activity</span>}
                    <span>Save Changes</span>
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Confirm Status Toggle Modal */}
      <ConfirmActionModal
        isOpen={!!statusToggleTarget}
        onClose={() => setStatusToggleTarget(null)}
        onConfirm={handleToggleStatusConfirm}
        isLoading={isSaving}
        isDestructive={statusToggleTarget?.is_active}
        title={statusToggleTarget?.is_active ? 'Deactivate User Account' : 'Reactivate User Account'}
        description={`Are you sure you want to ${statusToggleTarget?.is_active ? 'deactivate' : 'reactivate'} the account for ${statusToggleTarget?.name} (${statusToggleTarget?.email})?`}
        confirmText={statusToggleTarget?.is_active ? 'Deactivate User' : 'Reactivate User'}
      />
    </div>
  );
}

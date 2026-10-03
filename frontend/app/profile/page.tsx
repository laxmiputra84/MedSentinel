'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useAuth } from '@/lib/authContext';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { Hospital, UserInsurance, InsuranceClaim, Appointment, UserDocument, Notification } from '@/lib/types';
import { HospitalCard } from '@/components/HospitalCard';
import api from '@/lib/api';

export default function ProfilePage() {
  return (
    <ProtectedRoute>
      <ProfileDashboardContent />
    </ProtectedRoute>
  );
}

function ProfileDashboardContent() {
  const { user, logout, updateUser } = useAuth();

  const [activeTab, setActiveTab] = useState<'saved' | 'insurance' | 'claims' | 'appointments' | 'vault' | 'notifications'>('saved');

  // Dashboard Data
  const [savedHospitals, setSavedHospitals] = useState<Hospital[]>([]);
  const [userInsurances, setUserInsurances] = useState<UserInsurance[]>([]);
  const [userClaims, setUserClaims] = useState<InsuranceClaim[]>([]);
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [documents, setDocuments] = useState<UserDocument[]>([]);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);

  // Edit Profile Modal
  const [showEditModal, setShowEditModal] = useState(false);
  const [editName, setEditName] = useState(user?.name || '');
  const [editPhone, setEditPhone] = useState(user?.phone || '');
  const [editBloodGroup, setEditBloodGroup] = useState(user?.blood_group || 'O+');
  const [editAllergies, setEditAllergies] = useState(user?.allergies || '');
  const [editEmergency, setEditEmergency] = useState(user?.emergency_contact || '');
  const [savingProfile, setSavingProfile] = useState(false);

  // Reschedule Modal
  const [reschedulingAppt, setReschedulingAppt] = useState<Appointment | null>(null);
  const [newDate, setNewDate] = useState('');
  const [newTime, setNewTime] = useState('10:00 AM');
  const [rescheduling, setRescheduling] = useState(false);

  const fetchProfileData = async () => {
    try {
      const [hospRes, insRes, claimsRes, apptRes, docsRes, notifRes] = await Promise.all([
        api.get<Hospital[]>('/saved-items'),
        api.get<UserInsurance[]>('/user-insurances'),
        api.get<InsuranceClaim[]>('/insurance-claims'),
        api.get<Appointment[]>('/appointments'),
        api.get<UserDocument[]>('/documents'),
        api.get<Notification[]>('/notifications'),
      ]);
      setSavedHospitals(hospRes.data);
      setUserInsurances(insRes.data);
      setUserClaims(claimsRes.data);
      setAppointments(apptRes.data);
      setDocuments(docsRes.data);
      setNotifications(notifRes.data);
    } catch (err) {
      console.error('Error loading profile dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProfileData();
    if (user) {
      setEditName(user.name);
      setEditPhone(user.phone || '');
      setEditBloodGroup(user.blood_group || 'O+');
      setEditAllergies(user.allergies || '');
      setEditEmergency(user.emergency_contact || '');
    }
  }, [user]);

  const handleProfileUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingProfile(true);
    try {
      const res = await api.put('/users/me', {
        name: editName,
        phone: editPhone,
        blood_group: editBloodGroup,
        allergies: editAllergies,
        emergency_contact: editEmergency,
      });
      updateUser(res.data);
      setShowEditModal(false);
    } catch (err) {
      alert('Failed to update profile.');
    } finally {
      setSavingProfile(false);
    }
  };

  const handleRemoveSaved = async (hospitalId: number) => {
    try {
      await api.delete(`/saved-items/${hospitalId}`);
      setSavedHospitals(savedHospitals.filter((h) => h.id !== hospitalId));
    } catch (err) {
      console.error('Failed to remove saved hospital:', err);
    }
  };

  const handleCancelAppointment = async (appointmentId: number) => {
    if (!confirm('Are you sure you want to cancel this appointment?')) return;
    try {
      const res = await api.patch(`/appointments/${appointmentId}/cancel`, {
        cancellation_reason: 'Patient cancelled from dashboard',
      });
      setAppointments(appointments.map((a) => (a.id === appointmentId ? res.data : a)));
      fetchProfileData();
    } catch (err) {
      alert('Failed to cancel appointment.');
    }
  };

  const handleRescheduleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reschedulingAppt || !newDate) return;
    setRescheduling(true);
    try {
      const res = await api.patch(`/appointments/${reschedulingAppt.id}/reschedule`, {
        preferred_date: newDate,
        preferred_time: newTime,
        reason: 'Patient rescheduled',
      });
      setAppointments(appointments.map((a) => (a.id === reschedulingAppt.id ? res.data : a)));
      setReschedulingAppt(null);
      fetchProfileData();
    } catch (err) {
      alert('Failed to reschedule appointment.');
    } finally {
      setRescheduling(false);
    }
  };

  const initials = user?.name
    ? user.name
        .split(' ')
        .map((n) => n[0])
        .join('')
        .toUpperCase()
        .slice(0, 2)
    : 'U';

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      {/* Profile Header */}
      <header className="flex flex-col md:flex-row items-center justify-between gap-8 mb-12 bg-gray-800/80 backdrop-blur-xl p-8 rounded-3xl border border-white/10 shadow-2xl">
        <div className="flex flex-col sm:flex-row items-center gap-6 text-center sm:text-left">
          <div className="relative">
            <div className="w-24 h-24 sm:w-28 sm:h-28 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 border-4 border-white/20 flex items-center justify-center text-3xl font-extrabold text-white shadow-2xl shadow-blue-500/30">
              {initials}
            </div>
            <div className="absolute bottom-0 right-0 bg-emerald-500 text-white p-1.5 rounded-full shadow-lg border-2 border-gray-900 flex items-center justify-center">
              <span className="material-symbols-outlined text-xs font-bold">verified</span>
            </div>
          </div>

          <div>
            <div className="flex items-center justify-center sm:justify-start gap-2 mb-1">
              <h1 className="text-3xl font-extrabold text-white font-['Manrope']">
                {user?.name || 'Patient User'}
              </h1>
              {user?.role && user.role !== 'USER' && (
                <span className="px-2 py-0.5 bg-gradient-to-r from-purple-600 to-indigo-600 text-white text-[10px] font-extrabold uppercase rounded-md shadow">
                  {user.role}
                </span>
              )}
            </div>

            <div className="flex flex-wrap items-center justify-center sm:justify-start gap-2 text-xs">
              <span className="bg-blue-500/20 text-blue-300 px-3 py-1 rounded-lg font-bold border border-blue-500/30">
                Patient ID: MS-{user?.id ? user.id + 1000 : '99201'}
              </span>
              <span className="bg-purple-500/20 text-purple-300 px-3 py-1 rounded-lg font-bold border border-purple-500/30">
                {user?.email}
              </span>
              {user?.phone && (
                <span className="bg-white/10 text-gray-300 px-3 py-1 rounded-lg font-medium border border-white/15">
                  {user.phone}
                </span>
              )}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowEditModal(true)}
            className="flex items-center gap-1.5 px-5 py-3 bg-white/10 border border-white/15 font-semibold text-xs rounded-xl hover:bg-white/20 transition-all text-white"
          >
            <span className="material-symbols-outlined text-base">edit</span>
            <span>Edit Profile</span>
          </button>
          <button
            onClick={() => logout()}
            className="flex items-center gap-1.5 px-5 py-3 bg-red-600/80 hover:bg-red-700 font-semibold text-xs rounded-xl transition-all text-white shadow"
          >
            <span className="material-symbols-outlined text-base">logout</span>
            <span>Logout</span>
          </button>
        </div>
      </header>

      {/* Main Grid */}
      <div className="grid md:grid-cols-12 gap-8">
        {/* Left Sidebar: Medical Identity */}
        <aside className="md:col-span-4 space-y-6">
          <div className="bg-gray-800/80 backdrop-blur-xl p-6 rounded-2xl border border-white/10 shadow-xl space-y-4">
            <h3 className="text-base font-bold text-white font-['Manrope'] flex items-center gap-2 pb-3 border-b border-white/10">
              <span className="material-symbols-outlined text-emerald-400">security</span>
              Medical Identity
            </h3>

            <div className="p-3.5 bg-black/30 rounded-xl border border-white/5">
              <p className="text-[11px] text-gray-400 font-medium uppercase mb-0.5">Blood Group</p>
              <p className="text-base font-black text-white">{user?.blood_group || 'O Positive (O+)'}</p>
            </div>

            <div className="p-3.5 bg-black/30 rounded-xl border border-white/5">
              <p className="text-[11px] text-gray-400 font-medium uppercase mb-0.5">Allergies & Contraindications</p>
              <p className="text-xs font-bold text-red-400">{user?.allergies || 'None reported'}</p>
            </div>

            <div className="p-3.5 bg-black/30 rounded-xl border border-white/5">
              <p className="text-[11px] text-gray-400 font-medium uppercase mb-0.5">Emergency Contact</p>
              <p className="text-xs font-bold text-gray-200">{user?.emergency_contact || '+91 98765 43210'}</p>
            </div>
          </div>

          <div className="bg-gradient-to-br from-purple-900/40 to-blue-900/40 backdrop-blur-xl p-6 rounded-2xl border border-purple-500/30 shadow-xl space-y-3">
            <h3 className="text-base font-bold text-white font-['Manrope'] flex items-center gap-2">
              <span className="material-symbols-outlined text-purple-400">health_and_safety</span>
              Government Scheme Partner
            </h3>
            <p className="text-xs text-gray-300 leading-relaxed">
              You are pre-qualified for secondary and tertiary care under Ayushman Bharat PM-JAY.
            </p>
            <Link
              href="/eligibility"
              className="block w-full py-2.5 bg-gradient-to-r from-purple-600 to-blue-600 text-white font-bold rounded-xl text-center text-xs shadow transition-all"
            >
              Re-evaluate Eligibility →
            </Link>
          </div>
        </aside>

        {/* Right Dashboard Tabs */}
        <main className="md:col-span-8">
          <div className="bg-gray-800/80 backdrop-blur-xl rounded-2xl border border-white/10 shadow-2xl overflow-hidden">
            {/* Tabs Header */}
            <div className="flex flex-wrap border-b border-white/10 bg-black/30">
              {[
                { id: 'saved', label: 'Saved Hospitals', icon: 'favorite', count: savedHospitals.length },
                { id: 'insurance', label: 'Insurances', icon: 'shield', count: userInsurances.length },
                { id: 'claims', label: 'Claims', icon: 'receipt_long', count: userClaims.length },
                { id: 'appointments', label: 'Appointments', icon: 'calendar_month', count: appointments.length },
                { id: 'vault', label: 'Vault', icon: 'folder', count: documents.length },
                { id: 'notifications', label: 'Alerts', icon: 'notifications', count: notifications.length },
              ].map((t) => (
                <button
                  key={t.id}
                  onClick={() => setActiveTab(t.id as any)}
                  className={`flex items-center gap-1.5 px-4 sm:px-5 py-4 font-bold text-xs transition-all border-b-2 ${
                    activeTab === t.id
                      ? 'border-blue-500 text-blue-400 bg-white/5'
                      : 'border-transparent text-gray-400 hover:text-white hover:bg-white/5'
                  }`}
                >
                  <span className="material-symbols-outlined text-base">{t.icon}</span>
                  <span className="hidden sm:inline">{t.label}</span>
                  <span className="px-1.5 py-0.5 rounded-full bg-white/10 text-[10px] ml-1">{t.count}</span>
                </button>
              ))}
            </div>

            {/* Tab Contents */}
            <div className="p-6 sm:p-8">
              {/* Tab 1: Saved Hospitals */}
              {activeTab === 'saved' && (
                <div>
                  {savedHospitals.length === 0 ? (
                    <div className="text-center py-10">
                      <span className="material-symbols-outlined text-gray-500 text-4xl mb-2">favorite_border</span>
                      <p className="text-gray-300 font-bold text-sm">No saved hospitals yet</p>
                      <p className="text-gray-500 text-xs mt-1 mb-4">Bookmark hospitals while browsing to compare them here.</p>
                      <Link href="/hospitals" className="px-4 py-2 bg-blue-600 text-white font-bold rounded-xl text-xs">
                        Browse Hospitals →
                      </Link>
                    </div>
                  ) : (
                    <div className="grid sm:grid-cols-2 gap-4">
                      {savedHospitals.map((h) => (
                        <div key={h.id} className="relative">
                          <HospitalCard
                            hospital={h}
                            isSaved={true}
                            onSaveToggle={() => handleRemoveSaved(h.id)}
                          />
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Tab 2: Insurance Policies */}
              {activeTab === 'insurance' && (
                <div className="space-y-4">
                  {userInsurances.length === 0 ? (
                    <div className="text-center py-10">
                      <span className="material-symbols-outlined text-gray-500 text-4xl mb-2">health_and_safety</span>
                      <p className="text-gray-300 font-bold text-sm">No active insurance enrollments</p>
                      <p className="text-gray-500 text-xs mt-1 mb-4">Browse our insurance plans to secure health coverage.</p>
                      <Link href="/insurances" className="px-4 py-2 bg-emerald-600 text-white font-bold rounded-xl text-xs">
                        Explore Insurance Plans →
                      </Link>
                    </div>
                  ) : (
                    userInsurances.map((policy) => (
                      <div key={policy.id} className="p-5 bg-black/30 rounded-2xl border border-white/5 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 text-xs">
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-sm text-white">{policy.policy_number}</span>
                            <span className="px-2 py-0.5 bg-emerald-500/20 text-emerald-300 rounded font-bold uppercase text-[10px]">
                              {policy.status}
                            </span>
                          </div>
                          <p className="text-gray-400">Beneficiary: <strong className="text-white">{policy.dependents || 'Self'}</strong></p>
                          <p className="text-gray-400">Coverage: <strong className="text-emerald-400 font-bold">₹{policy.sum_insured?.toLocaleString()}</strong></p>
                        </div>

                        <Link
                          href="/claims"
                          className="px-4 py-2 bg-gradient-to-r from-emerald-600 to-teal-600 text-white font-bold rounded-xl text-xs shadow"
                        >
                          File a Claim
                        </Link>
                      </div>
                    ))
                  )}
                </div>
              )}

              {/* Tab 3: Insurance Claims */}
              {activeTab === 'claims' && (
                <div className="space-y-4">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-xs text-gray-400 font-semibold">Your Claim Records</span>
                    <Link href="/claims" className="text-blue-400 hover:underline text-xs font-bold">
                      + Submit New Claim
                    </Link>
                  </div>

                  {userClaims.length === 0 ? (
                    <div className="text-center py-10">
                      <p className="text-gray-400 text-xs">No claims filed yet.</p>
                    </div>
                  ) : (
                    userClaims.map((c) => (
                      <div key={c.id} className="p-4 bg-black/30 rounded-xl border border-white/5 flex justify-between items-center text-xs">
                        <div>
                          <span className="font-bold text-white block mb-0.5">Claim #{c.id}</span>
                          <span className="text-gray-400">{c.claim_description || 'Inpatient hospitalization'}</span>
                        </div>
                        <div className="text-right flex items-center gap-3">
                          <div>
                            <span className="text-emerald-400 font-bold block text-sm">₹{c.claim_amount?.toLocaleString()}</span>
                            <span className="px-2 py-0.5 bg-yellow-500/20 text-yellow-300 rounded text-[10px] font-bold uppercase">
                              {c.claim_status}
                            </span>
                          </div>
                          <Link
                            href="/claims"
                            className="px-3 py-1.5 bg-white/10 hover:bg-white/20 text-white rounded-lg text-xs"
                          >
                            Timeline →
                          </Link>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              )}

              {/* Tab 4: Booked Appointments */}
              {activeTab === 'appointments' && (
                <div className="space-y-4">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-xs text-gray-400 font-semibold">Upcoming Doctor Visits</span>
                    <Link href="/appointments" className="text-blue-400 hover:underline text-xs font-bold">
                      + Book New Visit
                    </Link>
                  </div>

                  {appointments.length === 0 ? (
                    <div className="text-center py-10">
                      <p className="text-gray-400 text-xs">No doctor consultations scheduled.</p>
                    </div>
                  ) : (
                    appointments.map((appt) => (
                      <div key={appt.id} className="p-4 bg-black/30 rounded-xl border border-white/5 flex flex-col sm:flex-row justify-between sm:items-center gap-3 text-xs">
                        <div>
                          <div className="flex items-center gap-2 mb-0.5">
                            <span className="font-bold text-white text-sm">{appt.department} Consultation</span>
                            <span
                              className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                                appt.status === 'CONFIRMED'
                                  ? 'bg-emerald-500/20 text-emerald-300'
                                  : appt.status === 'CANCELLED'
                                  ? 'bg-red-500/20 text-red-300'
                                  : 'bg-yellow-500/20 text-yellow-300'
                              }`}
                            >
                              {appt.status}
                            </span>
                          </div>
                          <span className="text-gray-400">{appt.preferred_date} at {appt.preferred_time}</span>
                        </div>

                        {appt.status !== 'CANCELLED' && (
                          <div className="flex items-center gap-2">
                            <button
                              onClick={() => {
                                setReschedulingAppt(appt);
                                setNewDate(appt.preferred_date);
                                setNewTime(appt.preferred_time);
                              }}
                              className="px-3 py-1.5 bg-white/10 hover:bg-white/20 text-white rounded-lg font-semibold text-xs"
                            >
                              Reschedule
                            </button>
                            <button
                              onClick={() => handleCancelAppointment(appt.id)}
                              className="px-3 py-1.5 bg-red-600/30 hover:bg-red-600/50 text-red-300 rounded-lg font-semibold text-xs"
                            >
                              Cancel
                            </button>
                          </div>
                        )}
                      </div>
                    ))
                  )}
                </div>
              )}

              {/* Tab 5: Medical Vault Documents */}
              {activeTab === 'vault' && (
                <div className="space-y-4">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-xs text-gray-400 font-semibold">Medical Records Vault</span>
                    <Link href="/medical-vault" className="text-blue-400 hover:underline text-xs font-bold">
                      + Open Vault Locker
                    </Link>
                  </div>

                  {documents.length === 0 ? (
                    <div className="text-center py-10">
                      <p className="text-gray-400 text-xs">No documents uploaded.</p>
                    </div>
                  ) : (
                    documents.map((doc) => (
                      <div key={doc.id} className="p-3.5 bg-black/30 rounded-xl border border-white/5 flex justify-between items-center text-xs">
                        <div className="flex items-center gap-3">
                          <span className="material-symbols-outlined text-blue-400 text-lg">description</span>
                          <div>
                            <span className="font-bold text-white block truncate max-w-[200px] sm:max-w-sm">{doc.original_name}</span>
                            <span className="text-gray-400 text-[10px]">{doc.doc_type} • {(doc.file_size / 1024).toFixed(0)} KB</span>
                          </div>
                        </div>
                        <a
                          href={`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}${doc.file_path.startsWith('/') ? '' : '/'}${doc.file_path}`}
                          target="_blank"
                          rel="noreferrer"
                          className="px-3 py-1 bg-white/10 hover:bg-white/20 text-white rounded text-xs"
                        >
                          View
                        </a>
                      </div>
                    ))
                  )}
                </div>
              )}

              {/* Tab 6: Notifications Alert Log */}
              {activeTab === 'notifications' && (
                <div className="space-y-3">
                  {notifications.length === 0 ? (
                    <div className="text-center py-10">
                      <p className="text-gray-400 text-xs">No notifications.</p>
                    </div>
                  ) : (
                    notifications.map((n) => (
                      <div
                        key={n.id}
                        className={`p-3.5 rounded-xl border text-xs ${
                          n.is_read ? 'bg-black/30 border-white/5 opacity-70' : 'bg-blue-950/40 border-blue-500/30'
                        }`}
                      >
                        <div className="font-bold text-white mb-0.5 flex justify-between items-center">
                          <span>{n.title}</span>
                          <span className="text-gray-500 font-mono text-[10px]">
                            {n.created_at ? new Date(n.created_at).toLocaleDateString() : 'Recent'}
                          </span>
                        </div>
                        <p className="text-gray-300 text-[11px]">{n.message}</p>
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>
          </div>
        </main>
      </div>

      {/* Edit Profile Modal */}
      {showEditModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-gray-800 rounded-2xl border border-white/20 p-8 max-w-md w-full shadow-2xl space-y-5 text-xs">
            <div className="flex justify-between items-center pb-3 border-b border-white/10">
              <h3 className="text-lg font-bold text-white font-['Manrope']">Edit Patient Profile</h3>
              <button onClick={() => setShowEditModal(false)} className="text-gray-400 hover:text-white">
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>

            <form onSubmit={handleProfileUpdate} className="space-y-4">
              <div>
                <label className="block text-gray-300 font-semibold mb-1">Full Name</label>
                <input
                  type="text"
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  required
                  className="w-full px-3 py-2 bg-black/40 border border-white/15 rounded-lg text-white"
                />
              </div>

              <div>
                <label className="block text-gray-300 font-semibold mb-1">Phone Number</label>
                <input
                  type="tel"
                  value={editPhone}
                  onChange={(e) => setEditPhone(e.target.value)}
                  className="w-full px-3 py-2 bg-black/40 border border-white/15 rounded-lg text-white"
                />
              </div>

              <div>
                <label className="block text-gray-300 font-semibold mb-1">Blood Group</label>
                <select
                  value={editBloodGroup}
                  onChange={(e) => setEditBloodGroup(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-900 border border-white/15 rounded-lg text-white"
                >
                  <option value="O+">O Positive (O+)</option>
                  <option value="O-">O Negative (O-)</option>
                  <option value="A+">A Positive (A+)</option>
                  <option value="A-">A Negative (A-)</option>
                  <option value="B+">B Positive (B+)</option>
                  <option value="B-">B Negative (B-)</option>
                  <option value="AB+">AB Positive (AB+)</option>
                  <option value="AB-">AB Negative (AB-)</option>
                </select>
              </div>

              <div>
                <label className="block text-gray-300 font-semibold mb-1">Allergies</label>
                <input
                  type="text"
                  value={editAllergies}
                  onChange={(e) => setEditAllergies(e.target.value)}
                  placeholder="e.g. Penicillin, Peanuts"
                  className="w-full px-3 py-2 bg-black/40 border border-white/15 rounded-lg text-white"
                />
              </div>

              <div>
                <label className="block text-gray-300 font-semibold mb-1">Emergency Contact Number</label>
                <input
                  type="text"
                  value={editEmergency}
                  onChange={(e) => setEditEmergency(e.target.value)}
                  placeholder="+91 XXXXX XXXXX"
                  className="w-full px-3 py-2 bg-black/40 border border-white/15 rounded-lg text-white"
                />
              </div>

              <button
                type="submit"
                disabled={savingProfile}
                className="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl text-xs transition-all shadow"
              >
                {savingProfile ? 'Saving Changes...' : 'Save Profile Details'}
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Reschedule Modal */}
      {reschedulingAppt && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-gray-800 rounded-2xl border border-white/20 p-6 max-w-md w-full shadow-2xl space-y-4 text-xs">
            <div className="flex justify-between items-center pb-2 border-b border-white/10">
              <h3 className="text-base font-bold text-white font-['Manrope']">
                Reschedule {reschedulingAppt.department} Visit
              </h3>
              <button onClick={() => setReschedulingAppt(null)} className="text-gray-400 hover:text-white">
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>

            <form onSubmit={handleRescheduleSubmit} className="space-y-3">
              <div>
                <label className="block text-gray-300 font-semibold mb-1">New Date *</label>
                <input
                  type="date"
                  value={newDate}
                  onChange={(e) => setNewDate(e.target.value)}
                  required
                  className="w-full px-3 py-2 bg-black/40 border border-white/15 rounded-lg text-white"
                />
              </div>

              <div>
                <label className="block text-gray-300 font-semibold mb-1">New Time Slot *</label>
                <select
                  value={newTime}
                  onChange={(e) => setNewTime(e.target.value)}
                  required
                  className="w-full px-3 py-2 bg-gray-900 border border-white/15 rounded-lg text-white"
                >
                  <option value="09:00 AM">09:00 AM - Morning</option>
                  <option value="10:30 AM">10:30 AM - Morning</option>
                  <option value="02:00 PM">02:00 PM - Afternoon</option>
                  <option value="04:30 PM">04:30 PM - Evening</option>
                  <option value="06:00 PM">06:00 PM - Evening</option>
                </select>
              </div>

              <button
                type="submit"
                disabled={rescheduling}
                className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl text-xs transition-all shadow"
              >
                {rescheduling ? 'Rescheduling...' : 'Confirm New Schedule'}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

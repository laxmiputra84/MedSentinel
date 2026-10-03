'use client';

import React, { useState, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/lib/authContext';
import api from '@/lib/api';

export default function AppointmentsPage() {
  return (
    <Suspense
      fallback={
        <div className="max-w-7xl mx-auto px-4 py-16 text-center text-gray-400 text-sm">
          <div className="w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
          Loading Scheduler...
        </div>
      }
    >
      <AppointmentsContent />
    </Suspense>
  );
}

function AppointmentsContent() {
  const searchParams = useSearchParams();
  const { user, isAuthenticated } = useAuth();

  const hospitalName = searchParams.get('hospitalName') || '';

  const [name, setName] = useState(user?.name || '');
  const [phone, setPhone] = useState(user?.phone || '');
  const [email, setEmail] = useState(user?.email || '');
  const [date, setDate] = useState('');
  const [time, setTime] = useState('');
  const [department, setDepartment] = useState('Cardiology');
  const [reason, setReason] = useState('');

  // OTP state
  const [otpSent, setOtpSent] = useState(false);
  const [otpCode, setOtpCode] = useState('');
  const [otpVerified, setOtpVerified] = useState(false);
  const [testOtp, setTestOtp] = useState<string | null>(null);
  const [otpSending, setOtpSending] = useState(false);
  const [otpVerifying, setOtpVerifying] = useState(false);

  const [booking, setBooking] = useState(false);
  const [successResult, setSuccessResult] = useState<any | null>(null);
  const [errorMsg, setErrorMsg] = useState('');

  const handleSendOtp = async () => {
    if (!phone || phone.length < 8) {
      setErrorMsg('Please enter a valid phone number to receive OTP');
      return;
    }
    setErrorMsg('');
    setOtpSending(true);
    try {
      const res = await api.post('/send-otp', { phone });
      setOtpSent(true);
      if (res.data.test_otp) {
        setTestOtp(res.data.test_otp);
      }
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to send OTP.');
    } finally {
      setOtpSending(false);
    }
  };

  const handleVerifyOtp = async () => {
    if (!otpCode || otpCode.length < 4) {
      setErrorMsg('Please enter the 6-digit OTP');
      return;
    }
    setErrorMsg('');
    setOtpVerifying(true);
    try {
      await api.post('/verify-otp', { phone, otp: otpCode });
      setOtpVerified(true);
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Invalid or expired OTP.');
    } finally {
      setOtpVerifying(false);
    }
  };

  const handleBookingSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!otpVerified) {
      setErrorMsg('Please verify your phone number via OTP before confirming your booking.');
      return;
    }

    setErrorMsg('');
    setBooking(true);
    try {
      const res = await api.post('/appointments', {
        name,
        phone,
        email,
        preferred_date: date,
        preferred_time: time,
        department,
        reason,
      });
      setSuccessResult(res.data);
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to book appointment.');
    } finally {
      setBooking(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      {/* Header */}
      <div className="text-center mb-12">
        <span className="text-blue-400 font-bold uppercase tracking-wider text-xs">Direct Hospital Scheduler</span>
        <h1 className="text-4xl sm:text-5xl font-extrabold mb-4 bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent font-['Manrope']">
          Book Your Medical Consultation
        </h1>
        <p className="text-gray-300 text-base max-w-xl mx-auto">
          Schedule visits with premier doctors, validated via 2-factor OTP phone security.
        </p>
      </div>

      {successResult ? (
        <div className="bg-gray-800/90 backdrop-blur-xl rounded-3xl p-10 border border-emerald-500/30 shadow-2xl text-center max-w-2xl mx-auto space-y-6">
          <div className="w-20 h-20 bg-emerald-500/20 text-emerald-400 rounded-full flex items-center justify-center mx-auto">
            <span className="material-symbols-outlined text-4xl">event_available</span>
          </div>

          <h2 className="text-3xl font-bold text-white font-['Manrope']">Appointment Confirmed!</h2>
          <p className="text-gray-300 text-sm">
            Your consultation booking for <strong className="text-white">{successResult.department}</strong> on{' '}
            <strong className="text-emerald-400">{successResult.preferred_date}</strong> at{' '}
            <strong className="text-emerald-400">{successResult.preferred_time}</strong> has been registered.
          </p>

          <div className="p-4 bg-black/40 rounded-xl border border-white/10 text-xs text-gray-300">
            A confirmation SMS and calendar invite have been dispatched to <strong>{successResult.phone}</strong>.
          </div>

          <div className="flex gap-4 justify-center pt-4">
            <Link
              href="/profile"
              className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-bold rounded-xl text-xs shadow-lg"
            >
              View in My Appointments →
            </Link>
            <button
              onClick={() => {
                setSuccessResult(null);
                setOtpVerified(false);
                setOtpSent(false);
                setOtpCode('');
              }}
              className="px-6 py-3 bg-white/10 text-white font-semibold rounded-xl text-xs"
            >
              Book Another Visit
            </button>
          </div>
        </div>
      ) : (
        <div className="grid lg:grid-cols-3 gap-8">
          {/* Main Form */}
          <div className="lg:col-span-2">
            <form
              onSubmit={handleBookingSubmit}
              className="bg-gray-800/80 backdrop-blur-xl rounded-2xl p-6 sm:p-8 border border-white/10 shadow-2xl space-y-6"
            >
              {hospitalName && (
                <div className="p-3.5 bg-blue-500/20 border border-blue-500/30 rounded-xl text-blue-300 text-xs font-semibold flex items-center gap-2">
                  <span className="material-symbols-outlined text-base">domain</span>
                  <span>Booking appointment at: {hospitalName}</span>
                </div>
              )}

              {errorMsg && (
                <div className="p-3.5 bg-red-500/20 border border-red-500/40 rounded-xl text-red-300 text-xs flex items-center gap-2">
                  <span className="material-symbols-outlined text-base">error</span>
                  <span>{errorMsg}</span>
                </div>
              )}

              <div className="grid sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-gray-300 mb-1.5">Full Patient Name *</label>
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="John Doe"
                    required
                    className="w-full px-4 py-3 bg-black/40 border border-white/15 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 text-sm"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-gray-300 mb-1.5">Email Address *</label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="john@example.com"
                    required
                    className="w-full px-4 py-3 bg-black/40 border border-white/15 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 text-sm"
                  />
                </div>
              </div>

              {/* Phone & OTP Section */}
              <div className="bg-black/30 p-4 rounded-xl border border-white/10 space-y-3">
                <label className="block text-xs font-semibold text-gray-300">
                  Mobile Phone & 2-Factor OTP Verification *
                </label>
                <div className="flex gap-2">
                  <input
                    type="tel"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder="+91 98765 43210"
                    disabled={otpVerified}
                    required
                    className="flex-1 px-4 py-2.5 bg-gray-900 border border-white/15 rounded-xl text-white placeholder-gray-500 text-sm"
                  />
                  {!otpVerified ? (
                    <button
                      type="button"
                      onClick={handleSendOtp}
                      disabled={otpSending}
                      className="px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl text-xs transition-all whitespace-nowrap"
                    >
                      {otpSending ? 'Sending...' : otpSent ? 'Resend OTP' : 'Send OTP'}
                    </button>
                  ) : (
                    <span className="px-3 py-2 bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 text-xs font-bold rounded-xl flex items-center gap-1">
                      <span className="material-symbols-outlined text-sm">check</span>
                      Verified
                    </span>
                  )}
                </div>

                {testOtp && !otpVerified && (
                  <div className="p-2.5 bg-purple-500/20 border border-purple-500/30 rounded-lg text-purple-300 text-xs flex justify-between items-center">
                    <span>Dev Mode Test OTP: <strong>{testOtp}</strong></span>
                    <button
                      type="button"
                      onClick={() => setOtpCode(testOtp)}
                      className="text-xs text-white underline font-bold"
                    >
                      Auto-fill
                    </button>
                  </div>
                )}

                {otpSent && !otpVerified && (
                  <div className="flex gap-2 pt-1">
                    <input
                      type="text"
                      value={otpCode}
                      onChange={(e) => setOtpCode(e.target.value)}
                      placeholder="Enter 6-digit OTP"
                      maxLength={6}
                      className="flex-1 px-4 py-2 bg-gray-900 border border-white/15 rounded-xl text-white text-xs font-bold tracking-widest text-center"
                    />
                    <button
                      type="button"
                      onClick={handleVerifyOtp}
                      disabled={otpVerifying}
                      className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-xl text-xs transition-all"
                    >
                      {otpVerifying ? 'Verifying...' : 'Verify OTP'}
                    </button>
                  </div>
                )}
              </div>

              {/* Date and Time */}
              <div className="grid sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-gray-300 mb-1.5">Preferred Date *</label>
                  <input
                    type="date"
                    value={date}
                    onChange={(e) => setDate(e.target.value)}
                    required
                    className="w-full px-4 py-3 bg-black/40 border border-white/15 rounded-xl text-white text-sm"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-gray-300 mb-1.5">Preferred Time *</label>
                  <select
                    value={time}
                    onChange={(e) => setTime(e.target.value)}
                    required
                    className="w-full px-4 py-3 bg-gray-900 border border-white/15 rounded-xl text-white text-sm"
                  >
                    <option value="">Select Time Slot</option>
                    <option value="09:00 AM">09:00 AM - Morning</option>
                    <option value="10:30 AM">10:30 AM - Morning</option>
                    <option value="02:00 PM">02:00 PM - Afternoon</option>
                    <option value="04:30 PM">04:30 PM - Evening</option>
                    <option value="06:00 PM">06:00 PM - Evening</option>
                  </select>
                </div>
              </div>

              {/* Department */}
              <div>
                <label className="block text-xs font-semibold text-gray-300 mb-1.5">Department *</label>
                <select
                  value={department}
                  onChange={(e) => setDepartment(e.target.value)}
                  required
                  className="w-full px-4 py-3 bg-gray-900 border border-white/15 rounded-xl text-white text-sm"
                >
                  <option value="Cardiology">Cardiology / Heart</option>
                  <option value="General Medicine">General Medicine</option>
                  <option value="Orthopedics">Orthopedics / Joint Care</option>
                  <option value="Endocrinology">Endocrinology / Diabetes</option>
                  <option value="Surgery">General / Laparoscopic Surgery</option>
                  <option value="Pediatrics">Pediatrics</option>
                </select>
              </div>

              {/* Reason */}
              <div>
                <label className="block text-xs font-semibold text-gray-300 mb-1.5">Reason for Visit (Optional)</label>
                <textarea
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  placeholder="Describe your symptoms or procedure required..."
                  rows={3}
                  className="w-full px-4 py-3 bg-black/40 border border-white/15 rounded-xl text-white placeholder-gray-500 text-sm focus:outline-none focus:border-blue-500"
                />
              </div>

              <button
                type="submit"
                disabled={booking}
                className="w-full py-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-extrabold rounded-xl hover:shadow-xl hover:shadow-blue-500/30 transition-all text-sm transform hover:scale-[1.01] disabled:opacity-50"
              >
                {booking ? 'Scheduling Consultation...' : 'Confirm Appointment →'}
              </button>
            </form>
          </div>

          {/* Sidebar Guidelines */}
          <div className="space-y-6">
            <div className="bg-gray-800/80 backdrop-blur-xl rounded-2xl p-6 border border-white/10 shadow-xl space-y-4">
              <h3 className="text-base font-bold text-white font-['Manrope'] flex items-center gap-2">
                <span className="material-symbols-outlined text-blue-400">verified_user</span>
                Booking Benefits
              </h3>
              <ul className="space-y-3 text-xs text-gray-300">
                <li className="flex items-start gap-2">
                  <span className="text-emerald-400 font-bold">✓</span>
                  <span>Instant appointment token generated</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-emerald-400 font-bold">✓</span>
                  <span>Free consultation cancellation up to 2 hours prior</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-emerald-400 font-bold">✓</span>
                  <span>Direct billing under PM-JAY / CGHS if applicable</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

'use client';

import React, { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/lib/authContext';
import api from '@/lib/api';

function LoginFormContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirectTarget = searchParams.get('redirect');
  const { login, isAuthenticated, user } = useAuth();

  const [activeTab, setActiveTab] = useState<'login' | 'signup'>('login');
  
  // Login fields
  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [showLoginPassword, setShowLoginPassword] = useState(false);

  // Signup fields
  const [signupName, setSignupName] = useState('');
  const [signupEmail, setSignupEmail] = useState('');
  const [signupPhone, setSignupPhone] = useState('');
  const [signupPassword, setSignupPassword] = useState('');
  const [showSignupPassword, setShowSignupPassword] = useState(false);

  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (isAuthenticated && user) {
      if (redirectTarget) {
        router.push(redirectTarget);
      } else if (['SUPER_ADMIN', 'HOSPITAL_ADMIN', 'INSURANCE_ADMIN'].includes((user.role || '').toUpperCase())) {
        router.push('/admin');
      } else {
        router.push('/profile');
      }
    }
  }, [isAuthenticated, user, redirectTarget, router]);

  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg('');
    setSuccessMsg('');
    setSubmitting(true);

    try {
      const res = await api.post('/auth/login', {
        email: loginEmail,
        password: loginPassword,
      });

      login(res.data);
      const userRole = (res.data.role || '').toUpperCase();
      if (redirectTarget) {
        router.push(redirectTarget);
      } else if (['SUPER_ADMIN', 'HOSPITAL_ADMIN', 'INSURANCE_ADMIN'].includes(userRole)) {
        router.push('/admin');
      } else {
        router.push('/profile');
      }
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.response?.data?.message || 'Invalid email or password';
      setErrorMsg(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const handleSignupSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg('');
    setSuccessMsg('');
    setSubmitting(true);

    try {
      await api.post('/auth/register', {
        name: signupName,
        email: signupEmail,
        phone: signupPhone,
        password: signupPassword,
      });

      // Auto login after registration
      const loginRes = await api.post('/auth/login', {
        email: signupEmail,
        password: signupPassword,
      });

      login(loginRes.data);
      router.push('/profile');
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.response?.data?.message || 'Registration failed. Please check your inputs.';
      setErrorMsg(msg);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-[85vh] flex items-center justify-center px-4 py-12 relative overflow-hidden">
      <div className="absolute top-0 right-0 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl pointer-events-none"></div>
      <div className="absolute bottom-0 left-0 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl pointer-events-none"></div>

      <div className="w-full max-w-md relative z-10">
        {/* Logo Section */}
        <div className="mb-8 text-center">
          <Link href="/" className="inline-flex items-center justify-center space-x-3 mb-4 group">
            <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg transition-transform group-hover:scale-105">
              <span className="material-symbols-outlined text-white text-2xl">health_and_safety</span>
            </div>
            <span className="text-3xl font-black bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent font-['Manrope']">
              MedSentinel
            </span>
          </Link>
          <p className="text-gray-400 text-sm">Affordable Healthcare Intelligence & Security</p>
        </div>

        {/* Main Card */}
        <div className="bg-gray-800/80 backdrop-blur-xl rounded-2xl border border-white/10 p-8 shadow-2xl">
          {/* Tabs */}
          <div className="flex gap-2 mb-8 bg-black/40 rounded-xl p-1 border border-white/5">
            <button
              onClick={() => {
                setActiveTab('login');
                setErrorMsg('');
                setSuccessMsg('');
              }}
              className={`flex-1 py-2.5 px-4 rounded-lg font-semibold text-sm transition-all ${
                activeTab === 'login'
                  ? 'bg-blue-600 text-white shadow-md'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              Login
            </button>
            <button
              onClick={() => {
                setActiveTab('signup');
                setErrorMsg('');
                setSuccessMsg('');
              }}
              className={`flex-1 py-2.5 px-4 rounded-lg font-semibold text-sm transition-all ${
                activeTab === 'signup'
                  ? 'bg-blue-600 text-white shadow-md'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              Sign Up
            </button>
          </div>

          {/* Alerts */}
          {errorMsg && (
            <div className="mb-6 p-3.5 bg-red-500/20 border border-red-500/40 rounded-xl text-red-300 text-xs flex items-center gap-2">
              <span className="material-symbols-outlined text-base">error</span>
              <span>{errorMsg}</span>
            </div>
          )}
          {successMsg && (
            <div className="mb-6 p-3.5 bg-emerald-500/20 border border-emerald-500/40 rounded-xl text-emerald-300 text-xs flex items-center gap-2">
              <span className="material-symbols-outlined text-base">check_circle</span>
              <span>{successMsg}</span>
            </div>
          )}

          {/* Login Form */}
          {activeTab === 'login' ? (
            <form onSubmit={handleLoginSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-300 mb-1.5">Email or Phone Number</label>
                <input
                  type="text"
                  value={loginEmail}
                  onChange={(e) => setLoginEmail(e.target.value)}
                  placeholder="name@example.com or +91 98765 43210"
                  required
                  className="w-full px-4 py-3 bg-black/40 border border-white/15 rounded-xl focus:outline-none focus:border-blue-500 text-white placeholder-gray-500 text-sm transition-all"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-300 mb-1.5">Password</label>
                <div className="relative">
                  <input
                    type={showLoginPassword ? 'text' : 'password'}
                    value={loginPassword}
                    onChange={(e) => setLoginPassword(e.target.value)}
                    placeholder="••••••••"
                    required
                    className="w-full px-4 py-3 bg-black/40 border border-white/15 rounded-xl focus:outline-none focus:border-blue-500 text-white placeholder-gray-500 text-sm transition-all"
                  />
                  <button
                    type="button"
                    onClick={() => setShowLoginPassword(!showLoginPassword)}
                    className="absolute right-3 top-3 text-gray-400 hover:text-white"
                  >
                    <span className="material-symbols-outlined text-lg">
                      {showLoginPassword ? 'visibility' : 'visibility_off'}
                    </span>
                  </button>
                </div>
              </div>

              {/* Quick Fill Demo Credentials */}
              <div className="pt-2 border-t border-white/10 space-y-2">
                <div className="text-[11px] font-bold text-gray-400 uppercase tracking-wider">Quick Sign-In Credentials:</div>
                <div className="grid grid-cols-2 gap-2 text-[11px]">
                  <button
                    type="button"
                    onClick={() => {
                      setLoginEmail('superadmin@medsentinel.com');
                      setLoginPassword('admin123');
                    }}
                    className="p-2 rounded-xl bg-purple-950/40 border border-purple-500/30 text-purple-300 hover:bg-purple-900/50 transition-all text-left flex flex-col"
                  >
                    <span className="font-bold flex items-center gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-purple-400"></span>
                      Super Admin
                    </span>
                    <span className="text-[10px] text-gray-400 truncate">superadmin@medsentinel.com</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      setLoginEmail('hospitaladmin@medsentinel.com');
                      setLoginPassword('hospital123');
                    }}
                    className="p-2 rounded-xl bg-blue-950/40 border border-blue-500/30 text-blue-300 hover:bg-blue-900/50 transition-all text-left flex flex-col"
                  >
                    <span className="font-bold flex items-center gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-blue-400"></span>
                      Hospital Admin
                    </span>
                    <span className="text-[10px] text-gray-400 truncate">hospitaladmin@medsentinel.com</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      setLoginEmail('insuranceadmin@medsentinel.com');
                      setLoginPassword('insurance123');
                    }}
                    className="p-2 rounded-xl bg-emerald-950/40 border border-emerald-500/30 text-emerald-300 hover:bg-emerald-900/50 transition-all text-left flex flex-col"
                  >
                    <span className="font-bold flex items-center gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                      Insurance Admin
                    </span>
                    <span className="text-[10px] text-gray-400 truncate">insuranceadmin@medsentinel.com</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      setLoginEmail('demo@medsentinel.com');
                      setLoginPassword('password123');
                    }}
                    className="p-2 rounded-xl bg-gray-900/60 border border-white/15 text-gray-300 hover:bg-white/10 transition-all text-left flex flex-col"
                  >
                    <span className="font-bold flex items-center gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-gray-400"></span>
                      Patient User
                    </span>
                    <span className="text-[10px] text-gray-400 truncate">demo@medsentinel.com</span>
                  </button>
                </div>
              </div>

              <button
                type="submit"
                disabled={submitting}
                className="w-full py-3.5 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-bold rounded-xl hover:shadow-lg hover:shadow-blue-500/30 transition-all transform hover:scale-[1.02] text-sm mt-4 disabled:opacity-50"
              >
                {submitting ? 'Authenticating...' : 'Login to MedSentinel'}
              </button>
            </form>
          ) : (
            /* Sign Up Form */
            <form onSubmit={handleSignupSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-300 mb-1.5">Full Name</label>
                <input
                  type="text"
                  value={signupName}
                  onChange={(e) => setSignupName(e.target.value)}
                  placeholder="John Doe"
                  required
                  className="w-full px-4 py-3 bg-black/40 border border-white/15 rounded-xl focus:outline-none focus:border-blue-500 text-white placeholder-gray-500 text-sm transition-all"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-300 mb-1.5">Email Address</label>
                <input
                  type="email"
                  value={signupEmail}
                  onChange={(e) => setSignupEmail(e.target.value)}
                  placeholder="john@example.com"
                  required
                  className="w-full px-4 py-3 bg-black/40 border border-white/15 rounded-xl focus:outline-none focus:border-blue-500 text-white placeholder-gray-500 text-sm transition-all"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-300 mb-1.5">Phone Number</label>
                <input
                  type="tel"
                  value={signupPhone}
                  onChange={(e) => setSignupPhone(e.target.value)}
                  placeholder="+91 98765 43210"
                  className="w-full px-4 py-3 bg-black/40 border border-white/15 rounded-xl focus:outline-none focus:border-blue-500 text-white placeholder-gray-500 text-sm transition-all"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-300 mb-1.5">Password</label>
                <div className="relative">
                  <input
                    type={showSignupPassword ? 'text' : 'password'}
                    value={signupPassword}
                    onChange={(e) => setSignupPassword(e.target.value)}
                    placeholder="At least 6 characters"
                    minLength={6}
                    required
                    className="w-full px-4 py-3 bg-black/40 border border-white/15 rounded-xl focus:outline-none focus:border-blue-500 text-white placeholder-gray-500 text-sm transition-all"
                  />
                  <button
                    type="button"
                    onClick={() => setShowSignupPassword(!showSignupPassword)}
                    className="absolute right-3 top-3 text-gray-400 hover:text-white"
                  >
                    <span className="material-symbols-outlined text-lg">
                      {showSignupPassword ? 'visibility' : 'visibility_off'}
                    </span>
                  </button>
                </div>
              </div>

              <button
                type="submit"
                disabled={submitting}
                className="w-full py-3.5 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-bold rounded-xl hover:shadow-lg hover:shadow-blue-500/30 transition-all transform hover:scale-[1.02] text-sm mt-4 disabled:opacity-50"
              >
                {submitting ? 'Creating Account...' : 'Create MedSentinel Account'}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-[85vh] flex items-center justify-center">
          <span className="material-symbols-outlined text-4xl text-blue-400 animate-spin">
            progress_activity
          </span>
        </div>
      }
    >
      <LoginFormContent />
    </Suspense>
  );
}

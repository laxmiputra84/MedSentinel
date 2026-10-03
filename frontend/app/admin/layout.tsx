'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/lib/authContext';
import { AdminSidebar } from '@/components/admin/AdminSidebar';

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const { user, isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      const redirectTarget = pathname ? `/login?redirect=${encodeURIComponent(pathname)}` : '/login?redirect=/admin';
      router.push(redirectTarget);
    }
  }, [isLoading, isAuthenticated, pathname, router]);

  if (isLoading) {
    return (
      <div className="min-h-[80vh] flex flex-col items-center justify-center gap-3">
        <span className="material-symbols-outlined text-4xl text-blue-400 animate-spin">
          progress_activity
        </span>
        <span className="text-gray-400 text-sm font-semibold">Verifying administrative credentials...</span>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-[80vh] flex flex-col items-center justify-center gap-3">
        <span className="material-symbols-outlined text-4xl text-blue-400 animate-spin">
          progress_activity
        </span>
        <span className="text-gray-400 text-sm font-semibold">Redirecting to administrator authentication...</span>
      </div>
    );
  }

  const role = (user?.role || 'USER').toUpperCase();
  const allowedRoles = ['SUPER_ADMIN', 'HOSPITAL_ADMIN', 'INSURANCE_ADMIN'];

  if (!allowedRoles.includes(role)) {
    return (
      <div className="min-h-[80vh] flex items-center justify-center px-4">
        <div className="max-w-md w-full bg-gray-900/90 border border-red-500/30 rounded-3xl p-8 text-center shadow-2xl backdrop-blur-xl space-y-5">
          <div className="w-16 h-16 bg-red-500/20 text-red-400 border border-red-500/30 rounded-2xl flex items-center justify-center mx-auto shadow-inner">
            <span className="material-symbols-outlined text-3xl">gpp_bad</span>
          </div>

          <div>
            <h1 className="text-xl font-bold text-white font-['Manrope']">Access Denied</h1>
            <p className="text-red-400 font-semibold text-sm mt-1">Admin access is required.</p>
            <p className="text-gray-400 text-xs mt-2 leading-relaxed">
              Your account (<span className="text-white font-mono font-medium">{user?.email}</span>) has role{' '}
              <span className="text-purple-300 font-bold">{role}</span>. Access to the MedSentinel Admin Console is strictly reserved for Super Admins, Hospital Directors, and Insurance Underwriters.
            </p>
          </div>

          <div className="pt-2 flex flex-col sm:flex-row gap-3 justify-center">
            <Link
              href="/"
              className="px-4 py-2.5 rounded-xl bg-white/10 hover:bg-white/15 text-xs font-semibold text-white border border-white/10 transition-all text-center"
            >
              Return to Patient Portal
            </Link>
            <Link
              href="/login?redirect=/admin"
              className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-xs font-bold text-white shadow-lg shadow-blue-500/20 transition-all text-center"
            >
              Sign In as Administrator
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-[calc(100vh-4rem)] bg-gradient-to-br from-gray-950 via-gray-900 to-black text-white">
      {/* Admin Sidebar Navigation */}
      <AdminSidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      {/* Main Admin Content Viewport */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Mobile Header Bar */}
        <div className="lg:hidden flex items-center justify-between px-4 py-3 bg-gray-900/80 backdrop-blur-md border-b border-white/10">
          <button
            onClick={() => setSidebarOpen(true)}
            className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-white/10 hover:bg-white/15 border border-white/10 text-xs font-semibold text-white"
          >
            <span className="material-symbols-outlined text-base">menu</span>
            <span>Admin Menu</span>
          </button>
          <span className="text-xs font-bold text-purple-300 bg-purple-900/30 border border-purple-500/30 px-2.5 py-1 rounded-lg">
            {role.replace('_', ' ')}
          </span>
        </div>

        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto space-y-6">
          {children}
        </main>
      </div>
    </div>
  );
}


'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/lib/authContext';

interface NavItem {
  name: string;
  href: string;
  icon: string;
  badge?: string;
  roles?: string[];
}

export const AdminSidebar: React.FC<{ isOpen: boolean; onClose: () => void }> = ({
  isOpen,
  onClose,
}) => {
  const pathname = usePathname();
  const { user } = useAuth();
  const userRole = user?.role || 'SUPER_ADMIN';

  const navItems: NavItem[] = [
    { name: 'Overview', href: '/admin', icon: 'dashboard' },
    { name: 'User Directory', href: '/admin/users', icon: 'group', roles: ['SUPER_ADMIN'] },
    { name: 'Knowledge Base', href: '/admin/knowledge-base', icon: 'dataset', badge: 'RAG' },
    { name: 'Hospitals', href: '/admin/hospitals', icon: 'local_hospital' },
    { name: 'Hospital Media', href: '/admin/hospital-media', icon: 'perm_media' },
    { name: 'Insurance Plans', href: '/admin/insurances', icon: 'health_and_safety' },
    { name: 'Claims Queue', href: '/admin/claims', icon: 'receipt_long' },
    { name: 'Medical Documents', href: '/admin/documents', icon: 'folder_open' },
    { name: 'Appointments', href: '/admin/appointments', icon: 'event' },
    { name: 'Govt Schemes', href: '/admin/schemes', icon: 'policy', roles: ['SUPER_ADMIN'] },
    { name: 'Notifications', href: '/admin/notifications', icon: 'campaign', roles: ['SUPER_ADMIN'] },
    { name: 'Analytics', href: '/admin/analytics', icon: 'monitoring' },
    { name: 'AI Insights', href: '/admin/ai-insights', icon: 'neurology', badge: 'AI' },
    { name: 'AI Monitoring', href: '/admin/ai-monitoring', icon: 'troubleshoot', badge: 'LIVE', roles: ['SUPER_ADMIN'] },
    { name: 'Plugin Hub', href: '/admin/plugins', icon: 'hub', badge: 'NEW', roles: ['SUPER_ADMIN'] },
    { name: 'Audit Logs', href: '/admin/audit-logs', icon: 'history', roles: ['SUPER_ADMIN'] },
  ];


  const filteredItems = navItems.filter((item) => {
    if (!item.roles) return true;
    return item.roles.includes(userRole);
  });

  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div
          onClick={onClose}
          className="fixed inset-0 bg-black/70 backdrop-blur-sm z-40 lg:hidden"
        />
      )}

      <aside
        className={`fixed lg:sticky top-0 lg:top-16 left-0 z-40 h-screen lg:h-[calc(100vh-4rem)] w-64 bg-gray-950/95 lg:bg-gray-900/60 backdrop-blur-xl border-r border-white/10 flex flex-col justify-between transition-transform duration-300 ${
          isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        <div className="flex-1 overflow-y-auto px-4 py-6 space-y-6">
          {/* Admin Header Mobile only */}
          <div className="lg:hidden flex items-center justify-between pb-4 border-b border-white/10">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                <span className="material-symbols-outlined text-white text-sm">shield_person</span>
              </div>
              <span className="font-bold text-sm bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                Admin Console
              </span>
            </div>
            <button onClick={onClose} className="p-1 rounded-lg text-gray-400 hover:text-white">
              <span className="material-symbols-outlined text-lg">close</span>
            </button>
          </div>

          {/* Role Status Tag */}
          <div className="bg-gradient-to-r from-blue-900/30 to-purple-900/30 border border-blue-500/20 rounded-xl p-3">
            <div className="flex items-center justify-between">
              <span className="text-[10px] uppercase font-bold text-gray-400 tracking-wider">Access Scope</span>
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-500/20 text-blue-300 border border-blue-500/30">
                {userRole.replace('_', ' ')}
              </span>
            </div>
            <p className="text-xs text-white font-medium mt-1 truncate">{user?.name || 'Administrator'}</p>
          </div>

          {/* Navigation Links */}
          <nav className="space-y-1">
            {filteredItems.map((item) => {
              const isActive = pathname === item.href || (item.href !== '/admin' && pathname.startsWith(item.href));
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => onClose()}
                  className={`flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all group ${
                    isActive
                      ? 'bg-gradient-to-r from-blue-600/90 to-purple-600/90 text-white shadow-lg shadow-blue-500/20 border border-blue-400/30'
                      : 'text-gray-400 hover:text-white hover:bg-white/5 border border-transparent'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <span
                      className={`material-symbols-outlined text-lg transition-transform group-hover:scale-110 ${
                        isActive ? 'text-white' : 'text-gray-400 group-hover:text-blue-400'
                      }`}
                    >
                      {item.icon}
                    </span>
                    <span>{item.name}</span>
                  </div>
                  {item.badge && (
                    <span className="px-1.5 py-0.5 text-[9px] font-extrabold uppercase rounded bg-purple-500/30 text-purple-300 border border-purple-400/30">
                      {item.badge}
                    </span>
                  )}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Footer Actions */}
        <div className="p-4 border-t border-white/10 space-y-2">
          <Link
            href="/"
            className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-xl text-xs font-semibold text-gray-300 hover:text-white bg-white/5 hover:bg-white/10 border border-white/10 transition-all"
          >
            <span className="material-symbols-outlined text-sm">arrow_back</span>
            <span>Back to Portal</span>
          </Link>
        </div>
      </aside>
    </>
  );
};

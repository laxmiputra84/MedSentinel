'use client';

import React from 'react';
import Link from 'next/link';
import { useAuth } from '@/lib/authContext';

interface AdminHeaderProps {
  title: string;
  subtitle?: string;
  onMenuToggle?: () => void;
  actions?: React.ReactNode;
}

export const AdminHeader: React.FC<AdminHeaderProps> = ({
  title,
  subtitle,
  onMenuToggle,
  actions,
}) => {
  const { user, logout } = useAuth();

  return (
    <header className="bg-gray-900/40 backdrop-blur-xl border-b border-white/10 px-4 sm:px-6 py-4 sticky top-16 z-30">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          {onMenuToggle && (
            <button
              onClick={onMenuToggle}
              className="lg:hidden p-2 rounded-xl text-gray-300 hover:text-white hover:bg-white/10 border border-white/10"
            >
              <span className="material-symbols-outlined text-xl">menu</span>
            </button>
          )}
          <div>
            <h1 className="text-xl sm:text-2xl font-bold text-white font-['Manrope'] tracking-tight flex items-center gap-2">
              <span>{title}</span>
            </h1>
            {subtitle && <p className="text-xs text-gray-400 mt-0.5">{subtitle}</p>}
          </div>
        </div>

        <div className="flex items-center gap-3 self-end sm:self-auto">
          {actions}

          <div className="hidden md:flex items-center gap-2 bg-white/5 border border-white/10 rounded-xl px-3 py-1.5 text-xs text-gray-300">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span className="text-[11px] font-medium text-gray-300">API Live</span>
          </div>

          <div className="flex items-center gap-2 pl-2 border-l border-white/10">
            <div className="text-right hidden sm:block">
              <div className="text-xs font-semibold text-white truncate max-w-[140px]">{user?.name || 'Administrator'}</div>
              <div className="text-[10px] text-gray-400">{user?.role || 'SUPER_ADMIN'}</div>
            </div>
            <button
              onClick={() => logout()}
              title="Sign Out"
              className="p-2 rounded-xl text-gray-400 hover:text-red-400 hover:bg-red-500/10 border border-white/10 transition-all"
            >
              <span className="material-symbols-outlined text-sm">logout</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};

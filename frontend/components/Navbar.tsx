'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/lib/authContext';
import { Notification } from '@/lib/types';
import api from '@/lib/api';

export const Navbar: React.FC = () => {
  const pathname = usePathname();
  const { user, isAuthenticated, logout } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Notification state
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [showNotifMenu, setShowNotifMenu] = useState(false);

  const navLinks = [
    { name: 'Home', href: '/' },
    { name: 'Hospitals', href: '/hospitals' },
    { name: 'Comparison', href: '/comparison' },
    { name: 'Schemes', href: '/schemes' },
    { name: 'Eligibility', href: '/eligibility' },
    { name: 'Insurance', href: '/insurances' },
    { name: 'Vault', href: '/medical-vault' },
  ];

  const fetchNotifications = async () => {
    if (!isAuthenticated) return;
    try {
      const res = await api.get<Notification[]>('/notifications');
      setNotifications(res.data);
    } catch (err) {
      // Quiet fail if not logged in
    }
  };

  useEffect(() => {
    fetchNotifications();
    if (isAuthenticated) {
      const interval = setInterval(fetchNotifications, 20000);
      return () => clearInterval(interval);
    }
  }, [isAuthenticated]);

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  const handleMarkAllRead = async () => {
    try {
      await api.patch('/notifications/read-all');
      setNotifications(notifications.map((n) => ({ ...n, is_read: true })));
    } catch (err) {
      console.error('Error marking all notifications as read:', err);
    }
  };

  const handleMarkRead = async (id: number) => {
    try {
      await api.patch(`/notifications/${id}/read`);
      setNotifications(notifications.map((n) => (n.id === id ? { ...n, is_read: true } : n)));
    } catch (err) {
      console.error('Error marking notification as read:', err);
    }
  };

  return (
    <nav className="bg-black/50 backdrop-blur-xl border-b border-white/10 sticky top-0 z-50 transition-all">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center space-x-3 group">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg group-hover:scale-105 transition-transform duration-200">
              <span className="material-symbols-outlined text-white text-xl">health_and_safety</span>
            </div>
            <span className="text-xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent font-['Manrope']">
              MedSentinel
            </span>
          </Link>

          {/* Desktop Nav Links */}
          <div className="hidden md:flex items-center space-x-1 lg:space-x-2">
            {navLinks.map((link) => {
              const isActive = pathname === link.href;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                    isActive
                      ? 'text-blue-400 bg-white/5 shadow-sm'
                      : 'text-gray-300 hover:text-white hover:bg-white/5'
                  }`}
                >
                  {link.name}
                </Link>
              );
            })}
          </div>

          {/* User Auth Buttons & Notification Bell */}
          <div className="hidden sm:flex items-center space-x-3">
            {isAuthenticated ? (
              <div className="flex items-center space-x-3">
                {/* Notification Bell */}
                <div className="relative">
                  <button
                    onClick={() => setShowNotifMenu(!showNotifMenu)}
                    className="relative p-2 rounded-xl text-gray-300 hover:text-white hover:bg-white/10 transition-all"
                    title="Notifications"
                  >
                    <span className="material-symbols-outlined text-xl">notifications</span>
                    {unreadCount > 0 && (
                      <span className="absolute top-1 right-1 w-4 h-4 bg-red-500 text-white text-[10px] font-extrabold rounded-full flex items-center justify-center animate-pulse">
                        {unreadCount}
                      </span>
                    )}
                  </button>

                  {/* Notification Dropdown */}
                  {showNotifMenu && (
                    <div className="absolute right-0 mt-2 w-80 bg-gray-900 border border-white/15 rounded-2xl shadow-2xl p-4 z-50 space-y-3 text-xs">
                      <div className="flex justify-between items-center pb-2 border-b border-white/10">
                        <span className="font-bold text-white">Notifications ({unreadCount} unread)</span>
                        {unreadCount > 0 && (
                          <button
                            onClick={handleMarkAllRead}
                            className="text-blue-400 hover:underline text-[11px]"
                          >
                            Mark all read
                          </button>
                        )}
                      </div>

                      <div className="max-h-64 overflow-y-auto space-y-2">
                        {notifications.length === 0 ? (
                          <div className="text-center py-6 text-gray-400">No notifications yet.</div>
                        ) : (
                          notifications.slice(0, 8).map((n) => (
                            <div
                              key={n.id}
                              onClick={() => handleMarkRead(n.id)}
                              className={`p-2.5 rounded-xl border transition-all cursor-pointer ${
                                n.is_read
                                  ? 'bg-black/20 border-white/5 opacity-70'
                                  : 'bg-blue-950/40 border-blue-500/30'
                              }`}
                            >
                              <div className="font-bold text-white flex items-center justify-between">
                                <span className="truncate">{n.title}</span>
                                {!n.is_read && (
                                  <span className="w-2 h-2 rounded-full bg-blue-400 flex-shrink-0"></span>
                                )}
                              </div>
                              <p className="text-gray-300 text-[11px] mt-0.5">{n.message}</p>
                            </div>
                          ))
                        )}
                      </div>
                    </div>
                  )}
                </div>

                {user?.role && user.role !== 'USER' && (
                  <Link
                    href="/admin"
                    className="px-3 py-1.5 rounded-xl text-xs font-bold text-purple-300 bg-purple-900/30 hover:bg-purple-900/50 border border-purple-500/40 transition-all flex items-center gap-1 shadow-sm"
                  >
                    <span className="material-symbols-outlined text-sm text-purple-400">shield_person</span>
                    <span>Admin</span>
                  </Link>
                )}
                <Link
                  href="/profile"
                  className="px-3.5 py-1.5 rounded-xl text-xs font-semibold text-white bg-white/10 hover:bg-white/20 border border-white/10 transition-all flex items-center gap-1.5"
                >
                  <span className="material-symbols-outlined text-sm text-blue-400">account_circle</span>
                  <span>{user?.name ? user.name.split(' ')[0] : 'Profile'}</span>
                  {user?.role && user.role !== 'USER' && (
                    <span className="px-1.5 py-0.2 bg-purple-500/30 text-purple-300 text-[9px] font-bold rounded">
                      {user.role === 'SUPER_ADMIN' ? 'Admin' : user.role === 'HOSPITAL_ADMIN' ? 'Hospital' : 'Insurer'}
                    </span>
                  )}
                </Link>
                <button
                  onClick={() => logout()}
                  className="px-3 py-1.5 rounded-xl text-xs font-semibold text-white bg-red-600/80 hover:bg-red-700 transition-all flex items-center gap-1 shadow"
                >
                  <span className="material-symbols-outlined text-sm">logout</span>
                  <span>Logout</span>
                </button>
              </div>
            ) : (
              <div className="flex items-center space-x-2">
                <Link
                  href="/login"
                  className="px-4 py-1.5 text-xs font-semibold text-gray-300 hover:text-white transition-colors"
                >
                  Sign In
                </Link>
                <Link
                  href="/register"
                  className="px-4 py-1.5 bg-gradient-to-r from-blue-600 to-purple-600 text-white text-xs font-semibold rounded-xl hover:shadow-lg hover:shadow-blue-500/30 transition-all"
                >
                  Get Started
                </Link>
              </div>
            )}
          </div>

          {/* Mobile Menu Button */}
          <div className="flex md:hidden items-center space-x-2">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-white/10 transition-all"
            >
              <span className="material-symbols-outlined text-xl">
                {mobileMenuOpen ? 'close' : 'menu'}
              </span>
            </button>
          </div>
        </div>
      </div>

      {/* Mobile dropdown */}
      {mobileMenuOpen && (
        <div className="md:hidden bg-gray-900/95 backdrop-blur-2xl border-b border-white/10 px-4 pt-2 pb-4 space-y-1">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              onClick={() => setMobileMenuOpen(false)}
              className={`block px-3 py-2 rounded-lg text-xs font-medium ${
                pathname === link.href
                  ? 'text-blue-400 bg-white/5 font-semibold'
                  : 'text-gray-300 hover:text-white'
              }`}
            >
              {link.name}
            </Link>
          ))}
          <div className="pt-3 border-t border-white/10 flex flex-col space-y-2">
            {isAuthenticated ? (
              <>
                <Link
                  href="/profile"
                  onClick={() => setMobileMenuOpen(false)}
                  className="px-3 py-2 text-xs text-white font-medium bg-white/10 rounded-lg text-center"
                >
                  My Profile
                </Link>
                <button
                  onClick={() => {
                    logout();
                    setMobileMenuOpen(false);
                  }}
                  className="px-3 py-2 text-xs text-white font-medium bg-red-600 rounded-lg text-center"
                >
                  Logout
                </button>
              </>
            ) : (
              <>
                <Link
                  href="/login"
                  onClick={() => setMobileMenuOpen(false)}
                  className="px-3 py-2 text-xs text-gray-300 text-center"
                >
                  Sign In
                </Link>
                <Link
                  href="/register"
                  onClick={() => setMobileMenuOpen(false)}
                  className="px-3 py-2 text-xs text-white font-semibold bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg text-center"
                >
                  Get Started
                </Link>
              </>
            )}
          </div>
        </div>
      )}
    </nav>
  );
};

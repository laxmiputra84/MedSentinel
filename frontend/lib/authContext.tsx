'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { User, UserRole } from './types';
import api from './api';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (tokenData: { access_token: string; refresh_token: string; user_id: number; name: string; email: string; role?: string }) => void;
  logout: () => Promise<void>;
  updateUser: (updated: Partial<User>) => void;
  refreshUserData: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const normalizeRole = (role?: string): UserRole => {
  if (!role) return 'USER';
  const r = role.trim().toUpperCase();
  if (['ADMIN', 'SUPERADMIN', 'SUPER_ADMINISTRATOR', 'ADMINISTRATOR'].includes(r)) return 'SUPER_ADMIN';
  if (['HOSPITAL', 'HOSPITALADMIN'].includes(r)) return 'HOSPITAL_ADMIN';
  if (['INSURANCE', 'INSURANCEADMIN', 'INSURER'].includes(r)) return 'INSURANCE_ADMIN';
  if (['PATIENT', 'CLIENT', 'USER'].includes(r)) return 'USER';
  if (['SUPER_ADMIN', 'HOSPITAL_ADMIN', 'INSURANCE_ADMIN'].includes(r)) return r as UserRole;
  return 'USER';
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchCurrentUser = async () => {
    try {
      const res = await api.get<User>('/auth/me');
      const normalizedUser: User = {
        ...res.data,
        role: normalizeRole(res.data.role),
      };
      setUser(normalizedUser);
      localStorage.setItem('user', JSON.stringify(normalizedUser));
    } catch (err: any) {
      // If unauthorized, clear tokens
      if (err?.response?.status === 401 || err?.response?.status === 403) {
        setUser(null);
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
      }
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
    const storedUser = typeof window !== 'undefined' ? localStorage.getItem('user') : null;

    if (token) {
      if (storedUser) {
        try {
          const parsed = JSON.parse(storedUser);
          if (parsed) {
            parsed.role = normalizeRole(parsed.role);
            setUser(parsed);
          }
        } catch (e) {}
      }
      fetchCurrentUser();
    } else {
      setIsLoading(false);
    }
  }, []);

  const login = (tokenData: { access_token: string; refresh_token: string; user_id: number; name: string; email: string; role?: string }) => {
    localStorage.setItem('access_token', tokenData.access_token);
    localStorage.setItem('refresh_token', tokenData.refresh_token);
    const initialUser: User = {
      id: tokenData.user_id,
      name: tokenData.name,
      email: tokenData.email,
      role: normalizeRole(tokenData.role),
    };
    setUser(initialUser);
    localStorage.setItem('user', JSON.stringify(initialUser));
    fetchCurrentUser();
  };

  const logout = async () => {
    try {
      const refreshToken = localStorage.getItem('refresh_token');
      await api.post('/auth/logout', { refresh_token: refreshToken });
    } catch (e) {
      // Proceed even if backend logout fails
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
      setUser(null);
    }
  };

  const updateUser = (updated: Partial<User>) => {
    setUser((prev) => {
      if (!prev) return null;
      const next = { ...prev, ...updated };
      localStorage.setItem('user', JSON.stringify(next));
      return next;
    });
  };

  const refreshUserData = async () => {
    await fetchCurrentUser();
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        login,
        logout,
        updateUser,
        refreshUserData,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

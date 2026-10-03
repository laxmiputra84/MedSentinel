'use client';

import React from 'react';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { useAuth } from '@/lib/authContext';
import {
  Settings,
  User,
  Bell,
  Cpu,
  Database,
  Shield,
  Save,
} from 'lucide-react';

export default function SettingsPage() {
  return (
    <ProtectedRoute>
      <SettingsContent />
    </ProtectedRoute>
  );
}

function SettingsContent() {
  const { user } = useAuth();

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center gap-3 mb-8 border-b border-slate-800 pb-6">
          <div className="p-2.5 bg-indigo-500/10 border border-indigo-500/30 rounded-xl text-indigo-400">
            <Settings className="w-7 h-7" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white">System Settings & Preferences</h1>
            <p className="text-sm text-slate-400">Configure multi-agent execution thresholds, notification webhooks, and profile details.</p>
          </div>
        </div>

        <div className="space-y-6">
          {/* User Profile */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
            <h2 className="text-base font-bold text-white mb-4 flex items-center gap-2">
              <User className="w-5 h-5 text-indigo-400" /> Account Profile
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div>
                <label className="text-slate-400 block mb-1">Full Name</label>
                <input
                  type="text"
                  disabled
                  value={user?.name || 'Administrator'}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-white"
                />
              </div>
              <div>
                <label className="text-slate-400 block mb-1">Email Address</label>
                <input
                  type="text"
                  disabled
                  value={user?.email || 'admin@medsentinel.com'}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-white"
                />
              </div>
              <div>
                <label className="text-slate-400 block mb-1">Role / Privilege Level</label>
                <input
                  type="text"
                  disabled
                  value={user?.role || 'ADMIN'}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-indigo-400 font-bold"
                />
              </div>
            </div>
          </div>

          {/* Engine Thresholds */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
            <h2 className="text-base font-bold text-white mb-4 flex items-center gap-2">
              <Cpu className="w-5 h-5 text-emerald-400" /> Multi-Agent Execution Settings
            </h2>
            <div className="space-y-4 text-xs">
              <div className="flex items-center justify-between p-3 bg-slate-950 rounded-xl border border-slate-800">
                <div>
                  <div className="font-semibold text-white">Maximum Agent Retries on Transient Failure</div>
                  <div className="text-slate-400 text-[11px]">Number of exponential backoff retry attempts per task</div>
                </div>
                <span className="font-mono font-bold text-indigo-400">3 Attempts</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-slate-950 rounded-xl border border-slate-800">
                <div>
                  <div className="font-semibold text-white">Step Timeout Limit</div>
                  <div className="text-slate-400 text-[11px]">Hard timeout before triggering fallback or replanning</div>
                </div>
                <span className="font-mono font-bold text-indigo-400">60 Seconds</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-slate-950 rounded-xl border border-slate-800">
                <div>
                  <div className="font-semibold text-white">FastEmbed ONNX Vector Model</div>
                  <div className="text-slate-400 text-[11px]">Configured semantic embedding engine</div>
                </div>
                <span className="font-mono font-bold text-emerald-400">BAAI/bge-small-en-v1.5</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

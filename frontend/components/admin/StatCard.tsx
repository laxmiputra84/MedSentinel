'use client';

import React from 'react';

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: string;
  trend?: {
    value: string;
    isPositive: boolean;
  };
  color?: 'blue' | 'purple' | 'emerald' | 'amber' | 'rose' | 'cyan';
  onClick?: () => void;
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtitle,
  icon,
  trend,
  color = 'blue',
  onClick,
}) => {
  const colorMap = {
    blue: {
      gradient: 'from-blue-500/20 to-blue-600/5',
      border: 'border-blue-500/30 hover:border-blue-400/50',
      iconBg: 'bg-blue-500/20 text-blue-400',
      text: 'text-blue-400',
    },
    purple: {
      gradient: 'from-purple-500/20 to-purple-600/5',
      border: 'border-purple-500/30 hover:border-purple-400/50',
      iconBg: 'bg-purple-500/20 text-purple-400',
      text: 'text-purple-400',
    },
    emerald: {
      gradient: 'from-emerald-500/20 to-emerald-600/5',
      border: 'border-emerald-500/30 hover:border-emerald-400/50',
      iconBg: 'bg-emerald-500/20 text-emerald-400',
      text: 'text-emerald-400',
    },
    amber: {
      gradient: 'from-amber-500/20 to-amber-600/5',
      border: 'border-amber-500/30 hover:border-amber-400/50',
      iconBg: 'bg-amber-500/20 text-amber-400',
      text: 'text-amber-400',
    },
    rose: {
      gradient: 'from-rose-500/20 to-rose-600/5',
      border: 'border-rose-500/30 hover:border-rose-400/50',
      iconBg: 'bg-rose-500/20 text-rose-400',
      text: 'text-rose-400',
    },
    cyan: {
      gradient: 'from-cyan-500/20 to-cyan-600/5',
      border: 'border-cyan-500/30 hover:border-cyan-400/50',
      iconBg: 'bg-cyan-500/20 text-cyan-400',
      text: 'text-cyan-400',
    },
  };

  const scheme = colorMap[color];

  return (
    <div
      onClick={onClick}
      className={`bg-gradient-to-br ${scheme.gradient} bg-gray-900/60 backdrop-blur-xl border ${scheme.border} rounded-2xl p-5 transition-all duration-300 ${
        onClick ? 'cursor-pointer hover:scale-[1.02] shadow-lg' : ''
      }`}
    >
      <div className="flex items-start justify-between">
        <div>
          <span className="text-xs font-semibold uppercase tracking-wider text-gray-400">{title}</span>
          <div className="text-2xl sm:text-3xl font-extrabold text-white font-['Manrope'] mt-1 tracking-tight">
            {typeof value === 'number' ? value.toLocaleString() : value}
          </div>
          {subtitle && <p className="text-[11px] text-gray-400 mt-1">{subtitle}</p>}
        </div>
        <div className={`w-11 h-11 rounded-xl ${scheme.iconBg} flex items-center justify-center shadow-md`}>
          <span className="material-symbols-outlined text-xl">{icon}</span>
        </div>
      </div>

      {trend && (
        <div className="mt-3 pt-3 border-t border-white/5 flex items-center gap-1.5 text-xs">
          <span
            className={`material-symbols-outlined text-sm ${
              trend.isPositive ? 'text-emerald-400' : 'text-rose-400'
            }`}
          >
            {trend.isPositive ? 'trending_up' : 'trending_down'}
          </span>
          <span className={trend.isPositive ? 'text-emerald-400 font-semibold' : 'text-rose-400 font-semibold'}>
            {trend.value}
          </span>
          <span className="text-gray-500 text-[10px]">vs previous cycle</span>
        </div>
      )}
    </div>
  );
};

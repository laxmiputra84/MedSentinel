'use client';

import React from 'react';

interface BarData {
  label: string;
  value: number;
  color?: string;
  subValue?: string;
}

interface AnalyticsChartProps {
  title: string;
  subtitle?: string;
  data: BarData[];
  type?: 'horizontal-bars' | 'donut-breakdown' | 'trend-bars';
  badge?: string;
}

export const AnalyticsChart: React.FC<AnalyticsChartProps> = ({
  title,
  subtitle,
  data,
  type = 'horizontal-bars',
  badge,
}) => {
  const totalSum = data.reduce((acc, curr) => acc + curr.value, 0) || 1;
  const maxValue = Math.max(...data.map((d) => d.value), 1);

  const defaultColors = [
    '#3b82f6', // blue
    '#8b5cf6', // purple
    '#10b981', // emerald
    '#f59e0b', // amber
    '#ec4899', // pink
    '#06b6d4', // cyan
    '#ef4444', // red
  ];

  return (
    <div className="bg-gray-900/60 backdrop-blur-xl border border-white/10 rounded-2xl p-5 shadow-xl flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between pb-3 border-b border-white/5">
          <div>
            <h2 className="text-sm font-bold text-white tracking-wide">{title}</h2>
            {subtitle && <p className="text-[11px] text-gray-400 mt-0.5">{subtitle}</p>}
          </div>
          {badge && (
            <span className="px-2 py-0.5 text-[10px] font-bold rounded-full bg-blue-500/20 text-blue-300 border border-blue-500/30">
              {badge}
            </span>
          )}
        </div>

        {type === 'horizontal-bars' && (
          <div className="mt-4 space-y-3.5">
            {data.map((item, idx) => {
              const percentage = Math.round((item.value / totalSum) * 100);
              const barColor = item.color || defaultColors[idx % defaultColors.length];

              return (
                <div key={item.label} className="space-y-1">
                  <div className="flex justify-between items-center text-xs">
                    <span className="font-semibold text-gray-300 truncate max-w-[200px]">{item.label}</span>
                    <div className="flex items-center gap-2">
                      <span className="font-extrabold text-white">{item.value.toLocaleString()}</span>
                      <span className="text-[10px] text-gray-400 font-medium">({percentage}%)</span>
                    </div>
                  </div>
                  <div className="w-full h-2.5 bg-black/40 rounded-full overflow-hidden p-0.5 border border-white/5">
                    <div
                      className="h-full rounded-full transition-all duration-500"
                      style={{
                        width: `${Math.max(percentage, 2)}%`,
                        backgroundColor: barColor,
                      }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {type === 'trend-bars' && (
          <div className="mt-6 flex items-end justify-between gap-2 h-36 pt-4 px-2">
            {data.map((item, idx) => {
              const heightPercent = Math.max(Math.round((item.value / maxValue) * 100), 8);
              const barColor = item.color || defaultColors[idx % defaultColors.length];

              return (
                <div key={item.label} className="flex-1 flex flex-col items-center gap-2 group h-full justify-end">
                  <div className="text-[10px] font-bold text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity">
                    {item.value}
                  </div>
                  <div
                    className="w-full rounded-t-lg transition-all duration-300 group-hover:brightness-125"
                    style={{
                      height: `${heightPercent}%`,
                      backgroundColor: barColor,
                    }}
                  />
                  <span className="text-[10px] text-gray-400 font-medium truncate max-w-[50px]">
                    {item.label}
                  </span>
                </div>
              );
            })}
          </div>
        )}

        {type === 'donut-breakdown' && (
          <div className="mt-4 space-y-3">
            {/* Multi-segmented distribution line */}
            <div className="w-full h-4 rounded-full overflow-hidden flex shadow-inner border border-white/10">
              {data.map((item, idx) => {
                const percentage = (item.value / totalSum) * 100;
                const barColor = item.color || defaultColors[idx % defaultColors.length];
                if (percentage <= 0) return null;

                return (
                  <div
                    key={item.label}
                    title={`${item.label}: ${item.value} (${Math.round(percentage)}%)`}
                    style={{ width: `${percentage}%`, backgroundColor: barColor }}
                    className="h-full transition-all"
                  />
                );
              })}
            </div>

            {/* Legend */}
            <div className="grid grid-cols-2 gap-2 pt-2">
              {data.map((item, idx) => {
                const barColor = item.color || defaultColors[idx % defaultColors.length];
                const percentage = Math.round((item.value / totalSum) * 100);

                return (
                  <div key={item.label} className="flex items-center gap-2 text-xs">
                    <span className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ backgroundColor: barColor }} />
                    <span className="text-gray-400 truncate flex-1">{item.label}</span>
                    <span className="font-bold text-white">{percentage}%</span>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>

      <div className="mt-4 pt-3 border-t border-white/5 flex items-center justify-between text-[11px] text-gray-500">
        <span>Total Records</span>
        <span className="font-bold text-gray-300">{totalSum.toLocaleString()}</span>
      </div>
    </div>
  );
};

'use client';

import React from 'react';

interface FilterOption {
  label: string;
  value: string;
}

interface FilterSelect {
  key: string;
  label: string;
  value: string;
  options: FilterOption[];
  onChange: (value: string) => void;
}

interface FilterPanelProps {
  searchQuery?: string;
  onSearchChange?: (query: string) => void;
  searchPlaceholder?: string;
  filters?: FilterSelect[];
  actions?: React.ReactNode;
  onReset?: () => void;
}

export const FilterPanel: React.FC<FilterPanelProps> = ({
  searchQuery,
  onSearchChange,
  searchPlaceholder = 'Search records by keywords...',
  filters = [],
  actions,
  onReset,
}) => {
  return (
    <div className="bg-gray-900/60 backdrop-blur-xl border border-white/10 rounded-2xl p-4 shadow-lg flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
      <div className="flex-1 flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
        {/* Search Input */}
        {onSearchChange && (
          <div className="relative flex-1">
            <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-lg">
              search
            </span>
            <input
              type="text"
              value={searchQuery || ''}
              onChange={(e) => onSearchChange(e.target.value)}
              placeholder={searchPlaceholder}
              className="w-full bg-black/40 border border-white/10 rounded-xl pl-9 pr-4 py-2 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
            />
            {searchQuery && (
              <button
                onClick={() => onSearchChange('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white"
              >
                <span className="material-symbols-outlined text-sm">close</span>
              </button>
            )}
          </div>
        )}

        {/* Dropdown Filters */}
        <div className="flex items-center gap-2 flex-wrap">
          {filters.map((f) => (
            <div key={f.key} className="relative min-w-[130px]">
              <select
                value={f.value}
                onChange={(e) => f.onChange(e.target.value)}
                className="w-full bg-black/40 border border-white/10 rounded-xl px-3 py-2 text-xs text-gray-200 focus:outline-none focus:border-blue-500 appearance-none cursor-pointer pr-7"
              >
                {f.options.map((opt) => (
                  <option key={opt.value} value={opt.value} className="bg-gray-900 text-white">
                    {opt.label}
                  </option>
                ))}
              </select>
              <span className="material-symbols-outlined absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 text-sm pointer-events-none">
                expand_more
              </span>
            </div>
          ))}

          {onReset && (
            <button
              onClick={onReset}
              title="Reset Filters"
              className="p-2 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-gray-300 hover:text-white transition-all text-xs flex items-center gap-1"
            >
              <span className="material-symbols-outlined text-sm">restart_alt</span>
              <span className="hidden sm:inline">Reset</span>
            </button>
          )}
        </div>
      </div>

      {actions && <div className="flex items-center gap-2 self-end md:self-auto">{actions}</div>}
    </div>
  );
};

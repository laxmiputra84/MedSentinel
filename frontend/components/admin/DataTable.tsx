'use client';

import React from 'react';

export interface Column<T> {
  key: string;
  header: string;
  render?: (item: T) => React.ReactNode;
  align?: 'left' | 'center' | 'right';
  width?: string;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  isLoading?: boolean;
  emptyMessage?: string;
  page?: number;
  total?: number;
  limit?: number;
  onPageChange?: (newPage: number) => void;
  onRowClick?: (item: T) => void;
}

export function DataTable<T extends { id?: string | number }>({
  columns,
  data,
  isLoading,
  emptyMessage = 'No records found matching your filters.',
  page = 1,
  total = 0,
  limit = 15,
  onPageChange,
  onRowClick,
}: DataTableProps<T>) {
  const totalPages = Math.ceil(total / limit) || 1;

  return (
    <div className="bg-gray-900/60 backdrop-blur-xl border border-white/10 rounded-2xl overflow-hidden shadow-xl">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs text-gray-300">
          <thead className="bg-white/5 border-b border-white/10 text-gray-400 font-bold uppercase tracking-wider text-[10px]">
            <tr>
              {columns.map((col) => (
                <th
                  key={col.key}
                  className={`px-4 py-3.5 ${col.align === 'right' ? 'text-right' : col.align === 'center' ? 'text-center' : 'text-left'} ${col.width || ''}`}
                >
                  {col.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5 font-medium">
            {isLoading ? (
              <tr>
                <td colSpan={columns.length} className="text-center py-12">
                  <div className="flex flex-col items-center justify-center gap-2">
                    <span className="material-symbols-outlined text-3xl text-blue-400 animate-spin">
                      progress_activity
                    </span>
                    <span className="text-gray-400 text-xs font-semibold">Loading data records...</span>
                  </div>
                </td>
              </tr>
            ) : data.length === 0 ? (
              <tr>
                <td colSpan={columns.length} className="text-center py-12 text-gray-400">
                  <div className="flex flex-col items-center justify-center gap-2">
                    <span className="material-symbols-outlined text-3xl text-gray-500">inbox</span>
                    <span className="text-gray-400 text-xs">{emptyMessage}</span>
                  </div>
                </td>
              </tr>
            ) : (
              data.map((item, index) => (
                <tr
                  key={item.id ? String(item.id) : index}
                  onClick={() => onRowClick && onRowClick(item)}
                  className={`transition-colors ${
                    onRowClick ? 'cursor-pointer hover:bg-white/5' : 'hover:bg-white/[0.02]'
                  }`}
                >
                  {columns.map((col) => (
                    <td
                      key={col.key}
                      className={`px-4 py-3.5 align-middle ${
                        col.align === 'right'
                          ? 'text-right'
                          : col.align === 'center'
                          ? 'text-center'
                          : 'text-left'
                      }`}
                    >
                      {col.render
                        ? col.render(item)
                        : (item as any)[col.key] !== undefined && (item as any)[col.key] !== null
                        ? String((item as any)[col.key])
                        : '—'}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      {total > 0 && onPageChange && (
        <div className="px-4 py-3 border-t border-white/10 bg-white/[0.02] flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-gray-400">
          <div>
            Showing <span className="font-semibold text-white">{(page - 1) * limit + 1}</span> to{' '}
            <span className="font-semibold text-white">{Math.min(page * limit, total)}</span> of{' '}
            <span className="font-semibold text-white">{total}</span> entries
          </div>

          <div className="flex items-center gap-1.5">
            <button
              onClick={() => onPageChange(page - 1)}
              disabled={page <= 1}
              className="px-2.5 py-1 rounded-lg border border-white/10 text-gray-300 hover:text-white hover:bg-white/5 disabled:opacity-30 disabled:pointer-events-none transition-all flex items-center"
            >
              <span className="material-symbols-outlined text-sm">chevron_left</span>
              <span className="text-[11px]">Prev</span>
            </button>

            <span className="px-3 py-1 bg-white/5 rounded-lg text-white font-bold text-[11px]">
              {page} / {totalPages}
            </span>

            <button
              onClick={() => onPageChange(page + 1)}
              disabled={page >= totalPages}
              className="px-2.5 py-1 rounded-lg border border-white/10 text-gray-300 hover:text-white hover:bg-white/5 disabled:opacity-30 disabled:pointer-events-none transition-all flex items-center"
            >
              <span className="text-[11px]">Next</span>
              <span className="material-symbols-outlined text-sm">chevron_right</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

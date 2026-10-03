'use client';

import React from 'react';

interface ConfirmActionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  description: string;
  confirmText?: string;
  cancelText?: string;
  isDestructive?: boolean;
  isLoading?: boolean;
}

export const ConfirmActionModal: React.FC<ConfirmActionModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  title,
  description,
  confirmText = 'Confirm Action',
  cancelText = 'Cancel',
  isDestructive = false,
  isLoading = false,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="fixed inset-0 bg-black/80 backdrop-blur-sm" onClick={onClose} />

      <div className="relative bg-gray-900 border border-white/15 rounded-2xl max-w-md w-full p-6 shadow-2xl z-10 space-y-4 animate-in fade-in zoom-in-95 duration-200">
        <div className="flex items-start gap-3.5">
          <div
            className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${
              isDestructive ? 'bg-red-500/20 text-red-400' : 'bg-blue-500/20 text-blue-400'
            }`}
          >
            <span className="material-symbols-outlined text-xl">
              {isDestructive ? 'warning' : 'info'}
            </span>
          </div>
          <div>
            <h3 className="text-base font-bold text-white font-['Manrope']">{title}</h3>
            <p className="text-xs text-gray-300 mt-1 leading-relaxed">{description}</p>
          </div>
        </div>

        <div className="flex items-center justify-end gap-3 pt-3 border-t border-white/10">
          <button
            type="button"
            onClick={onClose}
            disabled={isLoading}
            className="px-4 py-2 rounded-xl text-xs font-semibold text-gray-300 hover:text-white bg-white/5 hover:bg-white/10 border border-white/10 transition-all"
          >
            {cancelText}
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={isLoading}
            className={`px-4 py-2 rounded-xl text-xs font-semibold text-white transition-all flex items-center gap-1.5 shadow-lg ${
              isDestructive
                ? 'bg-gradient-to-r from-red-600 to-rose-700 hover:from-red-500 hover:to-rose-600 shadow-red-500/20'
                : 'bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 shadow-blue-500/20'
            } disabled:opacity-50`}
          >
            {isLoading && (
              <span className="material-symbols-outlined text-sm animate-spin">progress_activity</span>
            )}
            <span>{confirmText}</span>
          </button>
        </div>
      </div>
    </div>
  );
};

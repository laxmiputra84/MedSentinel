'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function DocumentsRedirect() {
  const router = useRouter();
  useEffect(() => {
    router.replace('/medical-vault');
  }, [router]);

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center text-slate-400">
      <div className="flex items-center gap-2">
        <div className="w-5 h-5 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
        <span>Navigating to Medical Documents Vault...</span>
      </div>
    </div>
  );
}

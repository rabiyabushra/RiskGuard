import React from 'react';
import { Loader2 } from 'lucide-react';

export default function Loading({ message = 'Loading RiskGuard intelligence...' }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 space-y-3">
      <Loader2 className="w-8 h-8 text-sky-400 animate-spin" />
      <p className="text-sm text-slate-400 animate-pulse">{message}</p>
    </div>
  );
}

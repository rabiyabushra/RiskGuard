import React from 'react';

export default function StatCard({ title, value, subtitle, icon: Icon, color = 'sky', highlight = false }) {
  const colorMap = {
    sky: 'from-sky-500/10 to-transparent border-sky-500/20 text-sky-400',
    emerald: 'from-emerald-500/10 to-transparent border-emerald-500/20 text-emerald-400',
    yellow: 'from-yellow-500/10 to-transparent border-yellow-500/20 text-yellow-400',
    orange: 'from-orange-500/10 to-transparent border-orange-500/20 text-orange-400',
    rose: 'from-rose-500/10 to-transparent border-rose-500/20 text-rose-400',
    indigo: 'from-indigo-500/10 to-transparent border-indigo-500/20 text-indigo-400',
  };

  const selectedColor = colorMap[color] || colorMap.sky;

  return (
    <div className={`bg-slate-800/60 rounded-xl p-5 border backdrop-blur transition-all duration-200 hover:border-slate-600/80 bg-gradient-to-b ${selectedColor}`}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">{title}</span>
        {Icon && (
          <div className="p-2 rounded-lg bg-slate-800 border border-slate-700/60">
            <Icon className="w-5 h-5" />
          </div>
        )}
      </div>
      <div className="mt-3">
        <div className="text-2xl sm:text-3xl font-bold text-white tracking-tight">{value}</div>
        {subtitle && <p className="text-xs text-slate-400 mt-1">{subtitle}</p>}
      </div>
    </div>
  );
}

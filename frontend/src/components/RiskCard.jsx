import React from 'react';
import { AlertTriangle, ShieldCheck, AlertCircle } from 'lucide-react';

export default function RiskCard({ level, count, percentage, onClick, isSelected = false }) {
  const configs = {
    HIGH: {
      title: 'High Risk Projects',
      color: 'border-orange-500/40 bg-orange-500/10 text-orange-400',
      badge: 'bg-orange-500/20 text-orange-300 border-orange-500/30',
      icon: AlertTriangle,
      description: 'Critical delay probability (≥ 65%). Immediate intervention advised.'
    },
    MEDIUM: {
      title: 'Medium Risk Projects',
      color: 'border-yellow-500/40 bg-yellow-500/10 text-yellow-400',
      badge: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30',
      icon: AlertCircle,
      description: 'Moderate risk tier (35% - 65%). On active watchlist.'
    },
    LOW: {
      title: 'Low Risk Projects',
      color: 'border-emerald-500/40 bg-emerald-500/10 text-emerald-400',
      badge: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
      icon: ShieldCheck,
      description: 'Healthy trajectory (< 35%). Minimal variance from schedule.'
    }
  };

  const config = configs[level] || configs.MEDIUM;
  const Icon = config.icon;

  return (
    <div
      onClick={onClick}
      className={`rounded-xl p-5 border transition-all duration-200 cursor-pointer ${config.color} ${
        isSelected ? 'ring-2 ring-sky-400 scale-[1.02]' : 'hover:scale-[1.01]'
      }`}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Icon className="w-5 h-5" />
          <span className="font-semibold text-sm uppercase tracking-wider">{level} RISK</span>
        </div>
        <span className={`text-xs px-2 py-0.5 rounded-full border font-mono ${config.badge}`}>
          {percentage}%
        </span>
      </div>
      <div className="mt-4">
        <div className="text-3xl font-bold text-white tracking-tight">{count}</div>
        <p className="text-xs text-slate-300/80 mt-1">{config.description}</p>
      </div>
    </div>
  );
}

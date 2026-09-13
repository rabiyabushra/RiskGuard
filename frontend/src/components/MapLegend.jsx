import React from 'react';
import { riskColors } from '@gis/maps/riskColors';

export default function MapLegend() {
  const legendItems = [
    { label: 'High Risk (Score ≥ 65)', color: riskColors.high, desc: 'Critical delay trajectory' },
    { label: 'Medium Risk (35 ≤ Score < 65)', color: riskColors.medium, desc: 'Watchlist / elevated risk' },
    { label: 'Low Risk (Score < 35)', color: riskColors.low, desc: 'On-track execution' },
  ];

  return (
    <div className="bg-slate-900/90 backdrop-blur-md border border-slate-700/80 rounded-xl p-3.5 shadow-2xl text-xs space-y-2 max-w-xs">
      <div className="font-semibold text-slate-200 border-b border-slate-700/60 pb-1.5 flex items-center justify-between">
        <span>Portfolio Risk Legend</span>
        <span className="text-[10px] text-slate-400 font-mono">Calibrated Tiers</span>
      </div>
      <div className="space-y-1.5">
        {legendItems.map((item, idx) => (
          <div key={idx} className="flex items-center space-x-2.5">
            <span
              className="w-3.5 h-3.5 rounded-full border border-white/20 shrink-0 shadow-sm"
              style={{ backgroundColor: item.color }}
            />
            <div className="flex-1">
              <p className="font-medium text-slate-200">{item.label}</p>
              <p className="text-[10px] text-slate-400">{item.desc}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

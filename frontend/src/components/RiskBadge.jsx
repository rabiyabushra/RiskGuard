import React from 'react';
import { getRiskBadgeClasses } from '../utils/riskUtils';

export default function RiskBadge({ category, score = null, size = 'md' }) {
  const cat = (category || 'UNKNOWN').toUpperCase();
  const badgeClasses = getRiskBadgeClasses(cat);
  
  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-xs px-2.5 py-1',
    lg: 'text-sm px-3.5 py-1.5 font-semibold'
  }[size] || 'text-xs px-2.5 py-1';

  return (
    <span className={`inline-flex items-center space-x-1.5 rounded-full font-medium ${badgeClasses} ${sizeClasses}`}>
      <span className="w-1.5 h-1.5 rounded-full bg-current" />
      <span>{cat} RISK</span>
      {score !== null && score !== undefined && (
        <span className="opacity-75 font-mono text-[0.85em]">({Number(score).toFixed(1)})</span>
      )}
    </span>
  );
}

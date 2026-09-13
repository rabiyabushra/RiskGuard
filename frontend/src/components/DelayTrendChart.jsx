import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend
} from 'recharts';

export default function DelayTrendChart({ projects = [] }) {
  // Aggregate real backend data by sector
  const sectorMap = {};

  projects.forEach((p) => {
    const sector = p.sector || 'Other';
    if (!sectorMap[sector]) {
      sectorMap[sector] = {
        sector,
        total: 0,
        totalRiskScore: 0,
        totalDelayProb: 0,
        highRiskCount: 0,
      };
    }
    sectorMap[sector].total += 1;
    sectorMap[sector].totalRiskScore += Number(p.risk_score || 0);
    sectorMap[sector].totalDelayProb += Number(p.delay_probability || 0);
    if ((p.risk_category || '').toUpperCase() === 'HIGH') {
      sectorMap[sector].highRiskCount += 1;
    }
  });

  const chartData = Object.values(sectorMap)
    .filter((s) => s.total >= 1)
    .map((s) => ({
      sector: s.sector.length > 18 ? s.sector.slice(0, 16) + '...' : s.sector,
      fullSector: s.sector,
      avgRiskScore: Number((s.totalRiskScore / s.total).toFixed(1)),
      avgDelayProb: Number(((s.totalDelayProb / s.total) * 100).toFixed(1)),
      projectsCount: s.total,
      highRiskCount: s.highRiskCount,
    }))
    .sort((a, b) => b.avgRiskScore - a.avgRiskScore)
    .slice(0, 8); // Top 8 sectors

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const d = payload[0].payload;
      return (
        <div className="bg-slate-800 border border-slate-700 p-3 rounded-lg shadow-xl text-xs space-y-1">
          <p className="font-semibold text-white">{d.fullSector}</p>
          <p className="text-slate-300">Total Projects: <span className="font-mono text-sky-400">{d.projectsCount}</span></p>
          <p className="text-slate-300">Avg Risk Score: <span className="font-mono text-amber-400">{d.avgRiskScore} / 100</span></p>
          <p className="text-slate-300">Avg Delay Probability: <span className="font-mono text-rose-400">{d.avgDelayProb}%</span></p>
        </div>
      );
    }
    return null;
  };

  if (chartData.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-xs text-slate-500">
        No sector project data available.
      </div>
    );
  }

  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 25 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.5} />
          <XAxis
            dataKey="sector"
            stroke="#94a3b8"
            fontSize={11}
            angle={-25}
            textAnchor="end"
            interval={0}
          />
          <YAxis stroke="#94a3b8" fontSize={11} domain={[0, 100]} />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            verticalAlign="top"
            wrapperStyle={{ paddingBottom: '10px' }}
            formatter={(val) => <span className="text-xs text-slate-300">{val}</span>}
          />
          <Bar dataKey="avgRiskScore" name="Avg Risk Score (0-100)" fill="#f97316" radius={[4, 4, 0, 0]} />
          <Bar dataKey="avgDelayProb" name="Delay Probability (%)" fill="#0ea5e9" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

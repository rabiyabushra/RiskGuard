import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import { riskColors } from '@gis/maps/riskColors';

export default function RiskChart({ highCount = 0, mediumCount = 0, lowCount = 0 }) {
  const data = [
    { name: 'High Risk', value: highCount, color: riskColors.high },
    { name: 'Medium Risk', value: mediumCount, color: riskColors.medium },
    { name: 'Low Risk', value: lowCount, color: riskColors.low },
  ].filter((d) => d.value > 0);

  const total = highCount + mediumCount + lowCount;

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const item = payload[0];
      const pct = total > 0 ? ((item.value / total) * 100).toFixed(1) : 0;
      return (
        <div className="bg-slate-800 border border-slate-700 p-2.5 rounded-lg shadow-xl text-xs">
          <p className="font-semibold text-white">{item.name}</p>
          <p className="text-slate-300 mt-1">
            <span className="font-mono font-bold text-sky-400">{item.value.toLocaleString()}</span> projects ({pct}%)
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={55}
            outerRadius={85}
            paddingAngle={3}
            dataKey="value"
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} stroke="#1e293b" strokeWidth={2} />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
          <Legend
            verticalAlign="bottom"
            formatter={(val) => <span className="text-xs text-slate-300">{val}</span>}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}

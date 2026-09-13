import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  ReferenceLine
} from 'recharts';

export default function SHAPChart({ positiveFactors = [], negativeFactors = [] }) {
  // Combine positive and negative factors
  const formattedPositive = positiveFactors.map((item) => ({
    name: formatFeatureLabel(item.feature),
    rawFeature: item.feature,
    value: Number(item.shap_value || 0),
    isPositive: true,
  }));

  const formattedNegative = negativeFactors.map((item) => ({
    name: formatFeatureLabel(item.feature),
    rawFeature: item.feature,
    value: Number(item.shap_value || 0),
    isPositive: false,
  }));

  // Sort by absolute attribution magnitude
  const chartData = [...formattedPositive, ...formattedNegative].sort(
    (a, b) => Math.abs(b.value) - Math.abs(a.value)
  );

  function formatFeatureLabel(feat) {
    if (!feat) return '';
    return feat
      .replace('sector_', 'Sector: ')
      .replace('state_std_', 'State: ')
      .replace(/_/g, ' ')
      .replace(/\b\w/g, (c) => c.toUpperCase());
  }

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-slate-800 border border-slate-700 p-3 rounded-lg shadow-xl text-xs space-y-1.5 max-w-xs">
          <p className="font-semibold text-white">{data.name}</p>
          <div className="flex items-center space-x-2">
            <span className="text-slate-400">SHAP Attribution:</span>
            <span className={`font-mono font-bold ${data.isPositive ? 'text-amber-400' : 'text-emerald-400'}`}>
              {data.value > 0 ? `+${data.value.toFixed(4)}` : data.value.toFixed(4)}
            </span>
          </div>
          <p className={`text-[11px] ${data.isPositive ? 'text-amber-300/80' : 'text-emerald-300/80'}`}>
            {data.isPositive
              ? 'Contributing toward HIGHER predicted delay risk.'
              : 'Contributing toward LOWER predicted delay risk.'}
          </p>
        </div>
      );
    }
    return null;
  };

  if (!chartData.length) {
    return (
      <div className="py-12 text-center text-xs text-slate-500">
        No SHAP attribution factors available for this project.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between text-xs px-1">
        <span className="text-emerald-400 flex items-center space-x-1">
          <span className="w-2.5 h-2.5 rounded bg-emerald-500 inline-block" />
          <span>Reduces Delay Risk (Negative SHAP)</span>
        </span>
        <span className="text-amber-400 flex items-center space-x-1">
          <span className="w-2.5 h-2.5 rounded bg-amber-500 inline-block" />
          <span>Increases Delay Risk (Positive SHAP)</span>
        </span>
      </div>

      <div className="h-80 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            layout="vertical"
            data={chartData}
            margin={{ top: 10, right: 30, left: 120, bottom: 10 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.5} horizontal={false} />
            <XAxis
              type="number"
              stroke="#94a3b8"
              fontSize={11}
              domain={['dataMin - 0.1', 'dataMax + 0.1']}
              tickFormatter={(v) => v.toFixed(2)}
            />
            <YAxis
              type="category"
              dataKey="name"
              stroke="#94a3b8"
              fontSize={11}
              tickLine={false}
              width={140}
            />
            <Tooltip content={<CustomTooltip />} />
            <ReferenceLine x={0} stroke="#64748b" strokeWidth={1.5} />
            <Bar dataKey="value" radius={[4, 4, 4, 4]}>
              {chartData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={entry.value >= 0 ? '#f97316' : '#22c55e'}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

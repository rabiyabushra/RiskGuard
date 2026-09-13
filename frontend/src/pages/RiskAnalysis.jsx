import React, { useState, useEffect } from 'react';
import { 
  Activity, 
  Sliders, 
  Sparkles, 
  Layers, 
  TrendingUp, 
  AlertTriangle, 
  CheckCircle2, 
  ArrowRight,
  HelpCircle,
  Play
} from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';

import api from '../services/api';
import RiskBadge from '../components/RiskBadge';
import RecommendationCard from '../components/RecommendationCard';
import Loading from '../components/Loading';
import ErrorMessage from '../components/ErrorMessage';
import { riskColors } from '../utils/riskUtils';

export default function RiskAnalysis() {
  // Global SHAP state
  const [globalShap, setGlobalShap] = useState(null);
  const [loadingShap, setLoadingShap] = useState(true);
  const [shapError, setShapError] = useState(null);

  // Simulator state
  const [simForm, setSimForm] = useState({
    project_name: 'Simulated National Highway Expressway Corridor',
    sector: 'Road Transport and Highways',
    state: 'Maharashtra',
    agency: 'NHAI',
    cost_original: 1200,
    cost_revised: 1550,
    physical_progress: 35.0,
    expenditure: 450,
    delay_months: 18,
  });

  const [simulating, setSimulating] = useState(false);
  const [simResult, setSimResult] = useState(null);
  const [simRecommendations, setSimRecommendations] = useState(null);
  const [simError, setSimError] = useState(null);

  useEffect(() => {
    async function fetchGlobalSHAP() {
      setLoadingShap(true);
      try {
        const res = await api.getGlobalSHAP();
        setGlobalShap(res);
      } catch (err) {
        console.error('Failed to load global SHAP:', err);
        setShapError(err.message || 'Global SHAP data unavailable');
      } finally {
        setLoadingShap(false);
      }
    }
    fetchGlobalSHAP();
  }, []);

  const handleSimulate = async (e) => {
    e.preventDefault();
    setSimulating(true);
    setSimError(null);
    setSimResult(null);
    setSimRecommendations(null);

    try {
      // 1. Run live prediction on Member 5 ML API
      const predPayload = {
        project_name: simForm.project_name,
        sector: simForm.sector,
        state: simForm.state,
        agency: simForm.agency,
        original_cost: parseFloat(simForm.cost_original) || 1000,
        revised_cost: parseFloat(simForm.cost_revised) || 1200,
        physical_progress: parseFloat(simForm.physical_progress) || 30,
        expenditure: parseFloat(simForm.expenditure) || 400,
        planned_duration_days: Math.max(1, (parseInt(simForm.delay_months) || 12) * 30),
      };

      const predRes = await api.predictDelay(predPayload);
      setSimResult(predRes);

      // 2. Fetch Gemini recommendations for the simulated project
      try {
        const recRes = await api.getCustomRecommendations({
          project_id: 'SIMULATED-01',
          project_name: simForm.project_name,
          state: simForm.state,
          sector: simForm.sector,
          delay_probability: predRes.delay_probability,
          risk_category: predRes.risk_category,
          revised_cost: predPayload.revised_cost,
          original_cost: predPayload.original_cost,
          physical_progress: predPayload.physical_progress,
        });
        setSimRecommendations(recRes.recommendations || recRes);
      } catch (recErr) {
        console.warn('Simulated recommendations error:', recErr);
      }

    } catch (err) {
      console.error('Simulation error:', err);
      setSimError(err.message || 'Failed to simulate project risk.');
    } finally {
      setSimulating(false);
    }
  };

  // Prepare Global SHAP chart data
  const chartData = (Array.isArray(globalShap) ? globalShap : []).map(f => ({
    name: (f.feature || f.name || '').replace(/_/g, ' '),
    importance: parseFloat(f.mean_abs_shap || f.importance || f.value || 0)
  }));

  return (
    <div className="space-y-8 pb-16 max-w-7xl mx-auto">
      {/* Header */}
      <div>
        <div className="flex items-center space-x-2">
          <Activity className="w-6 h-6 text-sky-400" />
          <h1 className="text-2xl font-bold text-white tracking-tight">
            Risk Analysis & Explainable AI Lab
          </h1>
        </div>
        <p className="text-xs text-slate-400 mt-1 max-w-3xl">
          Inspect portfolio-level explainability drivers derived via SHAP (SHapley Additive exPlanations) and run interactive real-time What-If scenario simulations through the trained Machine Learning pipeline.
        </p>
      </div>

      {/* Top Section: Global Feature Importance */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-slate-800 pb-4">
          <div>
            <h2 className="text-base font-semibold text-white flex items-center space-x-2">
              <Layers className="w-4 h-4 text-sky-400" />
              <span>Global SHAP Feature Importance Ranking</span>
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Identifies which parameters exert the strongest mathematical influence on infrastructure delay across India.
            </p>
          </div>
          <span className="px-2.5 py-1 rounded-full bg-slate-800 text-sky-400 text-xs font-mono font-medium self-start sm:self-auto">
            Model: Best Trained XGBoost Classifier
          </span>
        </div>

        {loadingShap ? (
          <div className="py-12 flex justify-center">
            <Loading message="Computing global SHAP feature attributions..." />
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
            <div className="lg:col-span-8 h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={chartData}
                  layout="vertical"
                  margin={{ top: 10, right: 30, left: 120, bottom: 5 }}
                >
                  <XAxis type="number" stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                  <YAxis
                    type="category"
                    dataKey="name"
                    stroke="#64748b"
                    tick={{ fill: '#cbd5e1', fontSize: 11 }}
                    width={110}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0f172a',
                      borderColor: '#334155',
                      borderRadius: '0.5rem',
                      color: '#f8fafc',
                      fontSize: '12px'
                    }}
                    formatter={(val) => [`${Number(val).toFixed(4)} Mean |SHAP|`, 'Importance']}
                  />
                  <Bar dataKey="importance" radius={[0, 6, 6, 0]}>
                    {chartData.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={index === 0 ? '#38bdf8' : index === 1 ? '#60a5fa' : index === 2 ? '#818cf8' : '#a78bfa'}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="lg:col-span-4 space-y-3 bg-slate-950/60 p-4 rounded-xl border border-slate-800 text-xs text-slate-300">
              <h3 className="font-semibold text-white flex items-center space-x-1.5">
                <HelpCircle className="w-4 h-4 text-sky-400" />
                <span>Interpreting Global SHAP</span>
              </h3>
              <p className="text-slate-400 leading-relaxed text-[11px]">
                Features at the top have the largest average magnitude on shifting predictions. Projects with lagging <strong>physical progress</strong> relative to elapsed time and high <strong>cost overrun ratios</strong> consistently receive severe delay penalties.
              </p>
              <div className="pt-2 border-t border-slate-800 space-y-1 text-[11px]">
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Top Leading Indicator:</span>
                  <span className="font-mono text-sky-400 font-medium">Physical Progress (%)</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Top Financial Indicator:</span>
                  <span className="font-mono text-amber-400 font-medium">Cost Overrun Ratio</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Bottom Section: Live What-If Scenario Simulator */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
        <div className="flex items-center space-x-2 border-b border-slate-800 pb-4">
          <Sliders className="w-5 h-5 text-indigo-400" />
          <div>
            <h2 className="text-base font-semibold text-white">Interactive Scenario Simulator (What-If Engine)</h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Modify infrastructure project parameters below to evaluate real-time delay probability shifts and test mitigation interventions.
            </p>
          </div>
        </div>

        <form onSubmit={handleSimulate} className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
            {/* Project Name */}
            <div className="sm:col-span-2">
              <label className="block text-slate-300 font-medium mb-1">Project Name</label>
              <input
                type="text"
                value={simForm.project_name}
                onChange={(e) => setSimForm({ ...simForm, project_name: e.target.value })}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-sky-500"
                required
              />
            </div>

            {/* Sector */}
            <div>
              <label className="block text-slate-300 font-medium mb-1">Sector</label>
              <select
                value={simForm.sector}
                onChange={(e) => setSimForm({ ...simForm, sector: e.target.value })}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-sky-500"
              >
                <option value="Road Transport and Highways">Road Transport and Highways</option>
                <option value="Railways">Railways</option>
                <option value="Power">Power</option>
                <option value="Petroleum">Petroleum</option>
                <option value="Coal">Coal</option>
                <option value="Telecommunications">Telecommunications</option>
                <option value="Shipping and Ports">Shipping and Ports</option>
                <option value="Civil Aviation">Civil Aviation</option>
              </select>
            </div>

            {/* State */}
            <div>
              <label className="block text-slate-300 font-medium mb-1">State</label>
              <select
                value={simForm.state}
                onChange={(e) => setSimForm({ ...simForm, state: e.target.value })}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-sky-500"
              >
                <option value="Maharashtra">Maharashtra</option>
                <option value="Uttar Pradesh">Uttar Pradesh</option>
                <option value="Gujarat">Gujarat</option>
                <option value="Karnataka">Karnataka</option>
                <option value="Tamil Nadu">Tamil Nadu</option>
                <option value="Bihar">Bihar</option>
                <option value="West Bengal">West Bengal</option>
                <option value="Madhya Pradesh">Madhya Pradesh</option>
                <option value="Rajasthan">Rajasthan</option>
                <option value="Andhra Pradesh">Andhra Pradesh</option>
                <option value="Odisha">Odisha</option>
                <option value="Assam">Assam</option>
              </select>
            </div>

            {/* Original Cost */}
            <div>
              <label className="block text-slate-300 font-medium mb-1">Original Cost (₹ Cr)</label>
              <input
                type="number"
                value={simForm.cost_original}
                onChange={(e) => setSimForm({ ...simForm, cost_original: e.target.value })}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-sky-500 font-mono"
                required
              />
            </div>

            {/* Revised Cost */}
            <div>
              <label className="block text-slate-300 font-medium mb-1">Revised Cost (₹ Cr)</label>
              <input
                type="number"
                value={simForm.cost_revised}
                onChange={(e) => setSimForm({ ...simForm, cost_revised: e.target.value })}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-sky-500 font-mono"
                required
              />
            </div>

            {/* Physical Progress */}
            <div>
              <label className="block text-slate-300 font-medium mb-1">Physical Progress (%)</label>
              <input
                type="number"
                step="0.1"
                min="0"
                max="100"
                value={simForm.physical_progress}
                onChange={(e) => setSimForm({ ...simForm, physical_progress: e.target.value })}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-sky-500 font-mono"
                required
              />
            </div>

            {/* Expenditure */}
            <div>
              <label className="block text-slate-300 font-medium mb-1">Expended So Far (₹ Cr)</label>
              <input
                type="number"
                value={simForm.expenditure}
                onChange={(e) => setSimForm({ ...simForm, expenditure: e.target.value })}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-sky-500 font-mono"
              />
            </div>
          </div>

          <div className="flex items-center justify-between pt-2">
            <span className="text-xs text-slate-500">
              Changes feed directly into the backend XGBoost model and Gemini LLM reasoning agent.
            </span>
            <button
              type="submit"
              disabled={simulating}
              className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-sky-600 to-indigo-600 hover:from-sky-500 hover:to-indigo-500 text-white text-xs font-semibold shadow-lg shadow-sky-500/20 transition-all active:scale-95 disabled:opacity-50"
            >
              <Play className={`w-3.5 h-3.5 fill-current ${simulating ? 'animate-spin' : ''}`} />
              <span>{simulating ? 'Computing Predictions...' : 'Run Simulation'}</span>
            </button>
          </div>
        </form>

        {simError && (
          <ErrorMessage
            title="Simulation Failed"
            message={simError}
          />
        )}

        {/* Simulation Output Card */}
        {simResult && (
          <div className="mt-8 space-y-6 pt-6 border-t border-slate-800">
            <div className="bg-slate-950 p-6 rounded-2xl border border-sky-500/30 shadow-2xl space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <span className="text-xs font-medium text-sky-400">Live ML Pipeline Output</span>
                  <h3 className="text-lg font-bold text-white mt-0.5">{simForm.project_name}</h3>
                </div>
                <div className="flex items-center space-x-3">
                  <RiskBadge category={simResult.risk_category} score={simResult.risk_score} size="lg" />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-3 border-t border-slate-800/80">
                <div className="bg-slate-900/80 p-3.5 rounded-xl border border-slate-800">
                  <span className="text-slate-400 text-xs block">Delay Probability</span>
                  <span className="text-xl font-bold font-mono text-sky-400 mt-1 block">
                    {(Number(simResult.delay_probability || 0) * 100).toFixed(1)}%
                  </span>
                  <span className="text-[11px] text-slate-500">Likelihood of schedule overrun</span>
                </div>

                <div className="bg-slate-900/80 p-3.5 rounded-xl border border-slate-800">
                  <span className="text-slate-400 text-xs block">Computed Risk Score</span>
                  <span className="text-xl font-bold font-mono text-white mt-1 block">
                    {Number(simResult.risk_score || 50).toFixed(1)} / 100
                  </span>
                  <span className="text-[11px] text-slate-500">Weighted multi-factor score</span>
                </div>

                <div className="bg-slate-900/80 p-3.5 rounded-xl border border-slate-800">
                  <span className="text-slate-400 text-xs block">Risk Classification</span>
                  <span className="text-xl font-bold font-mono text-amber-400 mt-1 block">
                    {simResult.risk_category || 'MEDIUM'}
                  </span>
                  <span className="text-[11px] text-slate-500">Tier designation</span>
                </div>
              </div>
            </div>

            {/* Simulated Recommendations */}
            {simRecommendations && (
              <div className="space-y-3">
                <h4 className="text-sm font-semibold text-white flex items-center space-x-2">
                  <Sparkles className="w-4 h-4 text-indigo-400" />
                  <span>Gemini Recommendations for Simulated Scenario</span>
                </h4>
                <RecommendationCard
                  projectId="SIMULATED"
                  recommendations={simRecommendations}
                  riskLevel={simResult.risk_category}
                />
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

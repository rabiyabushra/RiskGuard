import React, { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { 
  Building2, 
  AlertTriangle, 
  TrendingUp, 
  Activity, 
  RefreshCw, 
  Map as MapIcon, 
  ArrowRight,
  ShieldAlert,
  Calendar,
  Layers
} from 'lucide-react';

import api from '../services/api';
import StatCard from '../components/StatCard';
import RiskCard from '../components/RiskCard';
import RiskChart from '../components/RiskChart';
import DelayTrendChart from '../components/DelayTrendChart';
import RiskMap from '../components/RiskMap';
import ProjectTable from '../components/ProjectTable';
import Loading from '../components/Loading';
import ErrorMessage from '../components/ErrorMessage';
import { formatCurrency, formatPercent, formatNumber } from '../utils/riskUtils';

export default function Dashboard() {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  const fetchDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      // Fetch master project dataset with ML risk metrics from Member 5 backend
      const res = await api.getProjects({ limit: 250 });
      const projectList = res.projects || [];
      setProjects(projectList);
      setLastUpdated(new Date().toLocaleTimeString());
    } catch (err) {
      console.error('Failed to load projects from backend:', err);
      setError(err.message || 'Unable to connect to RiskGuard backend API at http://localhost:8000');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  // Compute portfolio-level aggregates
  const stats = useMemo(() => {
    if (!projects.length) {
      return {
        total: 0,
        high: 0,
        medium: 0,
        low: 0,
        avgRisk: 0,
        avgDelayProb: 0,
        totalCost: 0,
      };
    }

    let high = 0;
    let medium = 0;
    let low = 0;
    let sumRisk = 0;
    let sumDelayProb = 0;
    let sumCost = 0;

    projects.forEach(p => {
      const cat = (p.risk_category || '').toUpperCase();
      if (cat === 'HIGH' || cat === 'CRITICAL') high++;
      else if (cat === 'LOW') low++;
      else medium++;

      sumRisk += Number(p.risk_score || 50);
      sumDelayProb += Number(p.delay_probability || 0.5);
      sumCost += Number(p.revised_cost || p.original_cost || 0);
    });

    return {
      total: projects.length,
      high,
      medium,
      low,
      avgRisk: (sumRisk / projects.length).toFixed(1),
      avgDelayProb: ((sumDelayProb / projects.length) * 100).toFixed(1),
      totalCost: sumCost,
    };
  }, [projects]);

  if (loading && !projects.length) {
    return (
      <div className="min-h-[70vh] flex items-center justify-center">
        <Loading message="Connecting to RiskGuard Intelligence Backend & Loading Infrastructure Models..." />
      </div>
    );
  }

  if (error && !projects.length) {
    return (
      <div className="max-w-4xl mx-auto py-12 px-4">
        <ErrorMessage
          title="Backend Connection Failed"
          message={`Could not load project delay data from the RiskGuard API (${error}). Ensure the FastAPI server is running on port 8000.`}
          onRetry={fetchDashboardData}
        />
      </div>
    );
  }

  return (
    <div className="space-y-8 pb-12">
      {/* Top Banner & Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 bg-gradient-to-r from-slate-900 via-slate-900 to-slate-800 p-6 rounded-2xl border border-slate-800 shadow-xl">
        <div>
          <div className="inline-flex items-center space-x-2 px-2.5 py-1 rounded-full bg-sky-500/10 border border-sky-500/30 text-sky-400 text-xs font-medium mb-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span>PAIMANA Live Multi-Sector Delay Pipeline Active</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
            Infrastructure Delay Intelligence Dashboard
          </h1>
          <p className="text-sm text-slate-400 mt-1 max-w-2xl">
            Real-time machine learning predictions, SHAP feature attributions, and Gemini mitigation recommendations for infrastructure project delays.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          {lastUpdated && (
            <span className="text-xs text-slate-400 hidden sm:inline">
              Updated: <strong className="text-slate-200">{lastUpdated}</strong>
            </span>
          )}
          <button
            onClick={fetchDashboardData}
            disabled={loading}
            className="inline-flex items-center space-x-2 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 transition-all active:scale-95 disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 text-sky-400 ${loading ? 'animate-spin' : ''}`} />
            <span>Sync Data</span>
          </button>
        </div>
      </div>

      {/* Top Stat Cards (4 Cards) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Monitored Projects"
          value={formatNumber(stats.total)}
          subtitle="PAIMANA Master Infrastructure"
          icon={Building2}
          color="sky"
        />
        <StatCard
          title="High Risk Projects"
          value={formatNumber(stats.high)}
          subtitle={`${((stats.high / (stats.total || 1)) * 100).toFixed(0)}% of total portfolio`}
          icon={AlertTriangle}
          color="amber"
        />
        <StatCard
          title="Avg Delay Probability"
          value={`${stats.avgDelayProb}%`}
          subtitle="Trained XGBoost inference"
          icon={TrendingUp}
          color="rose"
        />
        <StatCard
          title="Portfolio Risk Index"
          value={`${stats.avgRisk}/100`}
          subtitle="Comprehensive risk metric"
          icon={Activity}
          color="indigo"
        />
      </div>

      {/* Risk Tier Breakdown Cards (3 Cards) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <RiskCard
          level="HIGH"
          count={stats.high}
          total={stats.total}
          subtitle="Likely >12 mo delay or high cost overrun"
        />
        <RiskCard
          level="MEDIUM"
          count={stats.medium}
          total={stats.total}
          subtitle="Moderate delay risks or acquisition bottlenecks"
        />
        <RiskCard
          level="LOW"
          count={stats.low}
          total={stats.total}
          subtitle="On-track or minimal schedule variance"
        />
      </div>

      {/* GIS Map & Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Leaflet GIS Map Container (7 cols) */}
        <div className="lg:col-span-7 flex flex-col space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <MapIcon className="w-4 h-4 text-sky-400" />
              <h2 className="text-base font-semibold text-white">Geographic Risk Distribution</h2>
            </div>
            <Link
              to="/map"
              className="inline-flex items-center space-x-1 text-xs text-sky-400 hover:text-sky-300 transition-colors"
            >
              <span>Fullscreen GIS Explorer</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <RiskMap
            projects={projects}
            height="460px"
            showControls={true}
          />
        </div>

        {/* Charts Container (5 cols) */}
        <div className="lg:col-span-5 flex flex-col space-y-6">
          <RiskChart projects={projects} />
          <DelayTrendChart projects={projects} />
        </div>
      </div>

      {/* Priority Watchlist Table */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <ShieldAlert className="w-4 h-4 text-amber-400" />
            <h2 className="text-base font-semibold text-white">High-Risk Project Watchlist</h2>
          </div>
          <Link
            to="/projects"
            className="inline-flex items-center space-x-1 text-xs text-sky-400 hover:text-sky-300 transition-colors"
          >
            <span>View All {projects.length} Projects</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <ProjectTable
          projects={projects}
          compact={true}
          initialRisk="HIGH"
          title="Top Critical Delay Projects"
          subtitle="Projects flagged with delay probability ≥ 60% requiring immediate executive intervention"
        />
      </div>
    </div>
  );
}

import React, { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { 
  Map as MapIcon, 
  Layers, 
  Filter, 
  ExternalLink, 
  ShieldAlert, 
  Building2, 
  Compass,
  Maximize2
} from 'lucide-react';

import api from '../services/api';
import RiskMap from '../components/RiskMap';
import RiskBadge from '../components/RiskBadge';
import Loading from '../components/Loading';
import ErrorMessage from '../components/ErrorMessage';
import { formatCurrency, formatPercent, normalizeStateName } from '../utils/riskUtils';

export default function GISMapView() {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedState, setSelectedState] = useState('');

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      setError(null);
      try {
        const res = await api.getProjects({ limit: 500 });
        setProjects(res.projects || []);
      } catch (err) {
        console.error('Failed to load projects for map:', err);
        setError(err.message || 'Unable to fetch projects from API.');
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  // Filter projects by selected state for side inspector
  const stateProjects = useMemo(() => {
    if (!selectedState) return projects.slice(0, 15);
    return projects.filter(
      p => normalizeStateName(p.state_std || p.state) === normalizeStateName(selectedState)
    );
  }, [projects, selectedState]);

  // Aggregate metrics for active state
  const stateMetrics = useMemo(() => {
    const list = selectedState
      ? projects.filter(p => normalizeStateName(p.state_std || p.state) === normalizeStateName(selectedState))
      : projects;

    let high = 0;
    let sumScore = 0;
    let sumCost = 0;

    list.forEach(p => {
      const cat = (p.risk_category || '').toUpperCase();
      if (cat === 'HIGH' || cat === 'CRITICAL') high++;
      sumScore += Number(p.risk_score || 50);
      sumCost += Number(p.cost_revised || p.cost_original || 0);
    });

    return {
      total: list.length,
      high,
      avgScore: list.length > 0 ? (sumScore / list.length).toFixed(1) : 0,
      totalCost: sumCost,
    };
  }, [projects, selectedState]);

  if (loading && !projects.length) {
    return (
      <div className="min-h-[70vh] flex items-center justify-center">
        <Loading message="Rendering National Geographic Spatial Infrastructure Map..." />
      </div>
    );
  }

  if (error && !projects.length) {
    return (
      <div className="max-w-4xl mx-auto py-12 px-4">
        <ErrorMessage
          title="GIS Map Data Error"
          message={error}
          onRetry={() => window.location.reload()}
        />
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <MapIcon className="w-6 h-6 text-sky-400" />
            <h1 className="text-2xl font-bold text-white tracking-tight">
              National GIS Delay Intelligence Explorer
            </h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Spatial choropleth visualization of state infrastructure risk scores with real-time project risk markers and delay hotspots across India.
          </p>
        </div>

        <div className="flex items-center space-x-2 text-xs">
          <span className="px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 font-mono">
            {projects.length} Geo-located Projects
          </span>
        </div>
      </div>

      {/* Main Split Layout: Leaflet Map (Left/Center) + State Inspector (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Full-Featured Leaflet GIS Map (8 cols) */}
        <div className="lg:col-span-8 flex flex-col space-y-2">
          <RiskMap
            projects={projects}
            selectedState={selectedState}
            onStateSelect={setSelectedState}
            height="620px"
            showControls={true}
          />
          <div className="flex items-center justify-between text-[11px] text-slate-500 px-2">
            <span>Click any state boundary to zoom and inspect regional project portfolio</span>
            <span>OpenStreetMap Tiles + India Official Survey GeoJSON Layers</span>
          </div>
        </div>

        {/* State / Project Inspector Drawer (4 cols) */}
        <div className="lg:col-span-4 flex flex-col space-y-4 bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl h-[645px] overflow-hidden">
          {/* Active State Header */}
          <div className="border-b border-slate-800 pb-4">
            <span className="text-[11px] font-semibold text-sky-400 uppercase tracking-wider block">
              Regional Jurisdiction
            </span>
            <div className="flex items-center justify-between mt-1">
              <h2 className="text-lg font-bold text-white truncate">
                {selectedState || 'All India Portfolio'}
              </h2>
              {selectedState && (
                <button
                  onClick={() => setSelectedState('')}
                  className="text-xs text-sky-400 hover:text-sky-300 transition-colors"
                >
                  Reset
                </button>
              )}
            </div>
          </div>

          {/* Quick Metrics for Selected Jurisdiction */}
          <div className="grid grid-cols-3 gap-2 text-center text-xs">
            <div className="bg-slate-950 p-2.5 rounded-xl border border-slate-800">
              <span className="text-[10px] text-slate-400 block">Projects</span>
              <span className="text-base font-bold font-mono text-white mt-0.5 block">
                {stateMetrics.total}
              </span>
            </div>
            <div className="bg-slate-950 p-2.5 rounded-xl border border-slate-800">
              <span className="text-[10px] text-slate-400 block">High Risk</span>
              <span className="text-base font-bold font-mono text-amber-400 mt-0.5 block">
                {stateMetrics.high}
              </span>
            </div>
            <div className="bg-slate-950 p-2.5 rounded-xl border border-slate-800">
              <span className="text-[10px] text-slate-400 block">Avg Risk</span>
              <span className="text-base font-bold font-mono text-sky-400 mt-0.5 block">
                {stateMetrics.avgScore}
              </span>
            </div>
          </div>

          {/* List of projects in active state */}
          <div className="flex-1 overflow-y-auto space-y-2.5 pr-1 text-xs">
            <span className="text-xs font-medium text-slate-400 block sticky top-0 bg-slate-900 py-1">
              {selectedState ? `Projects in ${selectedState}` : 'Selected High-Impact Projects'} ({stateProjects.length})
            </span>

            {stateProjects.length === 0 ? (
              <div className="py-12 text-center text-slate-500 text-xs">
                No tracked projects found for this region.
              </div>
            ) : (
              stateProjects.map((p) => (
                <div
                  key={p.project_id}
                  className="bg-slate-950/80 hover:bg-slate-950 border border-slate-800/80 hover:border-slate-700 p-3 rounded-xl transition-all space-y-2 group"
                >
                  <div className="flex items-start justify-between gap-2">
                    <span className="font-mono text-[10px] text-slate-500">#{p.project_id}</span>
                    <RiskBadge category={p.risk_category} size="sm" />
                  </div>

                  <h3 className="font-semibold text-slate-200 text-xs line-clamp-2 leading-tight group-hover:text-sky-400 transition-colors">
                    {p.project_name}
                  </h3>

                  <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1 border-t border-slate-900">
                    <span>{p.sector || 'Infrastructure'}</span>
                    <span className="font-mono text-slate-300">{formatCurrency(p.cost_revised || p.cost_original)}</span>
                  </div>

                  <Link
                    to={`/projects/${p.project_id}`}
                    className="inline-flex items-center space-x-1 text-[11px] text-sky-400 hover:text-sky-300 font-medium pt-1"
                  >
                    <span>Inspect Dossier</span>
                    <ExternalLink className="w-3 h-3" />
                  </Link>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

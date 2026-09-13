import React, { useState, useEffect } from 'react';
import { Building2, RefreshCw, Download } from 'lucide-react';
import api from '../services/api';
import ProjectTable from '../components/ProjectTable';
import Loading from '../components/Loading';
import ErrorMessage from '../components/ErrorMessage';

export default function Projects() {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchProjects = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getProjects({ limit: 500 });
      setProjects(res.projects || []);
    } catch (err) {
      console.error('Error fetching projects:', err);
      setError(err.message || 'Failed to fetch projects from backend API');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, []);

  const exportCSV = () => {
    if (!projects.length) return;
    const headers = [
      'Project ID',
      'Project Name',
      'Agency',
      'State',
      'Sector',
      'Original Cost (Cr)',
      'Revised Cost (Cr)',
      'Physical Progress (%)',
      'Delay Probability',
      'Risk Score',
      'Risk Category'
    ];

    const rows = projects.map(p => [
      `"${p.project_id || ''}"`,
      `"${(p.project_name || '').replace(/"/g, '""')}"`,
      `"${(p.agency || '').replace(/"/g, '""')}"`,
      `"${p.state_std || p.state || ''}"`,
      `"${p.sector || ''}"`,
      p.original_cost || 0,
      p.revised_cost || 0,
      p.physical_progress || 0,
      (Number(p.delay_probability || 0) * 100).toFixed(1),
      Number(p.risk_score || 0).toFixed(1),
      p.risk_category || 'MEDIUM'
    ]);

    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map(e => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `RiskGuard_Infrastructure_Projects_${new Date().toISOString().slice(0,10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  if (loading && !projects.length) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <Loading message="Loading infrastructure projects registry..." />
      </div>
    );
  }

  if (error && !projects.length) {
    return (
      <div className="max-w-4xl mx-auto py-12 px-4">
        <ErrorMessage
          title="Projects Directory Error"
          message={error}
          onRetry={fetchProjects}
        />
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-12">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <Building2 className="w-6 h-6 text-sky-400" />
            <h1 className="text-2xl font-bold text-white tracking-tight">
              Projects Intelligence Directory
            </h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Complete database of {projects.length} infrastructure projects enriched with ML delay predictions, risk classifications, and financial indicators.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={exportCSV}
            className="inline-flex items-center space-x-1.5 px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 transition-colors"
          >
            <Download className="w-3.5 h-3.5 text-slate-400" />
            <span>Export CSV</span>
          </button>
          <button
            onClick={fetchProjects}
            disabled={loading}
            className="inline-flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-sky-600 hover:bg-sky-500 text-white text-xs font-medium transition-all disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Main Filterable Project Table */}
      <ProjectTable
        projects={projects}
        loading={loading}
        compact={false}
        title="Infrastructure Projects Portfolio"
        subtitle="Search, filter by state, sector, or risk tier, and view comprehensive project dossiers"
      />
    </div>
  );
}

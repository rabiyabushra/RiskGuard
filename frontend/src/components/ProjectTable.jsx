import React, { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { Search, Filter, ArrowUpDown, ChevronLeft, ChevronRight, Eye } from 'lucide-react';
import RiskBadge from './RiskBadge';
import { formatCurrency, formatPercent } from '../utils/riskUtils';

export default function ProjectTable({
  projects = [],
  loading = false,
  compact = false,
  title = 'Projects Directory',
  subtitle = 'Filter and inspect infrastructure project delay risks',
  initialRisk = 'ALL'
}) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedState, setSelectedState] = useState('');
  const [selectedSector, setSelectedSector] = useState('');
  const [selectedRisk, setSelectedRisk] = useState(initialRisk);
  const [sortField, setSortField] = useState('risk_score');
  const [sortAsc, setSortAsc] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = compact ? 5 : 12;

  // Extract unique filter options
  const uniqueStates = useMemo(() => {
    const s = new Set();
    projects.forEach(p => {
      const val = p.state_std || p.state;
      if (val) s.add(val.trim());
    });
    return Array.from(s).sort();
  }, [projects]);

  const uniqueSectors = useMemo(() => {
    const s = new Set();
    projects.forEach(p => {
      if (p.sector) s.add(p.sector.trim());
    });
    return Array.from(s).sort();
  }, [projects]);

  // Filter and Sort
  const filteredAndSorted = useMemo(() => {
    let result = [...projects];

    // Filter by text
    if (searchTerm.trim()) {
      const q = searchTerm.toLowerCase();
      result = result.filter(p =>
        (p.project_id && String(p.project_id).toLowerCase().includes(q)) ||
        (p.project_name && p.project_name.toLowerCase().includes(q)) ||
        (p.agency && p.agency.toLowerCase().includes(q)) ||
        (p.state && p.state.toLowerCase().includes(q)) ||
        (p.sector && p.sector.toLowerCase().includes(q))
      );
    }

    // Filter by state
    if (selectedState) {
      result = result.filter(p => (p.state_std || p.state) === selectedState);
    }

    // Filter by sector
    if (selectedSector) {
      result = result.filter(p => p.sector === selectedSector);
    }

    // Filter by risk category
    if (selectedRisk !== 'ALL') {
      result = result.filter(p => {
        const cat = (p.risk_category || '').toUpperCase();
        if (selectedRisk === 'HIGH') return cat === 'HIGH' || cat === 'CRITICAL';
        return cat === selectedRisk;
      });
    }

    // Sorting
    result.sort((a, b) => {
      let valA = a[sortField];
      let valB = b[sortField];

      if (valA === undefined || valA === null) valA = 0;
      if (valB === undefined || valB === null) valB = 0;

      if (typeof valA === 'string') {
        return sortAsc ? valA.localeCompare(valB) : valB.localeCompare(valA);
      }
      return sortAsc ? Number(valA) - Number(valB) : Number(valB) - Number(valA);
    });

    return result;
  }, [projects, searchTerm, selectedState, selectedSector, selectedRisk, sortField, sortAsc]);

  // Pagination
  const totalPages = Math.max(1, Math.ceil(filteredAndSorted.length / pageSize));
  const paginatedProjects = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredAndSorted.slice(start, start + pageSize);
  }, [filteredAndSorted, currentPage, pageSize]);

  const handleSort = (field) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(false);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl shadow-xl overflow-hidden">
      {/* Header & Controls */}
      <div className="p-5 border-b border-slate-800 bg-slate-900/80">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h3 className="text-lg font-semibold text-white tracking-tight">{title}</h3>
            <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>
          </div>

          <div className="flex items-center space-x-2 text-xs text-slate-400">
            <span>Showing <strong className="text-sky-400">{filteredAndSorted.length}</strong> of {projects.length} projects</span>
          </div>
        </div>

        {/* Filter Bar */}
        <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {/* Search */}
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search by ID, name, sector..."
              value={searchTerm}
              onChange={(e) => { setSearchTerm(e.target.value); setCurrentPage(1); }}
              className="w-full pl-9 pr-3 py-1.5 bg-slate-950 border border-slate-800 text-slate-200 rounded-lg text-xs focus:outline-none focus:border-sky-500 transition-colors"
            />
          </div>

          {/* State Filter */}
          <select
            value={selectedState}
            onChange={(e) => { setSelectedState(e.target.value); setCurrentPage(1); }}
            className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 text-slate-200 rounded-lg text-xs focus:outline-none focus:border-sky-500 transition-colors"
          >
            <option value="">All States ({uniqueStates.length})</option>
            {uniqueStates.map(st => (
              <option key={st} value={st}>{st}</option>
            ))}
          </select>

          {/* Sector Filter */}
          <select
            value={selectedSector}
            onChange={(e) => { setSelectedSector(e.target.value); setCurrentPage(1); }}
            className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 text-slate-200 rounded-lg text-xs focus:outline-none focus:border-sky-500 transition-colors"
          >
            <option value="">All Sectors ({uniqueSectors.length})</option>
            {uniqueSectors.map(sec => (
              <option key={sec} value={sec}>{sec}</option>
            ))}
          </select>

          {/* Risk Tier Toggle */}
          <div className="flex items-center justify-between bg-slate-950 p-1 rounded-lg border border-slate-800">
            {['ALL', 'HIGH', 'MEDIUM', 'LOW'].map(lvl => (
              <button
                key={lvl}
                onClick={() => { setSelectedRisk(lvl); setCurrentPage(1); }}
                className={`flex-1 py-1 text-[11px] font-medium rounded-md transition-colors ${
                  selectedRisk === lvl
                    ? 'bg-sky-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {lvl}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Table Content */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="border-b border-slate-800 bg-slate-950/60 text-slate-400 uppercase font-medium tracking-wider">
              <th className="py-3 px-4">Project ID</th>
              <th className="py-3 px-4 min-w-[200px]">Project Name</th>
              <th className="py-3 px-4">State</th>
              <th className="py-3 px-4">Sector</th>
                <th className="py-3 px-4 cursor-pointer hover:text-slate-200" onClick={() => handleSort('revised_cost')}>
                <div className="flex items-center space-x-1">
                  <span>Cost</span>
                  <ArrowUpDown className="w-3 h-3 text-slate-500" />
                </div>
              </th>
              <th className="py-3 px-4 cursor-pointer hover:text-slate-200" onClick={() => handleSort('physical_progress')}>
                <div className="flex items-center space-x-1">
                  <span>Progress</span>
                  <ArrowUpDown className="w-3 h-3 text-slate-500" />
                </div>
              </th>
              <th className="py-3 px-4 cursor-pointer hover:text-slate-200" onClick={() => handleSort('delay_probability')}>
                <div className="flex items-center space-x-1">
                  <span>Delay Prob</span>
                  <ArrowUpDown className="w-3 h-3 text-slate-500" />
                </div>
              </th>
              <th className="py-3 px-4 cursor-pointer hover:text-slate-200" onClick={() => handleSort('risk_score')}>
                <div className="flex items-center space-x-1">
                  <span>Risk Score</span>
                  <ArrowUpDown className="w-3 h-3 text-slate-500" />
                </div>
              </th>
              <th className="py-3 px-4">Risk Tier</th>
              <th className="py-3 px-4 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {paginatedProjects.length === 0 ? (
              <tr>
                <td colSpan="10" className="text-center py-10 text-slate-500">
                  {loading ? 'Loading projects...' : 'No infrastructure projects match your filters.'}
                </td>
              </tr>
            ) : (
              paginatedProjects.map((p) => {
                const costVal = p.revised_cost || p.original_cost || 0;
                const progressVal = Number(p.physical_progress || 0);
                const delayProb = (Number(p.delay_probability || 0) * 100).toFixed(1);
                const riskScore = Number(p.risk_score || 0).toFixed(1);

                return (
                  <tr
                    key={p.project_id}
                    className="hover:bg-slate-800/40 transition-colors group"
                  >
                    <td className="py-3 px-4 font-mono font-medium text-slate-300">
                      {p.project_id}
                    </td>
                    <td className="py-3 px-4">
                      <Link
                        to={`/projects/${p.project_id}`}
                        className="font-medium text-white group-hover:text-sky-400 transition-colors line-clamp-1"
                        title={p.project_name}
                      >
                        {p.project_name}
                      </Link>
                      <span className="text-[11px] text-slate-500 block truncate">
                        {p.agency || 'Agency not specified'}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-slate-300 whitespace-nowrap">
                      {p.state_std || p.state}
                    </td>
                    <td className="py-3 px-4 text-slate-400 whitespace-nowrap">
                      <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 text-[11px]">
                        {p.sector || 'General'}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-200 whitespace-nowrap">
                      {formatCurrency(costVal)}
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap">
                      <div className="flex items-center space-x-2">
                        <div className="w-14 bg-slate-800 rounded-full h-1.5 overflow-hidden">
                          <div
                            className={`h-full rounded-full ${
                              progressVal >= 75
                                ? 'bg-emerald-500'
                                : progressVal >= 35
                                ? 'bg-sky-500'
                                : 'bg-amber-500'
                            }`}
                            style={{ width: `${Math.min(100, Math.max(0, progressVal))}%` }}
                          />
                        </div>
                        <span className="font-mono text-[11px] text-slate-300">
                          {progressVal.toFixed(0)}%
                        </span>
                      </div>
                    </td>
                    <td className="py-3 px-4 font-mono font-medium whitespace-nowrap">
                      <span className={Number(delayProb) >= 60 ? 'text-amber-400' : 'text-slate-300'}>
                        {delayProb}%
                      </span>
                    </td>
                    <td className="py-3 px-4 font-mono font-semibold whitespace-nowrap text-slate-100">
                      {riskScore}
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap">
                      <RiskBadge category={p.risk_category} size="sm" />
                    </td>
                    <td className="py-3 px-4 text-right whitespace-nowrap">
                      <Link
                        to={`/projects/${p.project_id}`}
                        className="inline-flex items-center space-x-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-sky-600 text-slate-300 hover:text-white transition-all text-xs font-medium"
                      >
                        <span>Dossier</span>
                        <Eye className="w-3 h-3" />
                      </Link>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      <div className="p-4 border-t border-slate-800 bg-slate-950/40 flex items-center justify-between text-xs text-slate-400">
        <div>
          Page <strong className="text-slate-200">{currentPage}</strong> of <strong className="text-slate-200">{totalPages}</strong>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
            disabled={currentPage === 1}
            className="p-1.5 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed text-slate-300 transition-colors"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <button
            onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
            disabled={currentPage === totalPages}
            className="p-1.5 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed text-slate-300 transition-colors"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}

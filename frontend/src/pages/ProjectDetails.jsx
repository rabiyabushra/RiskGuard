import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { 
  ArrowLeft, 
  Building2, 
  Calendar, 
  MapPin, 
  DollarSign, 
  Activity, 
  TrendingUp, 
  FileText, 
  Layers, 
  ShieldAlert,
  Clock,
  Sparkles
} from 'lucide-react';

import api from '../services/api';
import RiskBadge from '../components/RiskBadge';
import SHAPChart from '../components/SHAPChart';
import RecommendationCard from '../components/RecommendationCard';
import RiskMap from '../components/RiskMap';
import Loading from '../components/Loading';
import ErrorMessage from '../components/ErrorMessage';
import { formatCurrency, formatPercent } from '../utils/riskUtils';

export default function ProjectDetails() {
  const { projectId } = useParams();
  const [project, setProject] = useState(null);
  const [shapData, setShapData] = useState(null);
  const [recommendations, setRecommendations] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let isMounted = true;

    async function loadProjectDossier() {
      setLoading(true);
      setError(null);

      try {
        // 1. Fetch Project Details from backend
        const projRes = await api.getProjectById(projectId);
        if (!isMounted) return;
        setProject(projRes);

        // 2. Fetch SHAP Explainability in parallel
        try {
          const shapRes = await api.getProjectExplanation(projectId);
          if (isMounted) setShapData(shapRes);
        } catch (shapErr) {
          console.warn('SHAP explanation not available for this project:', shapErr);
        }

        // 3. Fetch Gemini Recommendations in parallel
        try {
          const recRes = await api.getRecommendations(projectId);
          if (isMounted) {
            setRecommendations(recRes.recommendations || recRes);
          }
        } catch (recErr) {
          console.warn('Gemini recommendations fetch error:', recErr);
        }

      } catch (err) {
        console.error('Error fetching project dossier:', err);
        if (isMounted) {
          setError(err.message || `Project ${projectId} could not be loaded.`);
        }
      } finally {
        if (isMounted) setLoading(false);
      }
    }

    if (projectId) {
      loadProjectDossier();
    }

    return () => {
      isMounted = false;
    };
  }, [projectId]);

  if (loading) {
    return (
      <div className="min-h-[70vh] flex items-center justify-center">
        <Loading message={`Loading Intelligence Dossier for Project #${projectId}...`} />
      </div>
    );
  }

  if (error || !project) {
    return (
      <div className="max-w-4xl mx-auto py-12 px-4 space-y-4">
        <Link
          to="/projects"
          className="inline-flex items-center space-x-2 text-xs text-sky-400 hover:text-sky-300 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Projects Directory</span>
        </Link>
        <ErrorMessage
          title="Project Dossier Not Found"
          message={error || `Project ID ${projectId} does not exist in the database.`}
        />
      </div>
    );
  }

  // Calculate financial variance
  const costOrig = Number(project.cost_original || 0);
  const costRev = Number(project.cost_revised || costOrig);
  const costOverrun = costOrig > 0 ? ((costRev - costOrig) / costOrig) * 100 : 0;
  const progress = Number(project.physical_progress || 0);
  const delayProb = Number(project.delay_probability || 0) * 100;
  const riskScore = Number(project.risk_score || 50).toFixed(1);

  // Extract SHAP features
  const shapFeatures = shapData?.top_features || shapData?.features || [];

  return (
    <div className="space-y-8 pb-16 max-w-7xl mx-auto">
      {/* Back Navigation & Breadcrumb */}
      <div className="flex items-center justify-between">
        <Link
          to="/projects"
          className="inline-flex items-center space-x-2 text-xs font-medium text-slate-400 hover:text-sky-400 transition-colors bg-slate-900 px-3 py-1.5 rounded-lg border border-slate-800"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Projects Directory</span>
        </Link>

        <div className="flex items-center space-x-2 text-xs">
          <span className="text-slate-500">Project ID:</span>
          <span className="font-mono text-sky-400 font-semibold">{project.project_id}</span>
        </div>
      </div>

      {/* Hero Dossier Header */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-900 to-slate-800/90 p-6 sm:p-8 rounded-3xl border border-slate-800 shadow-2xl space-y-6">
        <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-6">
          <div className="space-y-3 max-w-3xl">
            <div className="flex flex-wrap items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-md bg-slate-800 text-slate-300 text-xs font-medium border border-slate-700">
                {project.sector || 'Infrastructure'}
              </span>
              <span className="px-2.5 py-0.5 rounded-md bg-sky-500/10 text-sky-400 text-xs font-medium border border-sky-500/20 flex items-center space-x-1">
                <MapPin className="w-3 h-3" />
                <span>{project.state_std || project.state || 'India'}</span>
              </span>
              <span className="px-2.5 py-0.5 rounded-md bg-slate-800 text-slate-400 text-xs font-medium">
                Agency: <strong className="text-slate-200">{project.agency || 'N/A'}</strong>
              </span>
            </div>

            <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight leading-tight">
              {project.project_name}
            </h1>

            <p className="text-xs text-slate-400 flex items-center space-x-2">
              <Calendar className="w-3.5 h-3.5 text-slate-500" />
              <span>Original Commissioning: <strong className="text-slate-300">{project.date_original_commissioning || project.date_orig_comm || 'Not specified'}</strong></span>
              <span className="text-slate-600">•</span>
              <span>Anticipated Completion: <strong className="text-slate-300">{project.date_anticipated || project.date_anticip || 'Under Review'}</strong></span>
            </p>
          </div>

          {/* Risk Level Badge & Score */}
          <div className="flex flex-row lg:flex-col items-center lg:items-end justify-between gap-3 bg-slate-950/80 p-4 rounded-2xl border border-slate-800 min-w-[200px]">
            <span className="text-xs text-slate-400 font-medium">Delay Risk Assessment</span>
            <RiskBadge
              category={project.risk_category}
              score={project.risk_score}
              size="lg"
            />
            <div className="text-right">
              <span className="text-[11px] text-slate-500">Delay Probability: </span>
              <span className="font-mono text-sm font-bold text-sky-400">{delayProb.toFixed(1)}%</span>
            </div>
          </div>
        </div>

        {/* 4 Financial & Operational KPIs */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 pt-4 border-t border-slate-800/80">
          {/* Cost Overview */}
          <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800/60">
            <span className="text-xs text-slate-400 flex items-center space-x-1.5">
              <DollarSign className="w-3.5 h-3.5 text-sky-400" />
              <span>Revised Cost</span>
            </span>
            <div className="mt-2 flex items-baseline justify-between">
              <span className="text-lg font-bold font-mono text-white">
                {formatCurrency(costRev)}
              </span>
            </div>
            <span className="text-[11px] text-slate-500 mt-1 block">
              Orig: {formatCurrency(costOrig)} ({costOverrun > 0 ? `+${costOverrun.toFixed(1)}%` : 'No overrun'})
            </span>
          </div>

          {/* Physical Progress */}
          <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800/60">
            <span className="text-xs text-slate-400 flex items-center space-x-1.5">
              <Activity className="w-3.5 h-3.5 text-emerald-400" />
              <span>Physical Progress</span>
            </span>
            <div className="mt-2 flex items-baseline justify-between">
              <span className="text-lg font-bold font-mono text-emerald-400">
                {progress.toFixed(1)}%
              </span>
            </div>
            <div className="w-full bg-slate-800 rounded-full h-1.5 mt-2 overflow-hidden">
              <div
                className="bg-emerald-500 h-full rounded-full transition-all duration-500"
                style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
              />
            </div>
          </div>

          {/* Cumulative Expenditure */}
          <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800/60">
            <span className="text-xs text-slate-400 flex items-center space-x-1.5">
              <TrendingUp className="w-3.5 h-3.5 text-indigo-400" />
              <span>Cumulative Expenditure</span>
            </span>
            <div className="mt-2 flex items-baseline justify-between">
              <span className="text-lg font-bold font-mono text-slate-200">
                {formatCurrency(project.cumulative_expenditure || project.expenditure || 0)}
              </span>
            </div>
            <span className="text-[11px] text-slate-500 mt-1 block">
              Financial utilization against budget
            </span>
          </div>

          {/* Delay Margin */}
          <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800/60">
            <span className="text-xs text-slate-400 flex items-center space-x-1.5">
              <Clock className="w-3.5 h-3.5 text-amber-400" />
              <span>Schedule Variance</span>
            </span>
            <div className="mt-2 flex items-baseline justify-between">
              <span className="text-lg font-bold font-mono text-amber-400">
                {project.delay_months ? `${project.delay_months} Months` : 'Projected Delay'}
              </span>
            </div>
            <span className="text-[11px] text-slate-500 mt-1 block">
              Delay Probability: {delayProb.toFixed(1)}%
            </span>
          </div>
        </div>
      </div>

      {/* Main Analysis Section (2 Columns: Explainable AI SHAP vs Gemini Recommendations) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: SHAP Feature Attributions (6 cols) */}
        <div className="lg:col-span-6 space-y-4">
          <div className="flex items-center space-x-2">
            <Layers className="w-5 h-5 text-sky-400" />
            <h2 className="text-lg font-semibold text-white">Explainable AI (SHAP Analysis)</h2>
          </div>
          <p className="text-xs text-slate-400">
            SHAP (SHapley Additive exPlanations) isolates the mathematical impact of each project attribute on pushing the model toward or away from delay risk.
          </p>

          <SHAPChart
            features={shapFeatures}
            baseValue={shapData?.base_value}
            projectId={projectId}
          />
        </div>

        {/* Right Column: AI Actionable Mitigation Recommendations (Gemini) (6 cols) */}
        <div className="lg:col-span-6 space-y-4">
          <div className="flex items-center space-x-2">
            <Sparkles className="w-5 h-5 text-indigo-400" />
            <h2 className="text-lg font-semibold text-white">Gemini AI Recommendations</h2>
          </div>
          <p className="text-xs text-slate-400">
            Strategic risk mitigation and land acquisition recovery steps synthesized directly by Google Gemini from real ML delay factors.
          </p>

          <RecommendationCard
            projectId={projectId}
            initialRecommendations={recommendations}
            riskLevel={project.risk_category}
          />
        </div>
      </div>

      {/* Project Geographic Context & Multi-Source Attributes */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
        <div className="flex items-center space-x-2">
          <MapPin className="w-5 h-5 text-sky-400" />
          <h3 className="text-base font-semibold text-white">Regional & Multi-Source Project Context</h3>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Detailed Metadata Grid */}
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                <span className="text-slate-400 block text-[11px]">Executing Ministry / Agency</span>
                <span className="font-semibold text-slate-200 mt-1 block">{project.agency || 'N/A'}</span>
              </div>
              <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                <span className="text-slate-400 block text-[11px]">State Jurisdiction</span>
                <span className="font-semibold text-slate-200 mt-1 block">{project.state_std || project.state}</span>
              </div>
              <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                <span className="text-slate-400 block text-[11px]">Original Cost</span>
                <span className="font-semibold font-mono text-slate-200 mt-1 block">{formatCurrency(costOrig)}</span>
              </div>
              <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                <span className="text-slate-400 block text-[11px]">Revised Cost</span>
                <span className="font-semibold font-mono text-slate-200 mt-1 block">{formatCurrency(costRev)}</span>
              </div>
            </div>

            <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800/80 space-y-2 text-xs text-slate-300">
              <div className="flex items-center space-x-2 text-sky-400 font-semibold">
                <FileText className="w-4 h-4" />
                <span>Multi-Source Data Fusion Status</span>
              </div>
              <p className="text-slate-400 text-[11px] leading-relaxed">
                This project record fuses PAIMANA central data with demographic density indices, district court litigation caseloads, regional power grid proximity, and road network density to establish delay vulnerability.
              </p>
            </div>
          </div>

          {/* Mini Regional Map */}
          <div>
            <RiskMap
              projects={[project]}
              selectedState={project.state_std || project.state}
              height="280px"
              showControls={false}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

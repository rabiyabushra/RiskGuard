import React from 'react';
import { Routes, Route, Link } from 'react-router-dom';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import Projects from './pages/Projects';
import ProjectDetails from './pages/ProjectDetails';
import GISMapView from './pages/GISMapView';
import RiskAnalysis from './pages/RiskAnalysis';
import { ShieldCheck, ArrowRight } from 'lucide-react';

function NotFound() {
  return (
    <div className="min-h-[60vh] flex flex-col items-center justify-center text-center space-y-4">
      <div className="w-16 h-16 rounded-full bg-slate-800 flex items-center justify-center text-sky-400">
        <ShieldCheck className="w-8 h-8" />
      </div>
      <h2 className="text-2xl font-bold text-white">404 - Page Not Found</h2>
      <p className="text-sm text-slate-400 max-w-md">
        The intelligence module or project dossier you requested does not exist or has been moved.
      </p>
      <Link
        to="/"
        className="inline-flex items-center space-x-2 px-4 py-2 rounded-xl bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold transition-colors"
      >
        <span>Return to Dashboard</span>
        <ArrowRight className="w-4 h-4" />
      </Link>
    </div>
  );
}

export default function App() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-sky-500/30 selection:text-sky-200">
      {/* Global Navigation Bar */}
      <Navbar />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 pt-6">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/projects" element={<Projects />} />
          <Route path="/projects/:projectId" element={<ProjectDetails />} />
          <Route path="/map" element={<GISMapView />} />
          <Route path="/risk-analysis" element={<RiskAnalysis />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 bg-slate-900/60 mt-auto py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-4 text-xs text-slate-500">
          <div className="flex items-center space-x-2">
            <span className="font-semibold text-slate-300">RiskGuard Intelligence</span>
            <span>•</span>
            <span>Smart India Hackathon</span>
            <span>•</span>
            <span>Predictive Land Acquisition Delay Intelligence</span>
          </div>

          <div className="flex items-center space-x-4 text-slate-400">
            <span>FastAPI + MongoDB</span>
            <span>•</span>
            <span>XGBoost ML</span>
            <span>•</span>
            <span>SHAP Explainability</span>
            <span>•</span>
            <span>Google Gemini AI</span>
            <span>•</span>
            <span>Leaflet GIS</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

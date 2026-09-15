import React from 'react';
import { Sparkles, CheckCircle2, AlertTriangle, RefreshCw, Compass } from 'lucide-react';

function renderFormattedRecommendation(recText) {
  if (!recText || typeof recText !== 'string') return recText;

  // Match "**Action Title**: Description" or "**Action Title** - Description"
  const boldMatch = recText.match(/^\s*\*\*(.*?)\*\*[:\-]?\s*(.*)$/s);
  if (boldMatch) {
    const [, title, desc] = boldMatch;
    return (
      <div>
        <span className="font-semibold text-sky-400 block mb-1 text-sm tracking-wide">
          {title.trim()}
        </span>
        <span className="text-slate-200 text-xs sm:text-sm leading-relaxed block">
          {desc.trim()}
        </span>
      </div>
    );
  }

  // Match "Action Title: Description"
  const colonMatch = recText.match(/^([A-Z][A-Za-z0-9\s,&/\-]{2,45}):\s+(.*)$/s);
  if (colonMatch) {
    const [, title, desc] = colonMatch;
    return (
      <div>
        <span className="font-semibold text-sky-400 block mb-1 text-sm tracking-wide">
          {title.trim()}
        </span>
        <span className="text-slate-200 text-xs sm:text-sm leading-relaxed block">
          {desc.trim()}
        </span>
      </div>
    );
  }

  return <div className="text-xs sm:text-sm text-slate-200 leading-relaxed">{recText}</div>;
}

export default function RecommendationCard({
  recommendations = [],
  modelUsed = 'gemini-flash-latest',
  status = 'gemini_live',
  notes = null,
  onRefresh = null,
  loading = false
}) {
  const isLive = status === 'gemini_live';

  return (
    <div className="bg-gradient-to-br from-slate-800/90 to-slate-900/90 border border-slate-700/80 rounded-xl p-6 shadow-xl relative overflow-hidden">
      {/* Decorative Glow */}
      <div className="absolute top-0 right-0 -mr-16 -mt-16 w-48 h-48 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />

      <div className="flex items-center justify-between pb-4 border-b border-slate-700/60 mb-5">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 bg-gradient-to-br from-indigo-500/20 to-sky-500/20 rounded-lg border border-indigo-500/30">
            <Sparkles className="w-5 h-5 text-indigo-400" />
          </div>
          <div>
            <h3 className="font-semibold text-white text-base">Simplified Risk Mitigation Steps</h3>
            <p className="text-xs text-slate-400">Easy-to-understand, practical actions to prevent project delays</p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <span
            className={`text-xs px-2.5 py-1 rounded-full border font-mono ${
              isLive
                ? 'bg-indigo-500/20 text-indigo-300 border-indigo-500/40'
                : 'bg-slate-700 text-slate-300 border-slate-600'
            }`}
          >
            {isLive ? `Gemini AI (${modelUsed})` : 'AI Risk Advisor'}
          </span>

          {onRefresh && (
            <button
              onClick={onRefresh}
              disabled={loading}
              title="Refresh recommendations"
              className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-sky-400' : ''}`} />
            </button>
          )}
        </div>
      </div>

      {/* Recommendations List */}
      {recommendations && recommendations.length > 0 ? (
        <ul className="space-y-3.5">
          {recommendations.map((rec, index) => (
            <li
              key={index}
              className="flex items-start space-x-3 bg-slate-800/50 p-4 rounded-xl border border-slate-700/40 hover:border-slate-600/60 transition-colors"
            >
              <div className="w-6 h-6 rounded-full bg-emerald-500/10 border border-emerald-500/25 flex items-center justify-center shrink-0 mt-0.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              </div>
              <div className="flex-1 min-w-0">
                {renderFormattedRecommendation(rec)}
              </div>
            </li>
          ))}
        </ul>
      ) : (
        <div className="py-8 text-center text-xs text-slate-400">
          No recommendations available for this project.
        </div>
      )}

      {notes && (
        <div className="mt-4 pt-3 border-t border-slate-800 text-[11px] text-slate-400 flex items-center space-x-1.5">
          <AlertTriangle className="w-3.5 h-3.5 text-amber-400 shrink-0" />
          <span>{notes}</span>
        </div>
      )}
    </div>
  );
}

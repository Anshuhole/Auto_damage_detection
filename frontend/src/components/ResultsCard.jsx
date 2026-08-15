import React from 'react';
import { 
  CheckCircle2, AlertTriangle, FileDown, RefreshCw, 
  ShieldCheck, Share2, Tag, Percent, ArrowLeft 
} from 'lucide-react';
import GradCamViewer from './GradCamViewer';
import CostBreakdownCard from './CostBreakdownCard';
import { getReportPdfUrl } from '../services/api';

export default function ResultsCard({ result, onReset }) {
  if (!result) return null;

  const {
    id,
    image_filename,
    original_image_url,
    gradcam_image_url,
    has_damage,
    damage_type,
    damage_display_name,
    severity,
    confidence,
    probabilities = {},
    estimated_cost,
    bounding_boxes = [],
    notes,
    created_at
  } = result;

  const getSeverityBadge = () => {
    switch (severity?.toLowerCase()) {
      case 'severe':
        return {
          bg: 'bg-rose-950/80 text-rose-300 border-rose-600/60 shadow-[0_0_15px_rgba(244,63,94,0.3)]',
          label: 'Severe Damage'
        };
      case 'moderate':
        return {
          bg: 'bg-amber-950/80 text-amber-300 border-amber-600/60 shadow-[0_0_15px_rgba(245,158,11,0.3)]',
          label: 'Moderate Damage'
        };
      case 'minor':
        return {
          bg: 'bg-emerald-950/80 text-emerald-300 border-emerald-600/60 shadow-[0_0_15px_rgba(16,185,129,0.3)]',
          label: 'Minor Damage'
        };
      default:
        return {
          bg: 'bg-cyan-950/80 text-cyan-300 border-cyan-600/60 shadow-[0_0_15px_rgba(6,182,212,0.3)]',
          label: 'No Damage Detected'
        };
    }
  };

  const badgeInfo = getSeverityBadge();

  const handleDownloadPdf = () => {
    const url = getReportPdfUrl(id);
    window.open(url, '_blank');
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      
      {/* Top Banner Navigation */}
      <div className="flex items-center justify-between">
        <button
          onClick={onReset}
          className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-900/80 hover:bg-slate-800 text-slate-300 border border-slate-800 text-xs font-semibold transition-colors"
        >
          <ArrowLeft className="w-4 h-4 text-cyan-400" />
          <span>New Inspection</span>
        </button>

        <div className="flex items-center gap-3">
          <div className="text-right hidden sm:block">
            <div className="text-xs text-slate-400 font-mono">RECORD ID</div>
            <div className="text-xs font-bold text-slate-200 font-mono">{id}</div>
          </div>

          <button
            onClick={handleDownloadPdf}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white text-xs font-bold shadow-lg shadow-cyan-500/25 transition-all hover:scale-105 active:scale-95"
          >
            <FileDown className="w-4 h-4" />
            <span>Download Official PDF Report</span>
          </button>
        </div>
      </div>

      {/* Main Inspection Results Card */}
      <div className="glass-panel rounded-2xl p-6 sm:p-8 border-slate-800 shadow-2xl relative overflow-hidden">
        
        {/* Glow corner decorations */}
        <div className="absolute top-0 right-0 w-48 h-48 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />

        {/* Primary Classification Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-800">
          <div>
            <div className="flex items-center gap-2.5 mb-2">
              <span className={`px-3 py-1 rounded-lg text-xs font-extrabold uppercase tracking-wide border ${badgeInfo.bg}`}>
                {badgeInfo.label}
              </span>
              <span className="text-xs text-slate-400 font-mono">
                Confidence: <strong className="text-cyan-400">{(confidence * 100).toFixed(1)}%</strong>
              </span>
            </div>

            <h2 className="text-2xl sm:text-3xl font-black text-white tracking-tight">
              {damage_display_name}
            </h2>
            {notes && (
              <p className="text-xs text-slate-400 mt-1 italic">
                Notes: &ldquo;{notes}&rdquo;
              </p>
            )}
          </div>

          {/* Confidence Gauge Circle */}
          <div className="flex items-center gap-4 bg-slate-900/80 p-3.5 rounded-2xl border border-slate-800 shrink-0">
            <div className="relative w-14 h-14 flex items-center justify-center">
              <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
                <path
                  className="text-slate-800"
                  strokeWidth="3.5"
                  stroke="currentColor"
                  fill="none"
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                />
                <path
                  className="text-cyan-400"
                  strokeDasharray={`${confidence * 100}, 100`}
                  strokeWidth="3.5"
                  strokeLinecap="round"
                  stroke="currentColor"
                  fill="none"
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                />
              </svg>
              <span className="absolute text-xs font-black text-white font-mono">
                {(confidence * 100).toFixed(0)}%
              </span>
            </div>
            <div>
              <div className="text-xs font-bold text-white">ResNet50 Model</div>
              <div className="text-[11px] text-slate-400 font-mono">Transfer Fine-Tuned</div>
            </div>
          </div>
        </div>

        {/* Probability Breakdown Distribution */}
        <div className="py-5 border-b border-slate-800">
          <div className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-3 flex items-center gap-1.5">
            <Percent className="w-3.5 h-3.5 text-cyan-400" />
            <span>Class Probability Distribution</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-5 gap-2.5">
            {Object.entries(probabilities).map(([cls, prob]) => {
              const isTop = cls === damage_type;
              return (
                <div 
                  key={cls}
                  className={`p-2.5 rounded-xl border transition-all ${
                    isTop 
                      ? 'bg-cyan-950/40 border-cyan-500/50 text-cyan-300 shadow-sm' 
                      : 'bg-slate-900/60 border-slate-800/80 text-slate-400'
                  }`}
                >
                  <div className="flex items-center justify-between text-[11px] font-semibold mb-1">
                    <span className="capitalize">{cls.replace('_', ' ')}</span>
                    <span className="font-mono">{(prob * 100).toFixed(1)}%</span>
                  </div>
                  <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                    <div 
                      className={`h-full rounded-full ${isTop ? 'bg-cyan-400' : 'bg-slate-600'}`}
                      style={{ width: `${Math.max(4, prob * 100)}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Grad-CAM Visual Explainability Module */}
        <div className="pt-6 space-y-6">
          <GradCamViewer
            originalImageUrl={original_image_url}
            gradcamImageUrl={gradcam_image_url}
            boundingBoxes={bounding_boxes}
            damageType={damage_type}
          />

          {/* Repair Cost Estimation Card */}
          <CostBreakdownCard
            estimatedCost={estimated_cost}
            severity={severity}
            confidence={confidence}
          />
        </div>

      </div>

      {/* Action Footer */}
      <div className="flex items-center justify-between p-4 glass-card rounded-2xl border-slate-800">
        <span className="text-xs text-slate-400">
          Ready for another appraisal?
        </span>
        <button
          onClick={onReset}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-cyan-400 text-xs font-bold border border-slate-700 transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Start Another Scan</span>
        </button>
      </div>

    </div>
  );
}

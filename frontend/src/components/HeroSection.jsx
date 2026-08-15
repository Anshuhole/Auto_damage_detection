import React from 'react';
import { Sparkles, Shield, Cpu, FileCheck, Layers, Eye } from 'lucide-react';

export default function HeroSection({ onStartScan }) {
  return (
    <div className="relative pt-6 pb-8 overflow-hidden">
      {/* Background glow flares */}
      <div className="absolute top-1/2 left-1/4 -translate-y-1/2 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute top-1/2 right-1/4 -translate-y-1/2 w-96 h-96 bg-blue-600/10 rounded-full blur-3xl pointer-events-none" />

      <div className="relative max-w-4xl mx-auto text-center px-4">
        {/* Top Feature Pill */}
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-cyan-950/60 border border-cyan-800/60 text-cyan-300 text-xs font-medium mb-4 shadow-sm">
          <Sparkles className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />
          <span>Next-Gen Computer Vision for InsurTech & Vehicle Appraisals</span>
        </div>

        {/* Title */}
        <h1 className="text-3xl sm:text-5xl font-black tracking-tight text-white mb-4">
          Automated Vehicle Damage <br className="hidden sm:inline" />
          <span className="bg-gradient-to-r from-cyan-400 via-sky-300 to-blue-500 bg-clip-text text-transparent">
            Detection & Cost Intelligence
          </span>
        </h1>

        {/* Subtitle */}
        <p className="text-sm sm:text-base text-slate-400 max-w-2xl mx-auto mb-6 leading-relaxed">
          Upload or capture any vehicle photo to instantly detect scratches, dents, bumper cracks, and shattered glass. 
          Powered by fine-tuned <span className="text-slate-200 font-semibold">ResNet50</span> with <span className="text-cyan-400 font-semibold">Grad-CAM visual explainability</span> and itemized repair cost estimation.
        </p>

        {/* Key Feature Highlights */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 max-w-3xl mx-auto">
          <div className="glass-card rounded-xl p-3 text-left border-slate-800">
            <div className="flex items-center gap-2 text-cyan-400 mb-1">
              <Cpu className="w-4 h-4" />
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-300">Architecture</span>
            </div>
            <div className="text-sm font-bold text-white">ResNet50 CNN</div>
            <div className="text-[11px] text-slate-400">Transfer learning pipeline</div>
          </div>

          <div className="glass-card rounded-xl p-3 text-left border-slate-800">
            <div className="flex items-center gap-2 text-sky-400 mb-1">
              <Eye className="w-4 h-4" />
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-300">Explainability</span>
            </div>
            <div className="text-sm font-bold text-white">Grad-CAM Heatmaps</div>
            <div className="text-[11px] text-slate-400">Exact damage localization</div>
          </div>

          <div className="glass-card rounded-xl p-3 text-left border-slate-800">
            <div className="flex items-center gap-2 text-emerald-400 mb-1">
              <Layers className="w-4 h-4" />
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-300">Cost Engine</span>
            </div>
            <div className="text-sm font-bold text-white">Itemized Claim Est.</div>
            <div className="text-[11px] text-slate-400">Labor, paint & parts breakdown</div>
          </div>

          <div className="glass-card rounded-xl p-3 text-left border-slate-800">
            <div className="flex items-center gap-2 text-amber-400 mb-1">
              <FileCheck className="w-4 h-4" />
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-300">Inspection</span>
            </div>
            <div className="text-sm font-bold text-white">Official PDF Report</div>
            <div className="text-[11px] text-slate-400">One-click downloadable claims</div>
          </div>
        </div>
      </div>
    </div>
  );
}

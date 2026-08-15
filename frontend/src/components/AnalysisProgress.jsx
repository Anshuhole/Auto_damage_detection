import React, { useState, useEffect } from 'react';
import { Cpu, Eye, Layers, ShieldCheck, Sparkles, Loader2 } from 'lucide-react';

export default function AnalysisProgress() {
  const [activeStep, setActiveStep] = useState(0);

  const steps = [
    { label: 'Normalizing & Preprocessing Image Tensor', desc: 'Resizing to 224x224, ImageNet RGB standardization', icon: Sparkles },
    { label: 'ResNet50 Deep Feature Extraction', desc: 'Executing feed-forward pass across 50 convolutional layers', icon: Cpu },
    { label: 'Computing Grad-CAM Activation Heatmap', desc: 'Backpropagating gradients to Layer 4 bottleneck filters', icon: Eye },
    { label: 'Estimating Repair Costs & Labor Hours', desc: 'Evaluating damage severity against actuarial repair matrix', icon: Layers },
  ];

  useEffect(() => {
    const interval = setInterval(() => {
      setActiveStep((prev) => (prev < steps.length - 1 ? prev + 1 : prev));
    }, 450);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="max-w-xl mx-auto my-12">
      <div className="glass-panel rounded-2xl p-8 border-cyan-500/30 glow-cyan relative overflow-hidden text-center shadow-2xl">
        
        {/* Animated Scanner Laser Bar */}
        <div className="scan-line" />

        {/* Center Pulsing Radar */}
        <div className="relative w-24 h-24 mx-auto mb-6 flex items-center justify-center">
          <div className="absolute inset-0 rounded-full border border-cyan-500/20 animate-ping" />
          <div className="absolute inset-2 rounded-full border border-cyan-400/40 animate-pulse" />
          <div className="w-16 h-16 rounded-full bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/50">
            <Cpu className="w-8 h-8 text-white animate-spin" style={{ animationDuration: '4s' }} />
          </div>
        </div>

        <h3 className="text-xl font-black text-white mb-1">
          Analyzing Vehicle Surface...
        </h3>
        <p className="text-xs text-slate-400 mb-6">
          Neural network is isolating damaged regions and calculating repair estimates
        </p>

        {/* Step-by-step progress cards */}
        <div className="space-y-2.5 text-left max-w-md mx-auto">
          {steps.map((step, idx) => {
            const Icon = step.icon;
            const isDone = idx < activeStep;
            const isCurrent = idx === activeStep;

            return (
              <div 
                key={idx}
                className={`p-3 rounded-xl border transition-all duration-300 flex items-center gap-3 ${
                  isCurrent 
                    ? 'bg-cyan-950/40 border-cyan-500/60 shadow-sm shadow-cyan-500/20 text-cyan-200' 
                    : isDone
                    ? 'bg-slate-900/60 border-slate-700/60 text-slate-300'
                    : 'bg-slate-950/30 border-slate-800/40 text-slate-600'
                }`}
              >
                <div className={`p-1.5 rounded-lg shrink-0 ${
                  isCurrent ? 'bg-cyan-500/20 text-cyan-400' : isDone ? 'bg-emerald-500/20 text-emerald-400' : 'bg-slate-800 text-slate-600'
                }`}>
                  {isCurrent ? <Loader2 className="w-4 h-4 animate-spin" /> : <Icon className="w-4 h-4" />}
                </div>

                <div className="min-w-0 flex-1">
                  <div className="text-xs font-bold truncate">{step.label}</div>
                  <div className="text-[10px] text-slate-400 truncate">{step.desc}</div>
                </div>

                {isDone && (
                  <span className="text-[10px] text-emerald-400 font-mono font-bold shrink-0">DONE</span>
                )}
              </div>
            );
          })}
        </div>

      </div>
    </div>
  );
}

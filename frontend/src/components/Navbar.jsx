import React from 'react';
import { ShieldCheck, Car, History, BarChart3, Cpu, Sparkles, Activity } from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab, isApiOnline, onOpenSpecs }) {
  const navItems = [
    { id: 'inspect', label: 'AI Inspector', icon: Car },
    { id: 'history', label: 'Past Claims & History', icon: History },
    { id: 'analytics', label: 'Analytics Dashboard', icon: BarChart3 },
  ];

  return (
    <header className="sticky top-0 z-50 border-b border-slate-800/80 glass-panel">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          
          {/* Brand Logo */}
          <div 
            onClick={() => setActiveTab('inspect')}
            className="flex items-center gap-3 cursor-pointer group"
          >
            <div className="relative p-2 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 shadow-lg shadow-cyan-500/20 group-hover:scale-105 transition-transform duration-200">
              <Car className="w-6 h-6 text-white" />
              <div className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-emerald-400 rounded-full animate-ping" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-extrabold text-xl tracking-tight bg-gradient-to-r from-white via-slate-100 to-cyan-400 bg-clip-text text-transparent">
                  AutoInspect <span className="text-cyan-400">AI</span>
                </span>
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-cyan-950/80 text-cyan-400 border border-cyan-700/50 font-mono font-medium">
                  PRO v1.0
                </span>
              </div>
              <p className="text-xs text-slate-400 hidden sm:block">Intelligent Vehicle Damage & Cost Analytics</p>
            </div>
          </div>

          {/* Nav Items */}
          <nav className="flex items-center gap-1 sm:gap-2">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                    isActive
                      ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 shadow-sm shadow-cyan-500/10'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? 'text-cyan-400' : 'text-slate-400'}`} />
                  <span className="hidden md:inline">{item.label}</span>
                </button>
              );
            })}
          </nav>

          {/* System Status & Architecture Specs Button */}
          <div className="flex items-center gap-3">
            <button
              onClick={onOpenSpecs}
              className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs rounded-lg bg-slate-800/80 text-slate-300 border border-slate-700 hover:border-cyan-500/50 hover:text-cyan-300 transition-colors"
              title="View Model Architecture & GradCAM Specs"
            >
              <Cpu className="w-3.5 h-3.5 text-cyan-400" />
              <span className="hidden sm:inline">Model Specs</span>
            </button>

            <div className="flex items-center gap-2 px-2.5 py-1 rounded-full bg-slate-900/80 border border-slate-800 text-xs">
              <span className={`w-2 h-2 rounded-full ${isApiOnline ? 'bg-emerald-400 shadow-[0_0_8px_#34d399]' : 'bg-rose-500'}`} />
              <span className="text-slate-300 font-mono text-[11px]">
                {isApiOnline ? 'PyTorch Online' : 'Connecting...'}
              </span>
            </div>
          </div>

        </div>
      </div>
    </header>
  );
}

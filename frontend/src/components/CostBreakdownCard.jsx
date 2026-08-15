import React from 'react';
import { DollarSign, Wrench, Paintbrush, Package, FileSpreadsheet, ShieldAlert } from 'lucide-react';

export default function CostBreakdownCard({ estimatedCost, severity, confidence }) {
  if (!estimatedCost) return null;

  const { min, max, currency = 'USD', details = {} } = estimatedCost;
  const {
    labor_hours = 2.0,
    labor_cost = 190.0,
    paint_cost = 150.0,
    parts_cost = 50.0,
    action_summary = 'Standard vehicle body restoration protocol'
  } = details;

  return (
    <div className="glass-card rounded-2xl p-5 border-slate-800 space-y-4">
      
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-emerald-500/20 text-emerald-400">
            <DollarSign className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white">Estimated Claim & Repair Valuation</h3>
            <p className="text-[11px] text-slate-400">Actuarial rule-based repair pricing model</p>
          </div>
        </div>

        <div className="text-right">
          <span className="text-xs text-slate-400 font-mono">ESTIMATED TOTAL</span>
          <div className="text-xl sm:text-2xl font-black text-cyan-400 tracking-tight">
            ${min?.toLocaleString()} – ${max?.toLocaleString()}
            <span className="text-xs font-normal text-slate-400 ml-1">USD</span>
          </div>
        </div>
      </div>

      {/* Itemized Line Items */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {/* Labor Item */}
        <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
          <div className="flex items-center gap-2 text-slate-400 text-xs font-medium mb-1">
            <Wrench className="w-3.5 h-3.5 text-cyan-400" />
            <span>Body Shop Labor</span>
          </div>
          <div className="text-base font-bold text-white">${labor_cost?.toLocaleString()}</div>
          <div className="text-[10px] text-slate-500 font-mono">{labor_hours} hrs @ $95/hr</div>
        </div>

        {/* Paint Item */}
        <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
          <div className="flex items-center gap-2 text-slate-400 text-xs font-medium mb-1">
            <Paintbrush className="w-3.5 h-3.5 text-sky-400" />
            <span>Paint & Refinishing</span>
          </div>
          <div className="text-base font-bold text-white">${paint_cost?.toLocaleString()}</div>
          <div className="text-[10px] text-slate-500 font-mono">Primer + UV clear coat</div>
        </div>

        {/* Parts Item */}
        <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
          <div className="flex items-center gap-2 text-slate-400 text-xs font-medium mb-1">
            <Package className="w-3.5 h-3.5 text-amber-400" />
            <span>OEM Parts & Clips</span>
          </div>
          <div className="text-base font-bold text-white">${parts_cost?.toLocaleString()}</div>
          <div className="text-[10px] text-slate-500 font-mono">Hardware replacement</div>
        </div>
      </div>

      {/* Repair Action Protocol */}
      <div className="p-3 rounded-xl bg-cyan-950/20 border border-cyan-900/40 text-xs">
        <div className="font-bold text-cyan-300 mb-0.5 flex items-center gap-1.5">
          <FileSpreadsheet className="w-3.5 h-3.5 text-cyan-400" />
          <span>Recommended Repair Protocol:</span>
        </div>
        <p className="text-slate-300 leading-relaxed text-[11px]">
          {action_summary}
        </p>
      </div>

    </div>
  );
}

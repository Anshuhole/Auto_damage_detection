import React, { useState, useEffect } from 'react';
import { 
  BarChart3, Activity, ShieldAlert, DollarSign, 
  Layers, CheckCircle2, TrendingUp, PieChart, RefreshCw 
} from 'lucide-react';
import { getStats } from '../services/api';

export default function StatsDashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchStatsData = async () => {
    setLoading(true);
    try {
      const data = await getStats();
      setStats(data);
    } catch (err) {
      console.error('Failed to load dashboard stats:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatsData();
  }, []);

  if (loading) {
    return (
      <div className="glass-panel rounded-2xl p-12 text-center border-slate-800 max-w-4xl mx-auto">
        <RefreshCw className="w-8 h-8 text-cyan-400 animate-spin mx-auto mb-3" />
        <p className="text-xs text-slate-400">Aggregating inspection metrics & claim values...</p>
      </div>
    );
  }

  const {
    total_inspections = 0,
    damaged_count = 0,
    clean_count = 0,
    damage_rate_percentage = 0,
    avg_estimated_cost = 0,
    damage_distribution = {},
    severity_distribution = {}
  } = stats || {};

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      
      {/* Top Banner */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-cyan-400" />
            <span>Inspection Intelligence & Analytics</span>
          </h2>
          <p className="text-xs text-slate-400">Real-time aggregate telemetry across all scanned vehicles</p>
        </div>

        <button
          onClick={fetchStatsData}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs border border-slate-700 transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh Data</span>
        </button>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* KPI 1 */}
        <div className="glass-panel rounded-2xl p-5 border-slate-800 relative overflow-hidden">
          <div className="flex items-center justify-between text-slate-400 text-xs font-semibold mb-2">
            <span>Total Appraisals</span>
            <Activity className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-3xl font-black text-white">{total_inspections}</div>
          <div className="text-[11px] text-emerald-400 mt-1 font-mono">
            {clean_count} pristine / {damaged_count} damaged
          </div>
        </div>

        {/* KPI 2 */}
        <div className="glass-panel rounded-2xl p-5 border-slate-800 relative overflow-hidden">
          <div className="flex items-center justify-between text-slate-400 text-xs font-semibold mb-2">
            <span>Damage Incident Rate</span>
            <ShieldAlert className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-3xl font-black text-amber-400">{damage_rate_percentage}%</div>
          <div className="text-[11px] text-slate-400 mt-1 font-mono">
            Requires body shop adjustment
          </div>
        </div>

        {/* KPI 3 */}
        <div className="glass-panel rounded-2xl p-5 border-slate-800 relative overflow-hidden">
          <div className="flex items-center justify-between text-slate-400 text-xs font-semibold mb-2">
            <span>Avg Claim Estimate</span>
            <DollarSign className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-3xl font-black text-emerald-400">
            ${avg_estimated_cost.toLocaleString()}
          </div>
          <div className="text-[11px] text-slate-400 mt-1 font-mono">
            USD per damaged vehicle
          </div>
        </div>

        {/* KPI 4 */}
        <div className="glass-panel rounded-2xl p-5 border-slate-800 relative overflow-hidden">
          <div className="flex items-center justify-between text-slate-400 text-xs font-semibold mb-2">
            <span>Severe Incidents</span>
            <TrendingUp className="w-4 h-4 text-rose-400" />
          </div>
          <div className="text-3xl font-black text-rose-400">
            {severity_distribution['severe'] || 0}
          </div>
          <div className="text-[11px] text-slate-400 mt-1 font-mono">
            Major panel / glass replacement
          </div>
        </div>
      </div>

      {/* Breakdown Charts Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* Category Breakdown */}
        <div className="glass-panel rounded-2xl p-6 border-slate-800 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Layers className="w-4 h-4 text-cyan-400" />
              <span>Damage Category Distribution</span>
            </h3>
            <span className="text-xs text-slate-400 font-mono">Total: {total_inspections}</span>
          </div>

          <div className="space-y-3">
            {Object.entries(damage_distribution).map(([cat, count]) => {
              const pct = total_inspections > 0 ? (count / total_inspections) * 100 : 0;
              return (
                <div key={cat} className="space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="capitalize text-slate-300 font-medium">
                      {cat.replace('_', ' ')}
                    </span>
                    <span className="font-mono text-slate-400">
                      {count} ({pct.toFixed(0)}%)
                    </span>
                  </div>
                  <div className="w-full h-2 bg-slate-900 rounded-full overflow-hidden border border-slate-800">
                    <div
                      className="h-full bg-gradient-to-r from-cyan-500 to-blue-500 rounded-full"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Severity Breakdown */}
        <div className="glass-panel rounded-2xl p-6 border-slate-800 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <PieChart className="w-4 h-4 text-emerald-400" />
              <span>Severity Tier Breakdown</span>
            </h3>
            <span className="text-xs text-slate-400 font-mono">Severity Tiers</span>
          </div>

          <div className="space-y-3">
            {Object.entries(severity_distribution).map(([sev, count]) => {
              const pct = total_inspections > 0 ? (count / total_inspections) * 100 : 0;
              const colorClass = 
                sev === 'severe' ? 'from-rose-500 to-red-600' :
                sev === 'moderate' ? 'from-amber-500 to-orange-500' :
                sev === 'minor' ? 'from-emerald-500 to-teal-500' : 'from-cyan-500 to-blue-500';

              return (
                <div key={sev} className="space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="capitalize text-slate-300 font-medium">{sev}</span>
                    <span className="font-mono text-slate-400">
                      {count} ({pct.toFixed(0)}%)
                    </span>
                  </div>
                  <div className="w-full h-2 bg-slate-900 rounded-full overflow-hidden border border-slate-800">
                    <div
                      className={`h-full bg-gradient-to-r ${colorClass} rounded-full`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

      </div>

    </div>
  );
}

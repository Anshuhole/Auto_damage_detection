import React, { useState, useEffect } from 'react';
import { 
  Search, Filter, FileDown, Trash2, Eye, Calendar, 
  DollarSign, AlertCircle, RefreshCw, Car, ChevronRight 
} from 'lucide-react';
import { getHistory, deleteInspection, getReportPdfUrl } from '../services/api';

export default function InspectionHistory({ onSelectInspection, onNewScan }) {
  const [records, setRecords] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedSeverity, setSelectedSeverity] = useState('all');
  const [selectedType, setSelectedType] = useState('all');

  const fetchRecords = async () => {
    setLoading(true);
    try {
      const data = await getHistory({
        search,
        severity: selectedSeverity,
        damage_type: selectedType,
        limit: 50,
      });
      setRecords(data.items || []);
      setTotal(data.total || 0);
    } catch (err) {
      console.error('Failed to load history:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecords();
  }, [selectedSeverity, selectedType]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchRecords();
  };

  const handleDelete = async (id, e) => {
    e.stopPropagation();
    if (!window.confirm(`Are you sure you want to delete inspection record ${id}?`)) return;
    try {
      await deleteInspection(id);
      setRecords((prev) => prev.filter((r) => r.id !== id));
      setTotal((prev) => prev - 1);
    } catch (err) {
      alert('Failed to delete inspection.');
    }
  };

  const handleDownloadPdf = (id, e) => {
    e.stopPropagation();
    window.open(getReportPdfUrl(id), '_blank');
  };

  const getSeverityBadgeClass = (sev) => {
    switch (sev?.toLowerCase()) {
      case 'severe':
        return 'bg-rose-950 text-rose-300 border-rose-800';
      case 'moderate':
        return 'bg-amber-950 text-amber-300 border-amber-800';
      case 'minor':
        return 'bg-emerald-950 text-emerald-300 border-emerald-800';
      default:
        return 'bg-cyan-950 text-cyan-300 border-cyan-800';
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      
      {/* Header & Filter Controls */}
      <div className="glass-panel rounded-2xl p-6 border-slate-800 shadow-xl space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <Car className="w-5 h-5 text-cyan-400" />
              <span>Inspection Claim History & Database</span>
            </h2>
            <p className="text-xs text-slate-400">
              {total} verified vehicle appraisals logged in SQLite system
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={fetchRecords}
              className="p-2 rounded-xl bg-slate-800 text-slate-300 hover:text-white border border-slate-700 hover:border-cyan-500/40 transition-colors"
              title="Refresh History"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
            <button
              onClick={onNewScan}
              className="px-4 py-2 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-bold text-xs shadow-lg shadow-cyan-500/20"
            >
              + New Inspection
            </button>
          </div>
        </div>

        {/* Filter Controls Bar */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
          {/* Search bar */}
          <form onSubmit={handleSearchSubmit} className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search by ID or damage type..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-xl pl-9 pr-4 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
            />
          </form>

          {/* Severity Dropdown */}
          <div className="flex items-center gap-2 bg-slate-900 border border-slate-700 rounded-xl px-3 py-1.5">
            <Filter className="w-3.5 h-3.5 text-slate-400 shrink-0" />
            <span className="text-[11px] text-slate-400 shrink-0">Severity:</span>
            <select
              value={selectedSeverity}
              onChange={(e) => setSelectedSeverity(e.target.value)}
              className="bg-transparent border-none text-xs text-slate-200 focus:outline-none w-full cursor-pointer"
            >
              <option value="all" className="bg-dark-900">All Severities</option>
              <option value="minor" className="bg-dark-900">Minor</option>
              <option value="moderate" className="bg-dark-900">Moderate</option>
              <option value="severe" className="bg-dark-900">Severe</option>
              <option value="none" className="bg-dark-900">No Damage</option>
            </select>
          </div>

          {/* Damage Type Dropdown */}
          <div className="flex items-center gap-2 bg-slate-900 border border-slate-700 rounded-xl px-3 py-1.5">
            <Car className="w-3.5 h-3.5 text-slate-400 shrink-0" />
            <span className="text-[11px] text-slate-400 shrink-0">Category:</span>
            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
              className="bg-transparent border-none text-xs text-slate-200 focus:outline-none w-full cursor-pointer"
            >
              <option value="all" className="bg-dark-900">All Categories</option>
              <option value="scratch" className="bg-dark-900">Scratch</option>
              <option value="dent" className="bg-dark-900">Dent</option>
              <option value="crack" className="bg-dark-900">Crack</option>
              <option value="shattered_glass" className="bg-dark-900">Shattered Glass</option>
              <option value="no_damage" className="bg-dark-900">Clean / No Damage</option>
            </select>
          </div>
        </div>
      </div>

      {/* History Records Table / Grid */}
      {loading ? (
        <div className="glass-panel rounded-2xl p-12 text-center border-slate-800">
          <RefreshCw className="w-8 h-8 text-cyan-400 animate-spin mx-auto mb-3" />
          <p className="text-xs text-slate-400">Loading historical inspection logs...</p>
        </div>
      ) : records.length === 0 ? (
        <div className="glass-panel rounded-2xl p-12 text-center border-slate-800 space-y-4">
          <div className="w-14 h-14 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center mx-auto text-slate-500">
            <AlertCircle className="w-7 h-7" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white mb-1">No Past Inspections Found</h3>
            <p className="text-xs text-slate-400 max-w-sm mx-auto">
              Run your first vehicle damage inspection or adjust search query filters.
            </p>
          </div>
          <button
            onClick={onNewScan}
            className="px-5 py-2.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-bold shadow-lg shadow-cyan-500/20"
          >
            Launch Inspector
          </button>
        </div>
      ) : (
        <div className="glass-panel rounded-2xl border-slate-800 overflow-hidden shadow-2xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-900/90 border-b border-slate-800 text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                  <th className="py-3.5 px-4">Thumbnail</th>
                  <th className="py-3.5 px-4">Inspection ID</th>
                  <th className="py-3.5 px-4">Damage Classification</th>
                  <th className="py-3.5 px-4">Severity</th>
                  <th className="py-3.5 px-4">Confidence</th>
                  <th className="py-3.5 px-4">Estimated Range</th>
                  <th className="py-3.5 px-4">Date</th>
                  <th className="py-3.5 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-xs">
                {records.map((item) => {
                  const badgeClass = getSeverityBadgeClass(item.severity);
                  const cost = item.estimated_cost || {};

                  return (
                    <tr
                      key={item.id}
                      onClick={() => onSelectInspection(item.id)}
                      className="hover:bg-slate-800/40 cursor-pointer transition-colors group"
                    >
                      {/* Thumbnail */}
                      <td className="py-3 px-4">
                        <div className="w-14 h-10 rounded-lg overflow-hidden bg-black border border-slate-700/80 group-hover:border-cyan-500/60 transition-colors">
                          <img
                            src={item.original_image_url}
                            alt="Vehicle Preview"
                            className="w-full h-full object-cover"
                          />
                        </div>
                      </td>

                      {/* ID */}
                      <td className="py-3 px-4 font-mono font-bold text-slate-200">
                        {item.id}
                      </td>

                      {/* Classification */}
                      <td className="py-3 px-4">
                        <div className="font-semibold text-white">
                          {item.damage_display_name}
                        </div>
                        <div className="text-[10px] text-slate-400 font-mono capitalize">
                          {item.damage_type.replace('_', ' ')}
                        </div>
                      </td>

                      {/* Severity */}
                      <td className="py-3 px-4">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-extrabold uppercase border ${badgeClass}`}>
                          {item.severity}
                        </span>
                      </td>

                      {/* Confidence */}
                      <td className="py-3 px-4 font-mono text-cyan-400 font-bold">
                        {(item.confidence * 100).toFixed(1)}%
                      </td>

                      {/* Cost */}
                      <td className="py-3 px-4">
                        <div className="font-bold text-slate-200">
                          ${cost.min?.toLocaleString()} – ${cost.max?.toLocaleString()}
                        </div>
                        <div className="text-[10px] text-slate-400">USD</div>
                      </td>

                      {/* Date */}
                      <td className="py-3 px-4 text-slate-400 font-mono text-[11px]">
                        {item.created_at ? new Date(item.created_at).toLocaleDateString() : 'Recent'}
                      </td>

                      {/* Actions */}
                      <td className="py-3 px-4 text-right">
                        <div className="flex items-center justify-end gap-1.5" onClick={(e) => e.stopPropagation()}>
                          <button
                            onClick={(e) => handleDownloadPdf(item.id, e)}
                            className="p-1.5 rounded-lg bg-slate-800 text-slate-300 hover:text-cyan-300 hover:bg-slate-700 transition-colors"
                            title="Download PDF"
                          >
                            <FileDown className="w-4 h-4" />
                          </button>
                          <button
                            onClick={(e) => handleDelete(item.id, e)}
                            className="p-1.5 rounded-lg bg-slate-800 text-slate-300 hover:text-rose-400 hover:bg-rose-950/50 transition-colors"
                            title="Delete Record"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

    </div>
  );
}

import React, { useState, useEffect } from 'react';
import { X, FileDown, Eye, DollarSign, Calendar, Wrench, ShieldCheck, RefreshCw } from 'lucide-react';
import { getInspectionDetail, getReportPdfUrl } from '../services/api';
import GradCamViewer from './GradCamViewer';
import CostBreakdownCard from './CostBreakdownCard';

export default function InspectionModal({ inspectionId, onClose }) {
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!inspectionId) return;
    const fetchDetail = async () => {
      setLoading(true);
      try {
        const data = await getInspectionDetail(inspectionId);
        setDetail(data);
      } catch (err) {
        console.error('Failed to load inspection detail:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchDetail();
  }, [inspectionId]);

  if (!inspectionId) return null;

  const handleDownloadPdf = () => {
    window.open(getReportPdfUrl(inspectionId), '_blank');
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4 overflow-y-auto">
      <div className="relative w-full max-w-4xl bg-dark-900 border border-slate-700 rounded-2xl overflow-hidden shadow-2xl my-8">
        
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-900/80 sticky top-0 z-20">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono text-cyan-400 font-bold">{inspectionId}</span>
              <span className="text-xs text-slate-500">•</span>
              <span className="text-xs text-slate-400">
                {detail?.created_at ? new Date(detail.created_at).toLocaleString() : 'Inspection Record'}
              </span>
            </div>
            <h3 className="text-lg font-bold text-white">
              {detail?.damage_display_name || 'Loading Inspection...'}
            </h3>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleDownloadPdf}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-bold shadow-sm transition-colors"
            >
              <FileDown className="w-4 h-4" />
              <span>Download PDF</span>
            </button>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Modal Content */}
        <div className="p-6 space-y-6 max-h-[80vh] overflow-y-auto">
          {loading ? (
            <div className="text-center py-16">
              <RefreshCw className="w-8 h-8 text-cyan-400 animate-spin mx-auto mb-3" />
              <p className="text-xs text-slate-400">Loading appraisal record...</p>
            </div>
          ) : detail ? (
            <>
              {/* Grad-CAM Viewer */}
              <GradCamViewer
                originalImageUrl={detail.original_image_url}
                gradcamImageUrl={detail.gradcam_image_url}
                boundingBoxes={detail.bounding_boxes}
                damageType={detail.damage_type}
              />

              {/* Cost Estimate Breakdown */}
              <CostBreakdownCard
                estimatedCost={detail.estimated_cost}
                severity={detail.severity}
                confidence={detail.confidence}
              />

              {/* Inspector Notes */}
              {detail.notes && (
                <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 text-xs">
                  <span className="font-bold text-slate-300">Inspector Notes:</span>
                  <p className="text-slate-400 mt-1 italic">&ldquo;{detail.notes}&rdquo;</p>
                </div>
              )}
            </>
          ) : (
            <p className="text-center text-slate-400 py-12">Failed to load record details.</p>
          )}
        </div>

      </div>
    </div>
  );
}

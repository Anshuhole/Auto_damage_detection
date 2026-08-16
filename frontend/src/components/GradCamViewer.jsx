import React, { useState } from 'react';
import { Eye, Sliders, Layers, Maximize2, SplitSquareHorizontal, CheckSquare, Square, CheckCircle2, Flame } from 'lucide-react';

export default function GradCamViewer({ 
  originalImageUrl, 
  gradcamImageUrl, 
  boundingBoxes = [], 
  damageType 
}) {
  const [opacity, setOpacity] = useState(100); // Default 100% full thermal heat opacity
  const [viewMode, setViewMode] = useState('overlay'); // 'overlay' | 'side-by-side'
  const [showBoxes, setShowBoxes] = useState(true);

  const isClean = damageType === 'no_damage' || boundingBoxes.length === 0;

  return (
    <div className="glass-card rounded-2xl p-5 border-slate-800 space-y-4">
      
      {/* Control Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <Eye className="w-5 h-5 text-cyan-400" />
          <h3 className="text-sm font-bold text-white">Visual Explainability (Grad-CAM Heatmap)</h3>
        </div>

        <div className="flex items-center gap-2">
          {/* Mode Switch */}
          <div className="bg-slate-900 rounded-lg p-0.5 border border-slate-800 flex items-center text-xs font-semibold">
            <button
              onClick={() => setViewMode('overlay')}
              className={`px-2.5 py-1 rounded-md transition-colors ${
                viewMode === 'overlay' ? 'bg-cyan-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Interactive Overlay
            </button>
            <button
              onClick={() => setViewMode('side-by-side')}
              className={`px-2.5 py-1 rounded-md transition-colors ${
                viewMode === 'side-by-side' ? 'bg-cyan-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Side-by-Side
            </button>
          </div>

          {/* Bounding Box Toggle */}
          <button
            onClick={() => setShowBoxes(!showBoxes)}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium border transition-colors ${
              showBoxes 
                ? 'bg-cyan-950/60 border-cyan-700/60 text-cyan-300' 
                : 'bg-slate-900 border-slate-800 text-slate-400'
            }`}
          >
            {showBoxes ? <CheckSquare className="w-3.5 h-3.5 text-cyan-400" /> : <Square className="w-3.5 h-3.5" />}
            <span className="hidden sm:inline">Bounding Box</span>
          </button>
        </div>
      </div>

      {/* Main View Area */}
      {viewMode === 'overlay' ? (
        <div className="space-y-3">
          {/* Overlay Viewport: Image-relative container to ensure pixel-perfect bounding box alignment */}
          <div className="rounded-xl overflow-hidden bg-slate-950 border border-slate-700 flex items-center justify-center p-1 min-h-[300px]">
            <div className="relative inline-block max-w-full max-h-[500px]">
              
              {/* Base: Original Image */}
              <img
                src={originalImageUrl}
                alt="Original Vehicle Photo"
                className="block max-w-full max-h-[500px] w-auto h-auto rounded-lg object-contain"
              />

              {/* Top: Grad-CAM Overlay with dynamic opacity */}
              {!isClean && (
                <img
                  src={gradcamImageUrl}
                  alt="Grad-CAM Activation Overlay"
                  style={{ opacity: opacity / 100 }}
                  className="absolute inset-0 w-full h-full rounded-lg object-fill pointer-events-none transition-opacity duration-75"
                />
              )}

              {/* Pixel-Perfect Bounding Boxes */}
              {showBoxes && !isClean && boundingBoxes.map((box, idx) => (
                <div
                  key={idx}
                  style={{
                    top: `${box.y * 100}%`,
                    left: `${box.x * 100}%`,
                    width: `${box.width * 100}%`,
                    height: `${box.height * 100}%`,
                  }}
                  className="absolute border-2 border-dashed border-cyan-400 bg-cyan-400/15 rounded pointer-events-none transition-all shadow-[0_0_15px_rgba(6,182,212,0.8)] z-10"
                >
                  <span className="absolute -top-6 left-0 bg-cyan-500 text-slate-950 text-[10px] font-black uppercase px-2 py-0.5 rounded tracking-wide shadow-md whitespace-nowrap">
                    {box.label || `Damage Zone ${(box.confidence * 100).toFixed(0)}%`}
                  </span>
                </div>
              ))}

              {/* Clean Car Badge */}
              {isClean && (
                <div className="absolute top-3 right-3 bg-emerald-950/90 border border-emerald-500/50 text-emerald-300 text-xs px-3 py-1.5 rounded-lg flex items-center gap-1.5 shadow-lg backdrop-blur-md">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  <span className="font-semibold">Pristine Vehicle — Zero Damage Hotspots</span>
                </div>
              )}

              {/* Overlay Indicator Badge */}
              <div className="absolute bottom-3 left-3 bg-slate-950/85 backdrop-blur-md px-2.5 py-1 rounded-md border border-slate-700 text-[11px] font-mono text-slate-300 flex items-center gap-1.5">
                <Flame className="w-3 h-3 text-red-400" />
                Opacity: <span className="text-cyan-400 font-bold">{opacity}%</span>
              </div>
            </div>
          </div>

          {/* Interactive Thermal Opacity Scrollbar / Slider */}
          {!isClean && (
            <div className="space-y-2 pt-2 bg-slate-900/60 p-3 rounded-xl border border-slate-800/80">
              <div className="flex items-center justify-between text-xs font-semibold">
                <span className="flex items-center gap-1.5 text-slate-400">
                  <Sliders className="w-3.5 h-3.5 text-slate-400" /> Original Paint (0%)
                </span>
                
                {/* Preset Quick Buttons */}
                <div className="flex items-center gap-1.5">
                  {[25, 50, 75, 100].map((val) => (
                    <button
                      key={val}
                      onClick={() => setOpacity(val)}
                      className={`text-[10px] px-2 py-0.5 rounded font-mono transition-colors ${
                        opacity === val 
                          ? 'bg-cyan-500 text-slate-950 font-bold shadow-sm' 
                          : 'bg-slate-800 text-slate-400 hover:text-white hover:bg-slate-700'
                      }`}
                    >
                      {val}%
                    </button>
                  ))}
                </div>

                <span className="text-cyan-400 font-bold flex items-center gap-1.5">
                  <Flame className="w-3.5 h-3.5 text-red-400" />
                  Thermal Heat: <span className="font-mono text-white bg-slate-800 px-2 py-0.5 rounded border border-slate-700">{opacity}%</span>
                </span>
              </div>

              {/* Glowing Range Scrollbar */}
              <div className="relative flex items-center pt-1">
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={opacity}
                  onChange={(e) => setOpacity(Number(e.target.value))}
                  className="w-full h-3 bg-gradient-to-r from-slate-800 via-sky-950 to-cyan-900 rounded-lg appearance-none cursor-pointer accent-cyan-400 focus:outline-none shadow-inner border border-slate-700/60"
                />
              </div>
            </div>
          )}

          {/* Heatmap Spectrum Legend */}
          <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1">
            <span>Low Activation (Normal Paint)</span>
            <div className="h-2 w-36 rounded-full bg-gradient-to-r from-blue-600 via-yellow-400 to-red-600 mx-2 shadow-sm" />
            <span className="text-red-400 font-medium">High Damage Anomaly</span>
          </div>
        </div>
      ) : (
        /* Side-by-Side Comparison Mode */
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-1.5">
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-slate-400"></span> Original Vehicle Photo
            </div>
            <div className="rounded-xl overflow-hidden bg-slate-950 border border-slate-800 p-1 flex items-center justify-center">
              <img
                src={originalImageUrl}
                alt="Original Vehicle"
                className="max-h-[350px] w-auto h-auto rounded-lg object-contain"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <div className="text-xs font-semibold text-cyan-400 uppercase tracking-wider flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span> Grad-CAM Neural Activation
            </div>
            <div className="rounded-xl overflow-hidden bg-slate-950 border border-cyan-900/50 p-1 flex items-center justify-center">
              <img
                src={isClean ? originalImageUrl : gradcamImageUrl}
                alt="Grad-CAM Thermal Heatmap"
                className="max-h-[350px] w-auto h-auto rounded-lg object-contain"
              />
            </div>
          </div>
        </div>
      )}

    </div>
  );
}

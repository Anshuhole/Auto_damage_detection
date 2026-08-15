import React from 'react';
import { Zap } from 'lucide-react';

export const SAMPLE_CARS = [
  {
    id: 'sample_dent',
    name: 'Door Panel Dent',
    type: 'dent',
    badge: 'Dent',
    badgeColor: 'bg-amber-950 text-amber-300 border-amber-800',
    description: 'Deep mechanical deformation on passenger door panel',
    imageSrc: '/samples/sample_dent.jpeg'
  },
  {
    id: 'sample_scratch',
    name: 'Fender Key Scratch',
    type: 'scratch',
    badge: 'Scratch',
    badgeColor: 'bg-blue-950 text-blue-300 border-blue-800',
    description: 'Surface clear-coat & primer scratches along front quarter panel',
    imageSrc: '/samples/sample_scratch.jpeg'
  },
  {
    id: 'sample_crack',
    name: 'Bumper Crack & Split',
    type: 'crack',
    badge: 'Crack',
    badgeColor: 'bg-rose-950 text-rose-300 border-rose-800',
    description: 'Structural fracture across lower front bumper fascia',
    imageSrc: '/samples/sample_crack.jpeg'
  },
  {
    id: 'sample_glass',
    name: 'Shattered Windshield',
    type: 'shattered_glass',
    badge: 'Glass',
    badgeColor: 'bg-cyan-950 text-cyan-300 border-cyan-800',
    description: 'Spiderweb impact fracture on front glass windshield',
    imageSrc: '/samples/sample_glass.jpeg'
  },
  {
    id: 'sample_clean',
    name: 'Pristine Vehicle (Clean)',
    type: 'no_damage',
    badge: 'Clean',
    badgeColor: 'bg-emerald-950 text-emerald-300 border-emerald-800',
    description: 'Flawless vehicle body panels, no structural or paint defects',
    imageSrc: '/samples/sample_clean.jpg'
  }
];

export default function SampleCarGallery({ onSelectSample, isAnalyzing }) {
  return (
    <div className="mt-8">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Zap className="w-4 h-4 text-cyan-400" />
          <span className="text-xs font-bold uppercase tracking-wider text-slate-300">
            Instant Demo Presets (1-Click Real Car Test Runs)
          </span>
        </div>
        <span className="text-xs text-slate-500">Select any preset to test AI pipeline instantly</span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        {SAMPLE_CARS.map((sample) => (
          <button
            key={sample.id}
            disabled={isAnalyzing}
            onClick={() => onSelectSample(sample)}
            className="group glass-card rounded-xl p-2.5 text-left border-slate-800/90 hover:border-cyan-500/50 hover:bg-slate-800/80 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-cyan-500/40 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {/* Visual Thumbnail */}
            <div className="relative aspect-[16/10] rounded-lg overflow-hidden bg-slate-900 border border-slate-800 mb-2 group-hover:scale-[1.02] transition-transform">
              <img 
                src={sample.imageSrc} 
                alt={sample.name} 
                className="w-full h-full object-cover"
                loading="lazy"
              />
              <div className="absolute top-1.5 right-1.5">
                <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded border ${sample.badgeColor}`}>
                  {sample.badge}
                </span>
              </div>
            </div>

            {/* Label */}
            <div className="font-semibold text-xs text-slate-200 truncate group-hover:text-cyan-300">
              {sample.name}
            </div>
            <p className="text-[10px] text-slate-400 line-clamp-1 mt-0.5">
              {sample.description}
            </p>
          </button>
        ))}
      </div>
    </div>
  );
}

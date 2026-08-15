import React from 'react';
import { X, Cpu, Eye, Layers, ShieldCheck, Code, CheckCircle2, Zap } from 'lucide-react';

export default function ModelSpecsModal({ onClose }) {
  return (
    <div className="fixed inset-0 z-50 bg-black/85 backdrop-blur-md flex items-center justify-center p-4 overflow-y-auto">
      <div className="relative w-full max-w-4xl bg-dark-900 border border-slate-700 rounded-2xl overflow-hidden shadow-2xl my-8">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-900/80 sticky top-0 z-20">
          <div className="flex items-center gap-2.5">
            <Cpu className="w-5 h-5 text-cyan-400" />
            <div>
              <h3 className="text-base font-bold text-white">System Architecture & Model Specifications</h3>
              <p className="text-xs text-slate-400">Technical deep-dive & technical interview reference guide</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6 max-h-[80vh] overflow-y-auto text-xs text-slate-300">
          
          {/* Section 1: Transfer Learning Backbone */}
          <div className="glass-card rounded-xl p-4 border-slate-800 space-y-2">
            <div className="flex items-center gap-2 text-cyan-400 font-bold text-sm">
              <Cpu className="w-4 h-4" />
              <span>1. Neural Network Architecture: Pretrained ResNet50</span>
            </div>
            <p className="text-slate-400 leading-relaxed">
              We leverage an ImageNet pretrained <strong className="text-slate-200">ResNet50</strong> (50-layer deep residual network) backbone. 
              The early layers capture general visual primitives (edges, gradients, textures), while the fine-tuned bottleneck blocks in <code className="text-cyan-300">layer4</code> capture high-level automotive panel deformation and paint fracture features.
            </p>
            <div className="bg-slate-950 p-3 rounded-lg font-mono text-[11px] text-slate-300 border border-slate-800 space-y-1">
              <div>Backbone : ResNet50 (in_features = 2048)</div>
              <div>Shared FC: Linear(2048 -&gt; 512) -&gt; BatchNorm -&gt; ReLU -&gt; Dropout(0.35)</div>
              <div>Head 1   : Damage Class [scratch, dent, crack, shattered_glass, no_damage]</div>
              <div>Head 2   : Severity Level [minor, moderate, severe, none]</div>
            </div>
          </div>

          {/* Section 2: Explainability with Grad-CAM */}
          <div className="glass-card rounded-xl p-4 border-slate-800 space-y-2">
            <div className="flex items-center gap-2 text-sky-400 font-bold text-sm">
              <Eye className="w-4 h-4" />
              <span>2. Visual Explainability: Grad-CAM Formulation</span>
            </div>
            <p className="text-slate-400 leading-relaxed">
              Gradient-weighted Class Activation Mapping (Grad-CAM) computes the gradients of the predicted class score $y^c$ with respect to the feature map activations $A^k$ of the final convolutional layer:
            </p>
            <div className="bg-slate-950 p-3 rounded-lg font-mono text-[11px] text-cyan-300 border border-slate-800">
              α_k^c = (1 / Z) * Σ_i Σ_j (∂y^c / ∂A_{i,j}^k)<br/>
              L_{Grad-CAM}^c = ReLU( Σ_k α_k^c * A^k )
            </div>
            <p className="text-slate-400 leading-relaxed">
              Positive influence weights $\alpha_k^c$ highlight the exact pixels that caused the model to predict damage, eliminating black-box opacity for claims adjusters.
            </p>
          </div>

          {/* Section 3: Cost Estimation Matrix */}
          <div className="glass-card rounded-xl p-4 border-slate-800 space-y-2">
            <div className="flex items-center gap-2 text-emerald-400 font-bold text-sm">
              <Layers className="w-4 h-4" />
              <span>3. Actuarial Repair Cost Valuation Matrix</span>
            </div>
            <p className="text-slate-400 leading-relaxed">
              The rule-based cost engine combines body shop labor rates ($95.00/hr), panel paint/refinishing charges, OEM hardware costs, and severity multipliers:
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px] font-mono">
              <div className="bg-slate-950 p-2.5 rounded border border-slate-800">
                <span className="text-emerald-400 font-bold">Scratch:</span> $120–$280 (Minor) / $300–$650 (Mod) / $700–$1400 (Sev)
              </div>
              <div className="bg-slate-950 p-2.5 rounded border border-slate-800">
                <span className="text-amber-400 font-bold">Dent:</span> $150–$350 (Minor) / $400–$950 (Mod) / $1100–$2800 (Sev)
              </div>
              <div className="bg-slate-950 p-2.5 rounded border border-slate-800">
                <span className="text-rose-400 font-bold">Crack:</span> $200–$450 (Minor) / $500–$1100 (Mod) / $1200–$3200 (Sev)
              </div>
              <div className="bg-slate-950 p-2.5 rounded border border-slate-800">
                <span className="text-cyan-400 font-bold">Glass:</span> $180–$350 (Minor) / $400–$850 (Mod) / $900–$2200 (Sev)
              </div>
            </div>
          </div>

          {/* Section 4: Key Interview Highlights */}
          <div className="glass-card rounded-xl p-4 border-slate-800 space-y-2">
            <div className="flex items-center gap-2 text-amber-400 font-bold text-sm">
              <Zap className="w-4 h-4" />
              <span>4. Key Resume & Interview Discussion Points</span>
            </div>
            <ul className="space-y-1.5 list-disc list-inside text-slate-300">
              <li><strong className="text-white">Explainability First:</strong> Integrated Grad-CAM to prevent catastrophic insurance misclassifications and provide visual proof for adjusters.</li>
              <li><strong className="text-white">Modular Micro-services:</strong> PyTorch inference decoupled from FastAPI asynchronous routes and SQLite relational persistence.</li>
              <li><strong className="text-white">Automated Claim Generation:</strong> Instant PDF synthesis via ReportLab embedding side-by-side Grad-CAM visualizations and itemized breakdowns.</li>
              <li><strong className="text-white">Field Inspection Ready:</strong> Full webcam HUD capture and drag-drop support for field appraisers on mobile/desktop.</li>
            </ul>
          </div>

        </div>

      </div>
    </div>
  );
}

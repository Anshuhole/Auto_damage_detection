import React, { useState, useRef } from 'react';
import { UploadCloud, Camera, Image as ImageIcon, X, FileText, CheckCircle2, ArrowRight, ShieldAlert } from 'lucide-react';
import SampleCarGallery from './SampleCarGallery';

export default function ImageUploader({ 
  onAnalyzeFile, 
  onAnalyzeBase64, 
  isAnalyzing, 
  onOpenWebcam 
}) {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [notes, setNotes] = useState('');
  const fileInputRef = useRef(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      processFile(e.target.files[0]);
    }
  };

  const processFile = (file) => {
    if (!file.type.startsWith('image/')) {
      alert('Please upload a valid image file (JPEG, PNG, WEBP).');
      return;
    }
    setSelectedFile(file);
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
  };

  const handleClear = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleSubmit = () => {
    if (!selectedFile) return;
    onAnalyzeFile(selectedFile, notes);
  };

  const handleSelectSample = async (sample) => {
    try {
      const res = await fetch(sample.imageSrc);
      const blob = await res.blob();
      const filename = `${sample.id}.jpg`;
      const file = new File([blob], filename, { type: 'image/jpeg' });
      setSelectedFile(file);
      setPreviewUrl(sample.imageSrc);
      onAnalyzeFile(file, `Sample Preset Inspection: ${sample.name}`);
    } catch (err) {
      console.error('Failed to load sample image:', err);
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="glass-panel rounded-2xl p-6 sm:p-8 border-slate-800 shadow-2xl relative">
        
        {/* Glow corner decorations */}
        <div className="absolute top-0 right-0 w-32 h-32 bg-cyan-500/5 rounded-full blur-2xl pointer-events-none" />
        <div className="absolute bottom-0 left-0 w-32 h-32 bg-blue-500/5 rounded-full blur-2xl pointer-events-none" />

        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <UploadCloud className="w-5 h-5 text-cyan-400" />
              <span>Vehicle Inspection Workspace</span>
            </h2>
            <p className="text-xs text-slate-400">Upload high-res exterior photos or capture live damage in the field</p>
          </div>

          <button
            onClick={onOpenWebcam}
            className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-cyan-400 border border-slate-700 hover:border-cyan-500/40 text-xs font-semibold transition-all shadow-sm"
          >
            <Camera className="w-4 h-4" />
            <span>Open Webcam</span>
          </button>
        </div>

        {/* Upload / Preview Dropzone */}
        {!previewUrl ? (
          <div
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-2xl p-8 sm:p-12 text-center cursor-pointer transition-all duration-200 ${
              dragActive 
                ? 'border-cyan-400 bg-cyan-950/20 scale-[1.01]' 
                : 'border-slate-700/80 hover:border-cyan-500/50 bg-slate-900/40 hover:bg-slate-900/70'
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept="image/jpeg,image/png,image/webp"
              onChange={handleChange}
              className="hidden"
            />

            <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-cyan-500/20 to-blue-500/20 border border-cyan-500/30 flex items-center justify-center mx-auto mb-4 text-cyan-400 shadow-inner">
              <ImageIcon className="w-8 h-8" />
            </div>

            <h3 className="text-base font-bold text-white mb-1">
              Drag & drop vehicle photo here, or <span className="text-cyan-400 underline underline-offset-4">browse files</span>
            </h3>
            <p className="text-xs text-slate-400 max-w-sm mx-auto mb-4">
              Supports JPEG, PNG, WEBP up to 15MB. Best results with direct angle, well-lit shots.
            </p>

            <div className="inline-flex items-center gap-3 text-[11px] text-slate-400 bg-slate-800/80 px-4 py-1.5 rounded-full border border-slate-700 font-mono">
              <span>5 Damage Classes</span>
              <span>•</span>
              <span>Grad-CAM Explainable</span>
              <span>•</span>
              <span>Instant Valuation</span>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="relative rounded-2xl overflow-hidden bg-black/60 border border-slate-700 aspect-video max-h-[380px] flex items-center justify-center">
              <img 
                src={previewUrl} 
                alt="Selected Vehicle Preview" 
                className="w-full h-full object-contain"
              />
              
              {/* Overlay badges */}
              <div className="absolute top-3 left-3 bg-slate-950/80 backdrop-blur-md px-3 py-1.5 rounded-lg border border-slate-700 text-xs text-slate-200 font-mono flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                <span>{selectedFile?.name || 'Uploaded Vehicle Image'}</span>
              </div>

              <button
                onClick={handleClear}
                className="absolute top-3 right-3 p-1.5 bg-slate-950/80 hover:bg-rose-950/90 text-slate-300 hover:text-rose-300 rounded-lg border border-slate-700 hover:border-rose-700 transition-colors"
                title="Remove Image"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Optional Notes Input */}
            <div className="glass-card rounded-xl p-3.5 border-slate-800 flex items-center gap-3">
              <FileText className="w-4 h-4 text-slate-400 shrink-0" />
              <input
                type="text"
                placeholder="Optional inspection notes (e.g. 2021 Ford F-150, passenger door impact, claim #8841)..."
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                className="bg-transparent border-none text-xs text-slate-200 placeholder-slate-500 focus:outline-none w-full"
              />
            </div>

            {/* Action Bar */}
            <div className="flex items-center justify-between pt-2">
              <button
                onClick={handleClear}
                className="px-4 py-2 text-xs font-semibold text-slate-400 hover:text-slate-200"
              >
                Choose Different Image
              </button>

              <button
                disabled={isAnalyzing}
                onClick={handleSubmit}
                className="flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-cyan-500 via-sky-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-bold text-sm shadow-lg shadow-cyan-500/25 transition-all hover:scale-105 active:scale-95 disabled:opacity-50 disabled:pointer-events-none"
              >
                <span>Run AI Damage Analysis</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* 1-Click Sample Car Gallery */}
        <SampleCarGallery onSelectSample={handleSelectSample} isAnalyzing={isAnalyzing} />

      </div>
    </div>
  );
}

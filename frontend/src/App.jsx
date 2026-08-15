import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import HeroSection from './components/HeroSection';
import ImageUploader from './components/ImageUploader';
import WebcamCapture from './components/WebcamCapture';
import AnalysisProgress from './components/AnalysisProgress';
import ResultsCard from './components/ResultsCard';
import InspectionHistory from './components/InspectionHistory';
import StatsDashboard from './components/StatsDashboard';
import InspectionModal from './components/InspectionModal';
import ModelSpecsModal from './components/ModelSpecsModal';
import { predictImage, predictBase64, checkHealth, getInspectionDetail } from './services/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('inspect'); // 'inspect' | 'history' | 'analytics'
  const [isApiOnline, setIsApiOnline] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [currentResult, setCurrentResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);

  // Modals
  const [isWebcamOpen, setIsWebcamOpen] = useState(false);
  const [selectedInspectionId, setSelectedInspectionId] = useState(null);
  const [isSpecsOpen, setIsSpecsOpen] = useState(false);

  // Health check on mount and interval
  useEffect(() => {
    const pingApi = async () => {
      const online = await checkHealth();
      setIsApiOnline(online);
    };
    pingApi();
    const interval = setInterval(pingApi, 8000);
    return () => clearInterval(interval);
  }, []);

  const handleAnalyzeFile = async (file, notes) => {
    setIsAnalyzing(true);
    setErrorMessage(null);
    try {
      const data = await predictImage(file, notes);
      setCurrentResult(data);
    } catch (err) {
      console.error('Inference error:', err);
      setErrorMessage(err.message || 'Failed to complete damage analysis. Please check backend server.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleAnalyzeBase64 = async (base64Str, filename, notes) => {
    setIsAnalyzing(true);
    setErrorMessage(null);
    try {
      const data = await predictBase64(base64Str, filename, notes);
      setCurrentResult(data);
    } catch (err) {
      console.error('Base64 inference error:', err);
      setErrorMessage(err.message || 'Failed to complete damage analysis.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleWebcamCapture = (base64Data) => {
    setIsWebcamOpen(false);
    handleAnalyzeBase64(base64Data, 'webcam_capture.jpg', 'Field mobile inspection capture');
  };

  const handleSelectHistoryItem = (id) => {
    setSelectedInspectionId(id);
  };

  const handleResetScan = () => {
    setCurrentResult(null);
    setErrorMessage(null);
  };

  return (
    <div className="min-h-screen flex flex-col bg-dark-950 text-slate-100">
      
      {/* Navigation Header */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={(tab) => {
          setActiveTab(tab);
          setErrorMessage(null);
        }}
        isApiOnline={isApiOnline}
        onOpenSpecs={() => setIsSpecsOpen(true)}
      />

      {/* Main Content Viewport */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        
        {/* Error Alert Banner */}
        {errorMessage && (
          <div className="max-w-4xl mx-auto mb-6 p-4 rounded-xl bg-rose-950/80 border border-rose-800 text-rose-200 text-xs flex items-center justify-between shadow-lg">
            <span><strong>Analysis Error:</strong> {errorMessage}</span>
            <button
              onClick={() => setErrorMessage(null)}
              className="px-2 py-1 bg-rose-900 rounded text-xs hover:bg-rose-800"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Tab 1: AI Inspector Workspace */}
        {activeTab === 'inspect' && (
          <div className="space-y-6">
            {!currentResult && !isAnalyzing && (
              <>
                <HeroSection onStartScan={() => {}} />
                <ImageUploader
                  onAnalyzeFile={handleAnalyzeFile}
                  onAnalyzeBase64={handleAnalyzeBase64}
                  isAnalyzing={isAnalyzing}
                  onOpenWebcam={() => setIsWebcamOpen(true)}
                />
              </>
            )}

            {isAnalyzing && (
              <AnalysisProgress />
            )}

            {currentResult && !isAnalyzing && (
              <ResultsCard
                result={currentResult}
                onReset={handleResetScan}
              />
            )}
          </div>
        )}

        {/* Tab 2: Past Claims & History */}
        {activeTab === 'history' && (
          <InspectionHistory
            onSelectInspection={handleSelectHistoryItem}
            onNewScan={() => {
              setActiveTab('inspect');
              handleResetScan();
            }}
          />
        )}

        {/* Tab 3: Analytics Dashboard */}
        {activeTab === 'analytics' && (
          <StatsDashboard />
        )}

      </main>

      {/* Modals */}
      {isWebcamOpen && (
        <WebcamCapture
          onCapture={handleWebcamCapture}
          onClose={() => setIsWebcamOpen(false)}
        />
      )}

      {selectedInspectionId && (
        <InspectionModal
          inspectionId={selectedInspectionId}
          onClose={() => setSelectedInspectionId(null)}
        />
      )}

      {isSpecsOpen && (
        <ModelSpecsModal
          onClose={() => setIsSpecsOpen(false)}
        />
      )}

      {/* Footer */}
      <footer className="border-t border-slate-900/90 py-6 text-center text-xs text-slate-500 bg-dark-950/60">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <div>
            AutoInspect AI &copy; 2026 — Deep Learning Vehicle Damage & Valuation Platform
          </div>
          <div className="flex items-center gap-4 text-slate-400">
            <button onClick={() => setIsSpecsOpen(true)} className="hover:text-cyan-400">Architecture</button>
            <a href="/docs" target="_blank" rel="noreferrer" className="hover:text-cyan-400">FastAPI Swagger</a>
            <span className="font-mono text-[11px] text-cyan-400">PyTorch + Grad-CAM</span>
          </div>
        </div>
      </footer>

    </div>
  );
}

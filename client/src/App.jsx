// Main SIH Quantum Traffic Command Center Application (Bangalore Smart City Edition)
import React, { useState } from "react";
import TrafficMap from "./components/map/TrafficMap";
import Header from "./components/hud/Header";
import QuantumToggle from "./components/hud/QuantumToggle";
import MetricsGrid from "./components/hud/MetricsGrid";
import RerouteEventFeed from "./components/hud/RerouteEventFeed";
import IntersectionsList from "./components/hud/IntersectionsList";
import QuantumAnalysisModal from "./components/hud/QuantumAnalysisModal";
import TokenModal from "./components/hud/TokenModal";
import { useSocket } from "./context/SocketContext";
import { ChevronRight, ChevronLeft, Car } from "lucide-react";

export default function App() {
  const { telemetry, setVehicleCount } = useSocket();
  const { isQuantumOptimized } = telemetry;

  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [isAnalysisOpen, setIsAnalysisOpen] = useState(false);
  const [isTokenModalOpen, setIsTokenModalOpen] = useState(false);
  const [mapboxToken, setMapboxToken] = useState(() => {
    return localStorage.getItem("SIH_MAPBOX_TOKEN") || "";
  });
  const [cameraPreset, setCameraPreset] = useState("overview");
  const [selectedIntersection, setSelectedIntersection] = useState(null);
  const [vehicleCountInput, setVehicleCountInput] = useState(20);

  const handleSaveToken = (token) => {
    setMapboxToken(token);
    localStorage.setItem("SIH_MAPBOX_TOKEN", token);
  };

  const handleVehicleCountChange = (e) => {
    const val = Number(e.target.value);
    setVehicleCountInput(val);
    setVehicleCount(val);
  };

  return (
    <div
      className={`relative w-screen h-screen overflow-hidden bg-slate-950 transition-colors duration-700 ${
        isQuantumOptimized ? "quantum-theme" : "classical-theme"
      }`}
    >
      {/* 1. Full-Screen Deck.gl + Google Maps Viewport (Indiranagar, Bengaluru) */}
      <div className="absolute inset-0 w-full h-full">
        <TrafficMap
          mapboxToken={mapboxToken}
          cameraPreset={cameraPreset}
          selectedIntersection={selectedIntersection}
          onSelectIntersection={(inter) => {
            setSelectedIntersection(inter);
            if (!sidebarOpen) setSidebarOpen(true);
          }}
        />
      </div>

      {/* 2. Top Command Center Header (Never overlaps with right sidebar) */}
      <div className="absolute top-4 left-4 right-4 md:right-[436px] z-20 pointer-events-auto">
        <Header
          onOpenTokenModal={() => setIsTokenModalOpen(true)}
          onOpenAnalysisModal={() => setIsAnalysisOpen(true)}
          onSelectCameraPreset={(preset) => {
            setCameraPreset(preset);
            setTimeout(() => setCameraPreset(null), 1500);
          }}
          cameraPreset={cameraPreset}
        />
      </div>

      {/* 3. Sleek Semi-Transparent Glassmorphic Sidebar (Right side, Full Height) */}
      <div
        className={`absolute top-4 bottom-4 right-4 z-30 flex transition-all duration-500 ease-in-out pointer-events-auto ${
          sidebarOpen ? "translate-x-0" : "translate-x-[calc(100%-2.5rem)]"
        }`}
      >
        {/* Collapse / Expand Tab */}
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="self-center p-2 rounded-l-xl glass-panel text-cyan-400 hover:text-cyan-200 border-r-0 border-cyan-500/30 shadow-xl transition-transform active:scale-95 cursor-pointer"
          title={sidebarOpen ? "Collapse Control Panel" : "Expand Control Panel"}
        >
          {sidebarOpen ? <ChevronRight className="w-5 h-5" /> : <ChevronLeft className="w-5 h-5" />}
        </button>

        {/* Sidebar Main Content */}
        <aside className="w-80 md:w-[410px] h-full flex flex-col gap-3.5 p-4 glass-panel rounded-2xl border border-cyan-500/20 shadow-2xl overflow-y-auto">
          {/* Hero Quantum Switch (Dedicated Fixed Height, Never Clipped) */}
          <div className="shrink-0">
            <QuantumToggle />
          </div>

          {/* Real-time KPI Metrics Grid */}
          <div className="shrink-0">
            <MetricsGrid />
          </div>

          {/* Live Quantum Re-routing Event Stream */}
          <div className="shrink-0">
            <RerouteEventFeed />
          </div>

          {/* Vehicle Fleet Density Slider */}
          <div className="shrink-0 p-3 rounded-xl bg-slate-950/70 border border-slate-800">
            <div className="flex items-center justify-between text-xs font-mono text-slate-300 mb-1.5">
              <span className="flex items-center gap-1.5">
                <Car className="w-3.5 h-3.5 text-cyan-400" />
                Active Vehicles
              </span>
              <span className="text-cyan-300 font-bold">{vehicleCountInput} cars</span>
            </div>
            <input
              type="range"
              min="5"
              max="50"
              step="5"
              value={vehicleCountInput}
              onChange={handleVehicleCountChange}
              className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-cyan-400"
            />
          </div>

          {/* 10 Bangalore Intersections Control & Manual Light Override */}
          <div className="flex-1 min-h-[260px]">
            <IntersectionsList
              selectedIntersection={selectedIntersection}
              onSelectIntersection={(inter) => setSelectedIntersection(inter)}
            />
          </div>
        </aside>
      </div>

      {/* 4. Modals */}
      <QuantumAnalysisModal
        isOpen={isAnalysisOpen}
        onClose={() => setIsAnalysisOpen(false)}
      />

      <TokenModal
        isOpen={isTokenModalOpen}
        onClose={() => setIsTokenModalOpen(false)}
        mapboxToken={mapboxToken}
        onSaveToken={handleSaveToken}
      />
    </div>
  );
}

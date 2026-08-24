// Command Center Top Header Component (Bangalore Smart Corridor Edition)
import React, { useState, useEffect } from "react";
import {
  Activity,
  Cpu,
  Radio,
  Volume2,
  VolumeX,
  Key,
  RotateCcw,
  Sliders,
  Layers,
  Sparkles,
  MapPin,
} from "lucide-react";
import { useSocket } from "../../context/SocketContext";
import { sound } from "../../utils/audio";

export default function Header({
  onOpenTokenModal,
  onOpenAnalysisModal,
  onSelectCameraPreset,
  cameraPreset,
}) {
  const { connected, telemetry, resetSimulation } = useSocket();
  const [isMuted, setIsMuted] = useState(false);
  const [timeStr, setTimeStr] = useState("");

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTimeStr(now.toLocaleTimeString("en-US", { hour12: false }));
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  const handleToggleSound = () => {
    const muted = sound.toggleMute();
    setIsMuted(muted);
  };

  return (
    <header className="w-full flex flex-wrap items-center justify-between gap-3 px-4 py-2.5 glass-panel rounded-2xl border border-cyan-500/20 shadow-2xl">
      {/* Brand & Bangalore Project Identity */}
      <div className="flex items-center gap-3.5">
        <div className="relative flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-600/30 to-emerald-500/30 border border-cyan-400/40 shadow-neon-cyan">
          <Cpu className={`w-6 h-6 ${telemetry.isQuantumOptimized ? "text-emerald-400 animate-pulse" : "text-cyan-400"}`} />
          {telemetry.isQuantumOptimized && (
            <span className="absolute -top-1 -right-1 flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
            </span>
          )}
        </div>

        <div>
          <div className="flex items-center gap-2">
            <h1 className="font-display font-bold text-base md:text-lg tracking-wider text-slate-100 uppercase">
              Quantum<span className="text-emerald-400">Flow</span>
            </h1>
            <span className="px-2 py-0.5 text-[10px] font-mono tracking-widest uppercase rounded bg-cyan-950/80 border border-cyan-500/40 text-cyan-300 font-semibold">
              SIH 2026
            </span>
          </div>
          <p className="text-[11px] font-mono text-slate-400 flex items-center gap-1">
            <MapPin className="w-3 h-3 text-cyan-400" />
            <span>Indiranagar – Domlur – Old Airport Rd, Bengaluru</span>
          </p>
        </div>
      </div>

      {/* Center Bangalore Camera & Scenario Presets */}
      <div className="hidden lg:flex items-center gap-1.5 p-1 bg-slate-950/70 border border-slate-800/80 rounded-xl text-xs font-mono">
        <button
          onClick={() => onSelectCameraPreset("overview")}
          className={`px-3 py-1.5 rounded-lg transition-all ${
            cameraPreset === "overview"
              ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/50 shadow-neon-cyan"
              : "text-slate-400 hover:text-slate-200"
          }`}
        >
          Indiranagar Overview
        </button>
        <button
          onClick={() => onSelectCameraPreset("bottleneck")}
          className={`px-3 py-1.5 rounded-lg transition-all ${
            cameraPreset === "bottleneck"
              ? "bg-rose-500/20 text-rose-300 border border-rose-500/50 shadow-neon-red"
              : "text-slate-400 hover:text-slate-200"
          }`}
        >
          100ft Rd Bottleneck
        </button>
        <button
          onClick={() => onSelectCameraPreset("domlur")}
          className={`px-3 py-1.5 rounded-lg transition-all ${
            cameraPreset === "domlur"
              ? "bg-amber-500/20 text-amber-300 border border-amber-500/50"
              : "text-slate-400 hover:text-slate-200"
          }`}
        >
          Domlur Flyover
        </button>
        <button
          onClick={() => onSelectCameraPreset("bypass")}
          className={`px-3 py-1.5 rounded-lg transition-all ${
            cameraPreset === "bypass"
              ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/50 shadow-neon-green"
              : "text-slate-400 hover:text-slate-200"
          }`}
        >
          Quantum Bypass
        </button>
      </div>

      {/* Right Controls & Telemetry Status */}
      <div className="flex items-center gap-2 sm:gap-3">
        {/* Live Clock & Connection Status */}
        <div className="hidden md:flex flex-col items-end text-[11px] font-mono pr-2 border-r border-slate-800">
          <div className="flex items-center gap-1.5">
            <span
              className={`w-2 h-2 rounded-full ${
                connected ? "bg-emerald-400 shadow-[0_0_8px_#10b981]" : "bg-rose-500 shadow-[0_0_8px_#ff2a5f]"
              }`}
            />
            <span className={connected ? "text-emerald-400 font-bold" : "text-rose-400"}>
              {connected ? "LIVE 25 FPS" : "DISCONNECTED"}
            </span>
          </div>
          <span className="text-slate-400">{timeStr || "10:10:00 UTC"}</span>
        </div>

        {/* Algorithm Inspector Modal Button */}
        <button
          onClick={onOpenAnalysisModal}
          className="px-3 py-2 text-xs font-mono text-cyan-300 hover:text-cyan-100 bg-cyan-950/40 hover:bg-cyan-900/50 border border-cyan-500/30 hover:border-cyan-400 rounded-xl transition-all flex items-center gap-1.5 active:scale-95"
          title="Quantum Algorithm & QUBO Mathematical Model"
        >
          <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
          <span className="hidden sm:inline">QUBO Specs</span>
        </button>

        {/* Reset Simulation Button */}
        <button
          onClick={resetSimulation}
          className="p-2 text-xs font-mono text-slate-300 hover:text-rose-300 bg-slate-900/60 hover:bg-rose-950/40 border border-slate-700/60 hover:border-rose-500/40 rounded-xl transition-all active:scale-95"
          title="Reset Simulation & Clear Gridlock"
        >
          <RotateCcw className="w-4 h-4" />
        </button>

        {/* Audio Mute/Unmute */}
        <button
          onClick={handleToggleSound}
          className="p-2 text-xs font-mono text-slate-300 hover:text-cyan-300 bg-slate-900/60 hover:bg-slate-800 border border-slate-700/60 hover:border-cyan-500/40 rounded-xl transition-all active:scale-95"
          title={isMuted ? "Unmute Audio FX" : "Mute Audio FX"}
        >
          {isMuted ? <VolumeX className="w-4 h-4 text-slate-500" /> : <Volume2 className="w-4 h-4 text-cyan-400" />}
        </button>

        {/* Mapbox Token Modal Trigger */}
        <button
          onClick={onOpenTokenModal}
          className="p-2 text-xs font-mono text-slate-300 hover:text-amber-300 bg-slate-900/60 hover:bg-slate-800 border border-slate-700/60 hover:border-amber-500/40 rounded-xl transition-all active:scale-95"
          title="Mapbox Token Configuration"
        >
          <Key className="w-4 h-4 text-amber-400" />
        </button>
      </div>
    </header>
  );
}

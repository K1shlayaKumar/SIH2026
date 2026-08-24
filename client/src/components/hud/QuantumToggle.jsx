// Hero Quantum Optimization Toggle Switch Box
import React from "react";
import { Sparkles, Zap, ShieldAlert, Cpu, CheckCircle2, ArrowRight } from "lucide-react";
import { useSocket } from "../../context/SocketContext";

export default function QuantumToggle() {
  const { telemetry, toggleOptimization } = useSocket();
  const isActive = Boolean(telemetry.isQuantumOptimized);

  return (
    <div
      className={`w-full relative overflow-hidden p-4 md:p-5 rounded-2xl transition-all duration-500 border ${
        isActive
          ? "bg-slate-900/90 border-emerald-400/60 shadow-[0_0_25px_rgba(0,255,170,0.25)]"
          : "bg-slate-900/80 border-slate-700/70 shadow-lg"
      }`}
    >
      {/* Top Header & Status Badge */}
      <div className="flex items-center justify-between gap-2 mb-3">
        <div className="flex items-center gap-2">
          <div
            className={`p-1.5 rounded-lg border transition-all ${
              isActive
                ? "bg-emerald-950/80 border-emerald-500/50 text-emerald-400"
                : "bg-slate-800 border-slate-700 text-slate-400"
            }`}
          >
            <Cpu className={`w-4 h-4 ${isActive ? "animate-pulse" : ""}`} />
          </div>
          <div>
            <div className="text-xs font-mono font-bold tracking-wider uppercase text-slate-200">
              Algorithm Engine
            </div>
            <div className="text-[10px] font-mono text-slate-400">
              {isActive ? "Quantum QAOA & Wave Sync" : "Classical Fixed-Time Phase"}
            </div>
          </div>
        </div>

        {/* Status Pill Badge */}
        <div
          className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-mono font-bold border transition-all ${
            isActive
              ? "bg-emerald-950 border-emerald-400/70 text-emerald-300 shadow-[0_0_10px_rgba(0,255,170,0.3)]"
              : "bg-rose-950/80 border-rose-500/50 text-rose-400"
          }`}
        >
          {isActive ? (
            <>
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
              <span>ACTIVE</span>
            </>
          ) : (
            <>
              <ShieldAlert className="w-3 h-3 text-rose-400" />
              <span>CONGESTED</span>
            </>
          )}
        </div>
      </div>

      {/* Main Interactive Toggle Button */}
      <button
        type="button"
        onClick={() => toggleOptimization(!isActive)}
        className={`w-full p-3.5 rounded-xl border transition-all duration-300 flex items-center justify-between gap-3 text-left active:scale-[0.98] cursor-pointer ${
          isActive
            ? "bg-gradient-to-r from-emerald-950/90 via-teal-950/70 to-slate-900 border-emerald-400 shadow-[0_0_20px_rgba(0,255,170,0.3)]"
            : "bg-slate-950/80 hover:bg-slate-950 border-slate-700 hover:border-cyan-500/50"
        }`}
      >
        <div className="flex items-center gap-3 min-w-0">
          <div
            className={`p-2.5 rounded-xl border transition-all shrink-0 ${
              isActive
                ? "bg-emerald-500/20 border-emerald-400/60 text-emerald-300"
                : "bg-cyan-500/10 border-cyan-500/30 text-cyan-400"
            }`}
          >
            <Sparkles className={`w-5 h-5 ${isActive ? "text-emerald-300 animate-bounce" : "text-cyan-400"}`} />
          </div>
          <div className="truncate">
            <div
              className={`text-sm font-display font-bold leading-tight ${
                isActive ? "text-emerald-300 glow-text-emerald" : "text-slate-100"
              }`}
            >
              {isActive ? "Quantum Optimizer Active" : "Enable Quantum Optimization"}
            </div>
            <div className="text-[11px] font-mono text-slate-400 truncate mt-0.5">
              {isActive ? "⚡ Re-routing via bypass corridors" : "Click to clear Bangalore bottlenecks"}
            </div>
          </div>
        </div>

        {/* Prominent Physical Toggle Switch Component */}
        <div
          className={`w-13 h-7 px-1 rounded-full flex items-center transition-all duration-300 shrink-0 border ${
            isActive
              ? "bg-emerald-500 border-emerald-300 justify-end shadow-[0_0_15px_#00ffaa]"
              : "bg-slate-800 border-slate-600 justify-start"
          }`}
          style={{ width: "52px", height: "28px" }}
        >
          <div
            className={`w-5 h-5 rounded-full flex items-center justify-center transition-all transform duration-300 shadow-md ${
              isActive ? "bg-slate-950 text-emerald-400" : "bg-slate-400 text-slate-900"
            }`}
          >
            <Zap className="w-3 h-3" />
          </div>
        </div>
      </button>

      {/* Progress Bar / Quantum Flow State */}
      <div className="mt-3 pt-2.5 border-t border-slate-800/80 flex items-center justify-between text-[10px] font-mono">
        <span className="text-slate-400">
          Flow State:{" "}
          <strong className={isActive ? "text-emerald-400" : "text-rose-400"}>
            {isActive ? "Superposition Distributed" : "Severe Gridlock (100ft Rd)"}
          </strong>
        </span>
        <span className={isActive ? "text-emerald-300 font-bold" : "text-slate-500"}>
          {isActive ? "98.4% Optimal" : "28.0% Sub-optimal"}
        </span>
      </div>
    </div>
  );
}

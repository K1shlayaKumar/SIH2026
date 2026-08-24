// Live Metrics Grid Component with Real-Time KPIs & Sparklines
import React from "react";
import {
  Clock,
  Gauge,
  Zap,
  Leaf,
  AlertTriangle,
  Car,
  TrendingDown,
  TrendingUp,
} from "lucide-react";
import { useSocket } from "../../context/SocketContext";

// Simple SVG sparkline renderer
function Sparkline({ data = [], color = "#00f0ff", height = 24 }) {
  if (!data || data.length < 2) return null;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const width = 80;

  const points = data
    .map((val, idx) => {
      const x = (idx / (data.length - 1)) * width;
      const y = height - ((val - min) / range) * (height - 6) - 3;
      return `${x},${y}`;
    })
    .join(" ");

  return (
    <svg width={width} height={height} className="overflow-visible">
      <polyline
        fill="none"
        stroke={color}
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
        points={points}
      />
    </svg>
  );
}

export default function MetricsGrid() {
  const { telemetry, metricsHistory } = useSocket();
  const { metrics = {}, isQuantumOptimized } = telemetry;

  return (
    <div className="grid grid-cols-2 gap-3">
      {/* 1. Average Wait Time */}
      <div
        className={`p-3.5 rounded-xl border transition-all ${
          isQuantumOptimized
            ? "bg-slate-900/70 border-emerald-500/30"
            : "bg-slate-900/70 border-rose-500/30"
        }`}
      >
        <div className="flex items-center justify-between text-slate-400 mb-1.5">
          <span className="text-[11px] font-mono flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5 text-cyan-400" />
            Avg Wait Time
          </span>
          {isQuantumOptimized ? (
            <span className="text-[10px] font-mono font-bold text-emerald-400 flex items-center">
              <TrendingDown className="w-3 h-3 mr-0.5" /> -82%
            </span>
          ) : (
            <span className="text-[10px] font-mono font-bold text-rose-400 flex items-center">
              <TrendingUp className="w-3 h-3 mr-0.5" /> High
            </span>
          )}
        </div>

        <div className="flex items-baseline justify-between">
          <div className="flex items-baseline gap-1">
            <span
              className={`text-2xl font-display font-bold tracking-tight ${
                isQuantumOptimized ? "text-emerald-400 glow-text-emerald" : "text-rose-400 glow-text-red"
              }`}
            >
              {metrics.avgWaitTime || 0}
            </span>
            <span className="text-xs font-mono text-slate-400">sec</span>
          </div>

          <Sparkline
            data={metricsHistory.waitTime}
            color={isQuantumOptimized ? "#10b981" : "#ff2a5f"}
            height={20}
          />
        </div>
      </div>

      {/* 2. Algorithm Efficiency % */}
      <div
        className={`p-3.5 rounded-xl border transition-all ${
          isQuantumOptimized
            ? "bg-slate-900/70 border-emerald-500/30"
            : "bg-slate-900/70 border-amber-500/30"
        }`}
      >
        <div className="flex items-center justify-between text-slate-400 mb-1.5">
          <span className="text-[11px] font-mono flex items-center gap-1.5">
            <Zap className="w-3.5 h-3.5 text-amber-400" />
            Efficiency Score
          </span>
          <span
            className={`text-[10px] font-mono font-bold ${
              isQuantumOptimized ? "text-emerald-400" : "text-amber-400"
            }`}
          >
            {isQuantumOptimized ? "OPTIMAL" : "SUB-OPTIMAL"}
          </span>
        </div>

        <div className="flex items-baseline justify-between">
          <div className="flex items-baseline gap-1">
            <span
              className={`text-2xl font-display font-bold tracking-tight ${
                isQuantumOptimized ? "text-emerald-400 glow-text-emerald" : "text-amber-400"
              }`}
            >
              {metrics.efficiency || 0}%
            </span>
          </div>

          <Sparkline
            data={metricsHistory.efficiency}
            color={isQuantumOptimized ? "#10b981" : "#f59e0b"}
            height={20}
          />
        </div>
      </div>

      {/* 3. Average Velocity */}
      <div className="p-3.5 rounded-xl bg-slate-900/70 border border-cyan-500/20">
        <div className="flex items-center justify-between text-slate-400 mb-1.5">
          <span className="text-[11px] font-mono flex items-center gap-1.5">
            <Gauge className="w-3.5 h-3.5 text-cyan-400" />
            Fleet Velocity
          </span>
          <span className="text-[10px] font-mono text-cyan-300">
            {metrics.avgSpeed > 35 ? "FREE FLOW" : "SLOW FLOW"}
          </span>
        </div>

        <div className="flex items-baseline justify-between">
          <div className="flex items-baseline gap-1">
            <span className="text-xl font-display font-bold text-cyan-300">
              {metrics.avgSpeed || 0}
            </span>
            <span className="text-xs font-mono text-slate-400">km/h</span>
          </div>

          <Sparkline data={metricsHistory.speed} color="#00f0ff" height={20} />
        </div>
      </div>

      {/* 4. Active Hotspots / Carbon Saved */}
      <div className="p-3.5 rounded-xl bg-slate-900/70 border border-cyan-500/20">
        <div className="flex items-center justify-between text-slate-400 mb-1.5">
          <span className="text-[11px] font-mono flex items-center gap-1.5">
            {isQuantumOptimized ? (
              <Leaf className="w-3.5 h-3.5 text-emerald-400" />
            ) : (
              <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
            )}
            {isQuantumOptimized ? "CO₂ Mitigated" : "Bottlenecks"}
          </span>
          <span className="text-[10px] font-mono text-slate-400">
            {isQuantumOptimized ? "ECO IMPACT" : "ALERT"}
          </span>
        </div>

        <div className="flex items-baseline justify-between">
          <div className="flex items-baseline gap-1">
            <span
              className={`text-xl font-display font-bold ${
                isQuantumOptimized ? "text-emerald-400" : metrics.hotspots > 0 ? "text-rose-400" : "text-cyan-300"
              }`}
            >
              {isQuantumOptimized ? `${metrics.co2Reduction} kg` : `${metrics.hotspots} Nodes`}
            </span>
          </div>

          <div className="text-[10px] font-mono text-slate-400 flex items-center gap-1">
            <Car className="w-3 h-3 text-cyan-400" />
            {metrics.totalVehicles || 20} cars
          </div>
        </div>
      </div>
    </div>
  );
}

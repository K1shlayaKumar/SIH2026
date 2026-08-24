// Intersections & Traffic Light Manual Override Panel Component
import React, { useState } from "react";
import {
  SlidersHorizontal,
  CircleDot,
  Radio,
  Clock,
  Car,
  CheckCircle,
  XCircle,
  RefreshCw,
} from "lucide-react";
import { useSocket } from "../../context/SocketContext";

export default function IntersectionsList({ selectedIntersection, onSelectIntersection }) {
  const { telemetry, overrideLight } = useSocket();
  const { intersections = [], isQuantumOptimized } = telemetry;
  const [filter, setFilter] = useState("all"); // 'all' | 'congested' | 'overridden'

  const filteredIntersections = intersections.filter((item) => {
    if (filter === "congested") return item.queueCount > 4;
    if (filter === "overridden") return item.manualOverride !== null;
    return true;
  });

  return (
    <div className="flex flex-col h-full">
      {/* Panel Header */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-800/80">
        <div className="flex items-center gap-2">
          <SlidersHorizontal className="w-4 h-4 text-cyan-400" />
          <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-200">
            Intersection Signals ({intersections.length})
          </h3>
        </div>

        {/* Filter Pills */}
        <div className="flex items-center gap-1 text-[10px] font-mono">
          <button
            onClick={() => setFilter("all")}
            className={`px-2 py-0.5 rounded transition-all ${
              filter === "all"
                ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            All
          </button>
          <button
            onClick={() => setFilter("congested")}
            className={`px-2 py-0.5 rounded transition-all ${
              filter === "congested"
                ? "bg-rose-500/20 text-rose-300 border border-rose-500/40"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Queued
          </button>
          <button
            onClick={() => setFilter("overridden")}
            className={`px-2 py-0.5 rounded transition-all ${
              filter === "overridden"
                ? "bg-purple-500/20 text-purple-300 border border-purple-500/40"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Manual
          </button>
        </div>
      </div>

      {/* Intersections List */}
      <div className="flex-1 overflow-y-auto pr-1 mt-3 space-y-2 max-h-[380px]">
        {filteredIntersections.length === 0 ? (
          <div className="py-8 text-center text-xs font-mono text-slate-500">
            No intersections match this filter
          </div>
        ) : (
          filteredIntersections.map((inter) => {
            const isSelected = selectedIntersection?.id === inter.id;
            const isGreen = inter.phase === "NS_GREEN" || inter.manualOverride === "FORCE_GREEN";
            const isYellow = inter.phase === "YELLOW";
            const isRed = inter.phase === "ALL_RED" || inter.manualOverride === "FORCE_RED";

            return (
              <div
                key={inter.id}
                onClick={() => onSelectIntersection && onSelectIntersection(inter)}
                className={`p-3 rounded-xl border transition-all cursor-pointer ${
                  isSelected
                    ? "bg-cyan-950/40 border-cyan-400 shadow-neon-cyan"
                    : "bg-slate-900/60 hover:bg-slate-900/90 border-slate-800/80 hover:border-slate-700"
                }`}
              >
                {/* Top Line: ID, Name, Phase & Queue */}
                <div className="flex items-start justify-between gap-2 mb-2">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-bold text-xs text-cyan-300">
                        {inter.id}
                      </span>
                      {inter.manualOverride && (
                        <span className="px-1.5 py-0.2 text-[9px] font-mono uppercase bg-purple-950 border border-purple-500/40 text-purple-300 rounded">
                          OVERRIDE
                        </span>
                      )}
                    </div>
                    <div className="text-[11px] text-slate-300 truncate max-w-[170px]">
                      {inter.name}
                    </div>
                  </div>

                  {/* Signal Light Indicator & Queue Badge */}
                  <div className="flex items-center gap-2">
                    <div className="flex items-center gap-1 text-[11px] font-mono text-slate-400 bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
                      <Car className="w-3 h-3 text-slate-400" />
                      <span className={inter.queueCount > 5 ? "text-rose-400 font-bold" : "text-slate-300"}>
                        {inter.queueCount}
                      </span>
                    </div>

                    {/* Signal Dot */}
                    <div
                      className={`w-3.5 h-3.5 rounded-full border shadow-sm ${
                        isRed
                          ? "bg-rose-500 border-rose-300 shadow-[0_0_8px_#ff2a5f]"
                          : isYellow
                          ? "bg-amber-400 border-amber-200 shadow-[0_0_8px_#f59e0b]"
                          : "bg-emerald-400 border-emerald-200 shadow-[0_0_8px_#10b981]"
                      }`}
                      title={`Phase: ${inter.phase}, Timer: ${inter.timer}s`}
                    />
                  </div>
                </div>

                {/* Bottom Row: Phase Timer & Override Controls */}
                <div className="flex items-center justify-between pt-2 border-t border-slate-800/60 text-xs font-mono">
                  <div className="flex items-center gap-1.5 text-[11px] text-slate-400">
                    <Clock className="w-3 h-3 text-cyan-400" />
                    <span>
                      {isQuantumOptimized ? "Adaptive:" : "Phase:"} <strong className="text-slate-200">{inter.timer}s</strong>
                    </span>
                  </div>

                  {/* Quick Override Buttons */}
                  <div className="flex items-center gap-1">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        overrideLight(inter.id, "GREEN");
                      }}
                      className={`px-2 py-0.5 rounded text-[10px] font-bold border transition-all ${
                        inter.manualOverride === "FORCE_GREEN"
                          ? "bg-emerald-500 text-slate-950 border-emerald-300 shadow-neon-green"
                          : "bg-emerald-950/40 text-emerald-300 hover:bg-emerald-900/60 border-emerald-600/40"
                      }`}
                      title="Force Green Signal"
                    >
                      Green
                    </button>

                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        overrideLight(inter.id, "RED");
                      }}
                      className={`px-2 py-0.5 rounded text-[10px] font-bold border transition-all ${
                        inter.manualOverride === "FORCE_RED"
                          ? "bg-rose-500 text-slate-950 border-rose-300 shadow-neon-red"
                          : "bg-rose-950/40 text-rose-300 hover:bg-rose-900/60 border-rose-600/40"
                      }`}
                      title="Force Red Signal"
                    >
                      Red
                    </button>

                    {inter.manualOverride && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          overrideLight(inter.id, "AUTO");
                        }}
                        className="px-1.5 py-0.5 rounded text-[10px] bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-600"
                        title="Reset to Auto Control"
                      >
                        <RefreshCw className="w-2.5 h-2.5" />
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

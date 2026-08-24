// Live Quantum Re-routing Event Feed Component
import React from "react";
import { GitFork, ArrowRight, Clock, ShieldCheck, Zap } from "lucide-react";
import { useSocket } from "../../context/SocketContext";

export default function RerouteEventFeed() {
  const { telemetry } = useSocket();
  const { isQuantumOptimized, rerouteEvents = [], metrics = {} } = telemetry;

  if (!isQuantumOptimized) {
    return (
      <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 text-center">
        <div className="text-[11px] font-mono text-slate-400 flex items-center justify-center gap-1.5 mb-1">
          <GitFork className="w-3.5 h-3.5 text-slate-500" />
          Quantum Rerouting Stream
        </div>
        <p className="text-[10px] font-mono text-slate-500">
          Disabled • Activate Quantum Optimizer to view live path diversions
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col p-3 rounded-xl bg-slate-950/80 border border-emerald-500/30 shadow-neon-green/20">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-1.5 text-xs font-mono font-bold text-emerald-400">
          <Zap className="w-3.5 h-3.5 text-emerald-300 animate-bounce" />
          <span>Live Quantum Diversions</span>
        </div>
        <span className="px-2 py-0.5 text-[10px] font-mono font-bold text-emerald-300 bg-emerald-950/80 border border-emerald-500/40 rounded-full">
          {metrics.reroutedVehicles || rerouteEvents.length} Active
        </span>
      </div>

      <div className="space-y-1.5 max-h-[140px] overflow-y-auto pr-1 text-[11px] font-mono">
        {rerouteEvents.length === 0 ? (
          <div className="py-3 text-center text-[10px] text-emerald-400/80 animate-pulse">
            Analyzing urban grid flow vectors...
          </div>
        ) : (
          rerouteEvents.map((evt) => (
            <div
              key={evt.id}
              className="p-2 rounded-lg bg-slate-900/90 border border-emerald-500/20 hover:border-emerald-400/40 transition-all flex items-center justify-between gap-2"
            >
              <div className="flex items-center gap-1.5 min-w-0">
                <span className="font-bold text-cyan-300 shrink-0">{evt.vehicleId}</span>
                <ArrowRight className="w-3 h-3 text-emerald-400 shrink-0" />
                <span className="text-slate-300 truncate" title={evt.divertedTo}>
                  {evt.divertedTo}
                </span>
              </div>
              <div className="flex items-center gap-1 shrink-0">
                <span className="text-[10px] font-bold text-emerald-400 bg-emerald-950 px-1.5 py-0.5 rounded border border-emerald-500/30">
                  -{evt.timeSavedMin}m
                </span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

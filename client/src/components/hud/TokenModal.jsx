// Mapbox Token Settings Modal Component
import React, { useState } from "react";
import { Key, X, Check, Globe, Shield, Sparkles } from "lucide-react";

export default function TokenModal({ isOpen, onClose, mapboxToken, onSaveToken }) {
  const [inputVal, setInputVal] = useState(mapboxToken || "");
  const [savedSuccess, setSavedSuccess] = useState(false);

  if (!isOpen) return null;

  const handleSave = (e) => {
    e.preventDefault();
    onSaveToken(inputVal.trim());
    setSavedSuccess(true);
    setTimeout(() => {
      setSavedSuccess(false);
      onClose();
    }, 800);
  };

  const handleUseDefault = () => {
    setInputVal("");
    onSaveToken("");
    setSavedSuccess(true);
    setTimeout(() => {
      setSavedSuccess(false);
      onClose();
    }, 800);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fadeIn">
      <div className="relative w-full max-w-lg glass-panel rounded-2xl border border-cyan-500/40 p-6 shadow-2xl">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-2 rounded-xl text-slate-400 hover:text-slate-100 bg-slate-900/80 hover:bg-slate-800 border border-slate-700 transition-all"
        >
          <X className="w-4 h-4" />
        </button>

        <div className="flex items-center gap-3 mb-5">
          <div className="p-2.5 rounded-xl bg-amber-950/60 border border-amber-500/40 text-amber-400 shadow-sm">
            <Key className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-display font-bold text-slate-100">
              Mapbox Access Token
            </h2>
            <p className="text-xs font-mono text-slate-400">
              Configure custom Mapbox Dark Vector Tiles or use default Carto tiles
            </p>
          </div>
        </div>

        <form onSubmit={handleSave} className="space-y-4">
          <div>
            <label className="block text-xs font-mono text-slate-300 mb-1.5">
              Enter Mapbox Public Key (<code className="text-cyan-400">pk.eyJ...</code>):
            </label>
            <input
              type="text"
              placeholder="pk.eyJ1IjoieW91ci11c2VybmFtZSIsImEiOi..."
              value={inputVal}
              onChange={(e) => setInputVal(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950/80 border border-slate-700 focus:border-cyan-400 text-xs font-mono text-slate-100 placeholder:text-slate-600 outline-none transition-all"
            />
          </div>

          <div className="p-3.5 rounded-xl bg-cyan-950/30 border border-cyan-500/30 text-xs font-mono text-cyan-300 flex items-start gap-2.5">
            <Globe className="w-4 h-4 text-cyan-400 mt-0.5 shrink-0" />
            <div>
              <strong className="text-cyan-200">Zero-Config Mode Active:</strong> If left empty,
              the simulation seamlessly renders high-contrast Dark Matter vector tiles without any API key!
            </div>
          </div>

          <div className="flex items-center justify-between pt-2">
            <button
              type="button"
              onClick={handleUseDefault}
              className="px-3.5 py-2 rounded-xl text-xs font-mono text-slate-400 hover:text-slate-200 bg-slate-900 border border-slate-800 transition-all"
            >
              Reset to Carto Dark
            </button>

            <button
              type="submit"
              className="px-5 py-2 rounded-xl text-xs font-mono font-bold bg-cyan-500 hover:bg-cyan-400 text-slate-950 transition-all shadow-neon-cyan flex items-center gap-1.5 active:scale-95"
            >
              {savedSuccess ? (
                <>
                  <Check className="w-4 h-4 text-slate-950" /> Saved!
                </>
              ) : (
                "Save & Apply"
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

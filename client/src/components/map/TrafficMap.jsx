// Bangalore Indiranagar & Domlur Traffic Map with Google Maps City Grid & High-Visibility Vehicles
import React, { useState, useMemo, useEffect } from "react";
import DeckGL from "@deck.gl/react";
import { ScatterplotLayer, PathLayer, TextLayer, BitmapLayer } from "@deck.gl/layers";
import { TileLayer } from "@deck.gl/geo-layers";
import { useSocket } from "../../context/SocketContext";
import { Sun, Moon, Compass, Plus, Minus, Map as MapIcon, Car, Navigation } from "lucide-react";

// Real High-Resolution Google Maps / Carto Tile Providers
const TILE_SOURCES = {
  google_day: {
    name: "Google Maps",
    url: "https://a.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}@2x.png",
    isLight: true,
  },
  google_dark: {
    name: "Dark Nav",
    url: "https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png",
    isLight: false,
  },
  osm: {
    name: "OpenStreetMap",
    url: "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
    isLight: true,
  },
};

export default function TrafficMap({
  cameraPreset,
  showRoads = true,
  onSelectIntersection,
}) {
  const { telemetry, network } = useSocket();
  const { isQuantumOptimized, vehicles = [], intersections = [] } = telemetry;
  const roadSegments = network?.roadSegments || [];

  // Default to Google Maps Day Style for maximum street & building clarity
  const [activeTileKey, setActiveTileKey] = useState("google_day");
  const [selectedVehicleId, setSelectedVehicleId] = useState(null);
  const [showAllRoutes, setShowAllRoutes] = useState(true);

  // Local Dense Viewport
  const [viewState, setViewState] = useState({
    longitude: 77.6412,
    latitude: 12.9715,
    zoom: 16.5,
    pitch: 35,
    bearing: -10,
    minZoom: 11,
    maxZoom: 19,
    maxPitch: 65,
  });

  // Animated tick for pulses
  const [animTime, setAnimTime] = useState(0);
  useEffect(() => {
    let frameId;
    const animate = () => {
      setAnimTime((t) => (t + 0.04) % (Math.PI * 2));
      frameId = requestAnimationFrame(animate);
    };
    frameId = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(frameId);
  }, []);

  // Bangalore Camera Fly-To Presets
  useEffect(() => {
    if (!cameraPreset) return;
    if (cameraPreset === "overview") {
      setViewState((prev) => ({
        ...prev,
        longitude: 77.6412,
        latitude: 12.9715,
        zoom: 16.5,
        pitch: 30,
        bearing: -5,
        transitionDuration: 1200,
      }));
    } else if (cameraPreset === "bottleneck") {
      // Central Bottleneck Focus
      setViewState((prev) => ({
        ...prev,
        longitude: 77.6412,
        latitude: 12.9715,
        zoom: 17.2,
        pitch: 50,
        bearing: -20,
        transitionDuration: 1200,
      }));
    } else if (cameraPreset === "domlur") {
      // Outer ring
      setViewState((prev) => ({
        ...prev,
        longitude: 77.6385,
        latitude: 12.9690,
        zoom: 17.0,
        pitch: 45,
        bearing: 30,
        transitionDuration: 1200,
      }));
    } else if (cameraPreset === "bypass") {
      // Bypass ring
      setViewState((prev) => ({
        ...prev,
        longitude: 77.6440,
        latitude: 12.9740,
        zoom: 17.0,
        pitch: 42,
        bearing: 15,
        transitionDuration: 1200,
      }));
    }
  }, [cameraPreset]);

  const activeTileConfig = TILE_SOURCES[activeTileKey] || TILE_SOURCES.google_day;
  const isLightMap = activeTileConfig.isLight;

  // Deck.gl Layers Configuration
  const layers = useMemo(() => {
    const pulseFactor = Math.sin(animTime);
    const layersList = [];

    // 0. Base Google Maps City Grid Tiles Layer
    layersList.push(
      new TileLayer({
        id: `city-map-tiles-${activeTileKey}`,
        data: activeTileConfig.url,
        minZoom: 0,
        maxZoom: 19,
        tileSize: 256,
        renderSubLayers: (props) => {
          const {
            bbox: { west, south, east, north },
          } = props.tile;
          return new BitmapLayer(props, {
            data: null,
            image: props.data,
            bounds: [west, south, east, north],
          });
        },
      })
    );

    // 1. Street Corridor Flow Underlays
    if (showRoads && roadSegments.length > 0) {
      layersList.push(
        new PathLayer({
          id: "road-network-underlay",
          data: roadSegments,
          getPath: (d) => d.path || [d.fromCoord, d.toCoord],
          getColor: (d) => {
            if (isQuantumOptimized && d.isBypass) return [16, 185, 129, 160];
            if (!isQuantumOptimized && d.isBottleneck) return [225, 29, 72, 170];
            return isLightMap ? [148, 163, 184, 110] : [56, 189, 248, 90];
          },
          getWidth: 7,
          widthUnits: "pixels",
          jointRounded: true,
          capRounded: true,
          pickable: false,
          updateTriggers: {
            getColor: [isQuantumOptimized, isLightMap],
          },
        })
      );
    }

    // 2. Active Ground-Level GPS Turn-by-Turn Route Trajectories (On the Streets, NOT in the air!)
    if (showAllRoutes && vehicles.length > 0) {
      // Filter vehicles with active paths
      const validPathVehicles = vehicles.filter(
        (v) => v.remainingPath && v.remainingPath.length >= 2
      );

      // Route Casing
      layersList.push(
        new PathLayer({
          id: "vehicle-routes-casing",
          data: validPathVehicles,
          getPath: (d) => d.remainingPath,
          getColor: [15, 23, 42, 180],
          getWidth: 7,
          widthUnits: "pixels",
          jointRounded: true,
          capRounded: true,
          pickable: false,
        }),
        // Inner Glowing GPS Navigation Line (Green for Quantum Detour, Red for Congested, Blue for Normal)
        new PathLayer({
          id: "vehicle-routes-core",
          data: validPathVehicles,
          getPath: (d) => d.remainingPath,
          getColor: (d) => {
            const isSelected = selectedVehicleId === d.id;
            if (isSelected) return [245, 158, 11, 255]; // Selected Car: Gold Route
            if (d.status === "quantum_rerouted" || d.isRerouted) {
              return [16, 185, 129, 235]; // Optimal Quantum Bypass Route: Emerald Green
            }
            if (d.status === "congested") {
              return [239, 68, 68, 235]; // Congested Route: Crimson Red
            }
            return [2, 132, 199, 200]; // Normal Route: Navigation Blue
          },
          getWidth: (d) => (selectedVehicleId === d.id ? 5.5 : 3.5),
          widthUnits: "pixels",
          jointRounded: true,
          capRounded: true,
          pickable: false,
          updateTriggers: {
            getColor: [isQuantumOptimized, selectedVehicleId],
            getWidth: [selectedVehicleId],
          },
        })
      );
    }

    // 3. Prominent, Clearly Visible 20 Vehicles (Large Navigation Pods with Heading Direction)
    if (vehicles.length > 0) {
      // Outer Glowing Ring / Aura
      layersList.push(
        new ScatterplotLayer({
          id: "vehicles-glow",
          data: vehicles,
          getPosition: (d) => [d.pos[0], d.pos[1], 1],
          getRadius: (d) => {
            const isSelected = selectedVehicleId === d.id;
            if (isSelected) return 24 + pulseFactor * 4;
            if (d.status === "quantum_rerouted" || d.isRerouted) return 20 + pulseFactor * 3;
            if (d.status === "congested") return 18 + pulseFactor * 2.5;
            return 14;
          },
          getFillColor: (d) => {
            const isSelected = selectedVehicleId === d.id;
            if (isSelected) return [245, 158, 11, 200];
            if (d.status === "quantum_rerouted" || d.isRerouted) return [16, 185, 129, 200]; // Emerald Glow
            if (d.status === "congested") return [239, 68, 68, 200]; // Red Congestion Glow
            if (d.status === "slow") return [245, 158, 11, 170];
            return [2, 132, 199, 170]; // Blue Flow Glow
          },
          radiusMinPixels: 8,
          radiusMaxPixels: 28,
          pickable: false,
          updateTriggers: {
            getRadius: [animTime, selectedVehicleId],
            getFillColor: [isQuantumOptimized, selectedVehicleId],
          },
        }),
        // Large Solid Vehicle Body (Pod with White Border)
        new ScatterplotLayer({
          id: "vehicles-core",
          data: vehicles,
          getPosition: (d) => [d.pos[0], d.pos[1], 2],
          getRadius: 10,
          getFillColor: (d) => {
            const isSelected = selectedVehicleId === d.id;
            if (isSelected) return [245, 158, 11, 255];
            if (d.status === "quantum_rerouted" || d.isRerouted) return [16, 185, 129, 255]; // Vibrant Emerald
            if (d.status === "congested") return [225, 29, 72, 255]; // Crimson Red
            if (d.status === "slow") return [245, 158, 11, 255]; // Amber
            return [2, 132, 199, 255]; // Navigation Blue
          },
          getLineColor: [255, 255, 255, 255],
          getLineWidth: 2.5,
          lineWidthUnits: "pixels",
          radiusMinPixels: 7,
          radiusMaxPixels: 16,
          pickable: true,
          onClick: (info) => {
            if (info.object) {
              setSelectedVehicleId(selectedVehicleId === info.object.id ? null : info.object.id);
            }
          },
          updateTriggers: {
            getFillColor: [isQuantumOptimized, selectedVehicleId],
          },
        }),
        // Vehicle Text Badges (Shows Car # and REROUTED / SPEED Tag)
        new TextLayer({
          id: "vehicles-badges",
          data: vehicles,
          getPosition: (d) => [d.pos[0], d.pos[1], 5],
          getText: (d) => {
            if (d.status === "quantum_rerouted" || d.isRerouted) {
              return `⚡ ${d.id}: REROUTED (${d.speed}k)`;
            }
            if (d.status === "congested") {
              return `🛑 ${d.id}: QUEUED (${d.speed}k)`;
            }
            return `🚗 ${d.id} (${d.speed}k)`;
          },
          getSize: 11,
          getColor: (d) => {
            if (d.status === "quantum_rerouted" || d.isRerouted) return [16, 185, 129, 255];
            if (d.status === "congested") return [225, 29, 72, 255];
            return isLightMap ? [15, 23, 42, 255] : [255, 255, 255, 240];
          },
          getTextAnchor: "middle",
          getAlignmentBaseline: "bottom",
          pixelOffset: [0, -14],
          fontFamily: "Inter, sans-serif",
          fontWeight: 800,
          background: true,
          getBackgroundColor: isLightMap ? [255, 255, 255, 245] : [15, 23, 42, 235],
          backgroundPadding: [5, 2],
          pickable: false,
          updateTriggers: {
            getColor: [isLightMap, isQuantumOptimized],
            getBackgroundColor: [isLightMap],
          },
        })
      );
    }

    // 4. Bangalore Traffic Lights & Intersections (Pins with Phase Timers)
    if (intersections.length > 0) {
      layersList.push(
        // Outer Radar Signal Halo
        new ScatterplotLayer({
          id: "intersections-pulse-ring",
          data: intersections,
          getPosition: (d) => [d.coordinates[0], d.coordinates[1], 0],
          getRadius: (d) => 26 + (d.queueCount > 2 ? 10 : 0) + pulseFactor * 5,
          getFillColor: [0, 0, 0, 0],
          getLineColor: (d) => {
            if (d.manualOverride === "FORCE_RED" || d.phase === "ALL_RED") return [225, 29, 72, 230];
            if (d.manualOverride === "FORCE_GREEN" || d.phase === "NS_GREEN") return [16, 185, 129, 240];
            if (d.phase === "YELLOW") return [245, 158, 11, 240];
            return [16, 185, 129, 230];
          },
          getLineWidth: 2.5,
          lineWidthUnits: "pixels",
          stroked: true,
          filled: false,
          radiusMinPixels: 12,
          radiusMaxPixels: 36,
          pickable: false,
          updateTriggers: {
            getRadius: [animTime],
          },
        }),
        // Signal Core Beacon
        new ScatterplotLayer({
          id: "intersections-core",
          data: intersections,
          getPosition: (d) => [d.coordinates[0], d.coordinates[1], 3],
          getRadius: 14,
          getFillColor: (d) => {
            if (d.manualOverride === "FORCE_RED" || d.phase === "ALL_RED") return [225, 29, 72, 255];
            if (d.manualOverride === "FORCE_GREEN") return [0, 200, 120, 255];
            if (d.phase === "YELLOW") return [245, 158, 11, 255];
            if (d.phase === "NS_GREEN") return [16, 185, 129, 255];
            return [2, 132, 199, 255];
          },
          getLineColor: [255, 255, 255, 255],
          getLineWidth: 2,
          lineWidthUnits: "pixels",
          radiusMinPixels: 8,
          radiusMaxPixels: 18,
          pickable: true,
          onClick: (info) => {
            if (info.object && onSelectIntersection) {
              setTimeout(() => onSelectIntersection(info.object), 0);
            }
          },
        }),
        // Intersection Google Maps-style Callout Labels
        new TextLayer({
          id: "intersections-labels",
          data: intersections,
          getPosition: (d) => [d.coordinates[0], d.coordinates[1], 6],
          getText: (d) => `${d.id} - ${d.name.split(" ")[0]} [${d.timer}s]`,
          getSize: 12,
          getColor: isLightMap ? [15, 23, 42, 255] : [255, 255, 255, 240],
          getTextAnchor: "middle",
          getAlignmentBaseline: "bottom",
          pixelOffset: [0, -18],
          fontFamily: "Inter, sans-serif",
          fontWeight: 700,
          background: true,
          getBackgroundColor: isLightMap ? [255, 255, 255, 240] : [15, 23, 42, 230],
          backgroundPadding: [5, 3],
          pickable: false,
          updateTriggers: {
            getColor: [isLightMap],
            getBackgroundColor: [isLightMap],
          },
        })
      );
    }

    return layersList;
  }, [
    vehicles,
    intersections,
    roadSegments,
    isQuantumOptimized,
    showRoads,
    showAllRoutes,
    selectedVehicleId,
    activeTileKey,
    isLightMap,
    animTime,
    onSelectIntersection,
  ]);

  return (
    <div className="relative w-full h-full overflow-hidden bg-[#e5e3df]">
      <DeckGL
        viewState={viewState}
        onViewStateChange={({ viewState: newViewState }) => setViewState(newViewState)}
        controller={{
          dragRotate: true,
          scrollZoom: true,
          doubleClickZoom: true,
          touchRotate: true,
        }}
        layers={layers}
        getTooltip={({ object }) => {
          if (!object) return null;
          if (object.queueCount !== undefined) {
            return {
              html: `
                <div class="p-2.5 bg-slate-900/95 border border-cyan-500/40 rounded-lg shadow-xl text-xs font-mono text-slate-100">
                  <div class="font-bold text-cyan-400 text-sm mb-1">${object.id}: ${object.name}</div>
                  <div>Signal Phase: <span class="text-emerald-400 font-bold">${object.phase}</span></div>
                  <div>Timer: <span class="text-amber-400 font-bold">${object.timer}s</span></div>
                  <div>Queue: <span class="text-rose-400 font-bold">${object.queueCount} vehicles</span></div>
                  ${object.manualOverride ? `<div class="text-purple-400 mt-1 font-bold">OVERRIDE: ${object.manualOverride}</div>` : ""}
                </div>
              `,
            };
          }
          if (object.speed !== undefined) {
            const isRerouted = object.status === "quantum_rerouted" || object.isRerouted;
            return {
              html: `
                <div class="p-3 bg-slate-900/95 border ${isRerouted ? "border-emerald-400/70 shadow-[0_0_15px_rgba(0,255,170,0.3)]" : "border-cyan-500/40"} rounded-xl shadow-xl text-xs font-mono text-slate-100 min-w-[200px]">
                  <div class="flex items-center justify-between gap-2 mb-1.5">
                    <span class="font-bold text-sm ${isRerouted ? "text-emerald-400" : "text-cyan-400"}">${object.id}</span>
                    <span class="px-2 py-0.5 rounded text-[10px] font-bold ${isRerouted ? "bg-emerald-950 text-emerald-300 border border-emerald-500/40" : "bg-cyan-950 text-cyan-300"}">${object.speed} km/h</span>
                  </div>
                  <div class="text-[11px] text-slate-300 mb-1">
                    Route: <span class="text-slate-200 font-medium">${object.startName || "Origin"}</span> → <span class="text-slate-200 font-medium">${object.destName || "Destination"}</span>
                  </div>
                  <div>Status: <span class="font-bold uppercase ${isRerouted ? "text-emerald-400" : "text-amber-300"}">${object.status}</span></div>
                  ${isRerouted ? '<div class="text-emerald-300 text-[10px] mt-1.5 font-bold p-1 bg-emerald-950/60 rounded border border-emerald-500/30">⚡ Quantum Optimal Bypass Active</div>' : ""}
                  <div class="text-[10px] text-slate-500 mt-1">Click car to isolate route</div>
                </div>
              `,
            };
          }
          return null;
        }}
      />

      {/* Map Control Tools (Google Maps Style Switcher, Route Toggle, 2D/3D & Zoom) */}
      <div className="absolute bottom-6 right-6 flex flex-col gap-2 z-10">
        {/* Route Paths Toggle */}
        <button
          onClick={() => setShowAllRoutes(!showAllRoutes)}
          className={`px-3 py-1.5 rounded-xl text-xs font-mono flex items-center justify-center gap-1.5 transition-all shadow-xl backdrop-blur-md border ${
            showAllRoutes
              ? "bg-slate-900/90 text-emerald-400 border-emerald-500/50"
              : "bg-slate-900/90 text-slate-400 border-slate-700/80"
          }`}
          title="Toggle GPS Navigation Lines on Streets"
        >
          <Navigation className="w-3.5 h-3.5" />
          <span>{showAllRoutes ? "GPS Routes: ON" : "GPS Routes: OFF"}</span>
        </button>

        {/* Style Switcher (Google Day vs Dark Nav vs OSM) */}
        <div className="flex items-center gap-1 p-1 bg-slate-900/90 border border-slate-700/80 rounded-xl shadow-xl backdrop-blur-md">
          <button
            onClick={() => setActiveTileKey("google_day")}
            className={`px-2.5 py-1.5 rounded-lg text-xs font-mono flex items-center gap-1.5 transition-all ${
              activeTileKey === "google_day"
                ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/50 shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
            title="Google Maps Style (Day & Street Labels)"
          >
            <Sun className="w-3.5 h-3.5 text-amber-400" />
            <span className="font-medium">Google Maps</span>
          </button>

          <button
            onClick={() => setActiveTileKey("google_dark")}
            className={`px-2.5 py-1.5 rounded-lg text-xs font-mono flex items-center gap-1.5 transition-all ${
              activeTileKey === "google_dark"
                ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/50 shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
            title="Google Navigation (Dark Mode)"
          >
            <Moon className="w-3.5 h-3.5 text-cyan-400" />
            <span className="font-medium">Dark Nav</span>
          </button>

          <button
            onClick={() => setActiveTileKey("osm")}
            className={`px-2.5 py-1.5 rounded-lg text-xs font-mono flex items-center gap-1.5 transition-all ${
              activeTileKey === "osm"
                ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/50 shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
            title="OpenStreetMap Standard"
          >
            <MapIcon className="w-3.5 h-3.5 text-emerald-400" />
            <span className="font-medium">OSM</span>
          </button>
        </div>

        {/* 2D / 3D Tilt Button & Zoom Buttons */}
        <div className="flex items-center justify-between gap-1.5 p-1 bg-slate-900/90 border border-slate-700/80 rounded-xl shadow-xl backdrop-blur-md">
          <button
            onClick={() =>
              setViewState((prev) => ({
                ...prev,
                pitch: prev.pitch > 20 ? 0 : 48,
                bearing: 0,
              }))
            }
            className="flex-1 px-3 py-1.5 text-xs font-mono text-cyan-300 hover:text-cyan-100 rounded-lg flex items-center justify-center gap-1 transition-all active:scale-95"
            title="Toggle 2D Overhead / 3D Perspective"
          >
            <Compass className="w-3.5 h-3.5" />
            <span>{viewState.pitch > 20 ? "3D (48°)" : "2D (0°)"}</span>
          </button>

          <div className="h-4 w-px bg-slate-700" />

          <button
            onClick={() => setViewState((prev) => ({ ...prev, zoom: Math.min(prev.zoom + 0.8, 19) }))}
            className="p-1.5 text-slate-300 hover:text-cyan-300 rounded-lg hover:bg-slate-800 transition-all active:scale-95"
            title="Zoom In"
          >
            <Plus className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => setViewState((prev) => ({ ...prev, zoom: Math.max(prev.zoom - 0.8, 11) }))}
            className="p-1.5 text-slate-300 hover:text-cyan-300 rounded-lg hover:bg-slate-800 transition-all active:scale-95"
            title="Zoom Out"
          >
            <Minus className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
}

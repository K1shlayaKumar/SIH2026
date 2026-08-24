// Main Socket.io and Express Server for SIH Quantum Traffic Simulation
import express from "express";
import http from "http";
import { Server } from "socket.io";
import cors from "cors";
import { TrafficEngine } from "./simulation/trafficEngine.js";
import { buildRoadNetwork, CITY_CENTER } from "./simulation/grid.js";

const app = express();
app.use(cors());
app.use(express.json());

const server = http.createServer(app);
const io = new Server(server, {
  cors: {
    origin: "*",
    methods: ["GET", "POST"],
  },
});

const PORT = process.env.PORT || 5000;
const engine = new TrafficEngine();
const { intersections, roadSegments } = buildRoadNetwork();

// REST API for static metadata / health check
app.get("/api/health", (req, res) => {
  res.json({
    status: "online",
    service: "SIH-Quantum-Traffic-Optimizer",
    timestamp: new Date().toISOString(),
    vehicles: engine.vehicles.length,
    isQuantumOptimized: engine.isQuantumOptimized,
  });
});

app.get("/api/network", (req, res) => {
  res.json({
    cityCenter: CITY_CENTER,
    intersections,
    roadSegments,
  });
});

// Socket.io Connection & Event Handling
io.on("connection", (socket) => {
  console.log(`[Socket] Client connected: ${socket.id}`);

  // Send initial network topology & immediate telemetry
  socket.emit("network_data", {
    cityCenter: CITY_CENTER,
    intersections,
    roadSegments,
  });

  socket.emit("traffic_update", engine.getTelemetry());

  // 1. Toggle Quantum Optimization
  socket.on("toggle_optimization", (enabled) => {
    console.log(`[Socket] toggle_optimization: ${enabled}`);
    engine.setOptimization(enabled);
    io.emit("optimization_state", { isQuantumOptimized: engine.isQuantumOptimized });
    io.emit("traffic_update", engine.getTelemetry());
  });

  // 2. Manual Light Override
  socket.on("override_light", (data) => {
    // data: { intersectionId: 'INT-4', color: 'GREEN' | 'RED' | 'AUTO' }
    const { intersectionId, color } = data || {};
    console.log(`[Socket] override_light: ${intersectionId} -> ${color}`);

    let overrideState = null;
    if (color === "GREEN" || color === "FORCE_GREEN") overrideState = "FORCE_GREEN";
    else if (color === "RED" || color === "FORCE_RED") overrideState = "FORCE_RED";
    else overrideState = "AUTO";

    engine.setLightOverride(intersectionId, overrideState);
    io.emit("traffic_update", engine.getTelemetry());
  });

  // 3. Reset Simulation
  socket.on("reset_simulation", () => {
    console.log("[Socket] reset_simulation");
    engine.initVehicles();
    engine.setOptimization(false);
    io.emit("traffic_update", engine.getTelemetry());
  });

  // 4. Change vehicle fleet density
  socket.on("set_vehicle_count", (count) => {
    const validCount = Math.max(50, Math.min(600, Number(count) || 320));
    console.log(`[Socket] set_vehicle_count: ${validCount}`);
    engine.targetVehicleCount = validCount;
    engine.initVehicles();
    io.emit("traffic_update", engine.getTelemetry());
  });

  socket.on("disconnect", () => {
    console.log(`[Socket] Client disconnected: ${socket.id}`);
  });
});

// Simulation Loop: 25 FPS (40ms interval)
const TICK_RATE_MS = 40;
const DT = TICK_RATE_MS / 1000;

setInterval(() => {
  engine.update(DT);
  const telemetry = engine.getTelemetry();
  io.emit("traffic_update", telemetry);
}, TICK_RATE_MS);

server.listen(PORT, () => {
  console.log(`
=====================================================
🚀 SIH Quantum-Inspired Traffic Server RUNNING
📡 Port: ${PORT}
🌐 REST API: http://localhost:${PORT}/api/health
⚡ WebSocket Engine: 25 FPS Real-Time Broadcast
=====================================================
`);
});

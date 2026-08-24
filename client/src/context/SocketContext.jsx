// WebSocket Context for Real-Time Simulation State
import React, { createContext, useContext, useEffect, useState, useCallback, useRef } from "react";
import { io } from "socket.io-client";
import { sound } from "../utils/audio";

const SocketContext = createContext(null);

export const SocketProvider = ({ children }) => {
  const [socket, setSocket] = useState(null);
  const [connected, setConnected] = useState(false);
  const [network, setNetwork] = useState(null);
  const [telemetry, setTelemetry] = useState({
    isQuantumOptimized: false,
    metrics: {
      avgWaitTime: 95,
      efficiency: 32.5,
      avgSpeed: 14.2,
      co2Reduction: 2.1,
      hotspots: 3,
      quantumConvergence: 22.4,
      totalVehicles: 320,
      congestedVehicles: 140,
      flowingVehicles: 80,
      totalThroughput: 0,
      simulationTime: 0,
    },
    intersections: [],
    vehicles: [],
  });

  const [metricsHistory, setMetricsHistory] = useState({
    waitTime: [95, 98, 102, 108, 115, 120, 128, 132, 140],
    efficiency: [35, 34, 32, 30, 28, 29, 27, 26, 25],
    speed: [18, 17, 15, 14, 13, 12, 11, 10, 9],
  });

  const prevQuantumRef = useRef(false);

  useEffect(() => {
    // Connect to server (proxied in Vite dev server or direct port 5000)
    const socketInstance = io(window.location.origin, {
      transports: ["websocket", "polling"],
      reconnectionAttempts: 10,
      reconnectionDelay: 1000,
    });

    socketInstance.on("connect", () => {
      console.log("[Socket] Connected to simulation engine:", socketInstance.id);
      setConnected(true);
    });

    socketInstance.on("disconnect", () => {
      console.log("[Socket] Disconnected");
      setConnected(false);
    });

    socketInstance.on("network_data", (data) => {
      setNetwork(data);
    });

    socketInstance.on("traffic_update", (data) => {
      setTelemetry((prev) => {
        // Trigger sound effects on quantum state transition
        if (data.isQuantumOptimized && !prevQuantumRef.current) {
          sound.playQuantumEngage();
        } else if (!data.isQuantumOptimized && prevQuantumRef.current) {
          sound.playQuantumDisengage();
        }
        prevQuantumRef.current = data.isQuantumOptimized;

        // Record history samples periodically
        if (data.metrics) {
          setMetricsHistory((h) => ({
            waitTime: [...h.waitTime.slice(-25), data.metrics.avgWaitTime],
            efficiency: [...h.efficiency.slice(-25), data.metrics.efficiency],
            speed: [...h.speed.slice(-25), data.metrics.avgSpeed],
          }));
        }

        return data;
      });
    });

    setSocket(socketInstance);

    return () => {
      socketInstance.disconnect();
    };
  }, []);

  const toggleOptimization = useCallback(
    (enabled) => {
      if (!socket) return;
      socket.emit("toggle_optimization", enabled);
    },
    [socket]
  );

  const overrideLight = useCallback(
    (intersectionId, color) => {
      if (!socket) return;
      sound.playOverride();
      socket.emit("override_light", { intersectionId, color });
    },
    [socket]
  );

  const resetSimulation = useCallback(() => {
    if (!socket) return;
    sound.playClick();
    socket.emit("reset_simulation");
  }, [socket]);

  const setVehicleCount = useCallback(
    (count) => {
      if (!socket) return;
      socket.emit("set_vehicle_count", count);
    },
    [socket]
  );

  return (
    <SocketContext.Provider
      value={{
        socket,
        connected,
        network,
        telemetry,
        metricsHistory,
        toggleOptimization,
        overrideLight,
        resetSimulation,
        setVehicleCount,
      }}
    >
      {children}
    </SocketContext.Provider>
  );
};

export const useSocket = () => {
  const ctx = useContext(SocketContext);
  if (!ctx) throw new Error("useSocket must be used within a SocketProvider");
  return ctx;
};

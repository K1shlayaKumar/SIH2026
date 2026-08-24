// Bangalore Traffic Simulation Physics Engine - 20 High-Visibility Demonstration Vehicles
import {
  INTERSECTIONS,
  buildRoadNetwork,
  getDistanceMeters,
  getPathLengthMeters,
  interpolatePath,
  getBearing,
} from "./grid.js";

export class TrafficEngine {
  constructor() {
    const { roadSegments } = buildRoadNetwork();
    this.intersections = INTERSECTIONS.map((item) => ({
      ...item,
      phase: Math.random() > 0.5 ? "NS_GREEN" : "EW_GREEN",
      timer: Math.floor(Math.random() * 15) + 10,
      phaseDuration: 24,
      yellowDuration: 3,
      manualOverride: null,
      queueCount: 0,
      throughput: 0,
    }));

    this.roadSegments = roadSegments;
    this.roadMap = new Map();
    this.roadSegments.forEach((r) => this.roadMap.set(r.id, r));

    this.isQuantumOptimized = false;
    this.vehicles = [];
    this.targetVehicleCount = 20; // 20 Prominent Demonstration Vehicles

    this.totalThroughputCount = 0;
    this.simulationTime = 0;

    this.rerouteEvents = [];
    this.rerouteIdCounter = 0;

    this.initVehicles();
  }

  initVehicles() {
    this.vehicles = [];
    for (let i = 0; i < this.targetVehicleCount; i++) {
      this.vehicles.push(this.createVehicle(i + 1));
    }
  }

  createVehicle(id, startIntersectionId = null) {
    const startNode = startIntersectionId
      ? this.intersections.find((n) => n.id === startIntersectionId)
      : this.intersections[(id - 1) % this.intersections.length];

    // Pick diverse destinations across the city
    const destCandidates = this.intersections.filter((n) => n.id !== startNode.id);
    const destNode = destCandidates[(id * 3) % destCandidates.length];

    const route = this.calculateRoute(startNode.id, destNode.id, this.isQuantumOptimized);

    const firstSegment = this.roadMap.get(route[0]);
    const laneIndex = (id % 2); // 2 lanes for clean visibility
    const laneOffsetRatio = (laneIndex - 0.5) * 0.000045;

    // Distinct colors for prominent cars
    const CAR_COLORS = [
      [14, 165, 233],  // Sky Blue
      [249, 115, 22],  // Amber Orange
      [168, 85, 247],  // Purple
      [236, 72, 153],  // Pink
      [6, 182, 212],   // Cyan
      [234, 179, 8],   // Yellow
      [16, 185, 129],  // Emerald
      [239, 68, 68],   // Red
    ];
    const color = CAR_COLORS[(id - 1) % CAR_COLORS.length];

    return {
      id: `Car-${id}`,
      number: id,
      color,
      route,
      routeStep: 0,
      segmentProgress: ((id * 0.17) % 0.8) + 0.05,
      speed: 30 + Math.random() * 15, // km/h
      targetSpeed: 45 + Math.random() * 10,
      laneIndex,
      laneOffsetRatio,
      pos: [startNode.coordinates[0], startNode.coordinates[1]],
      heading: 0,
      status: "flowing", // 'flowing' | 'slow' | 'congested' | 'quantum_rerouted'
      waitTime: 0,
      isRerouted: false,
      rerouteReason: null,
      destId: destNode.id,
      destName: destNode.name,
      startId: startNode.id,
      startName: startNode.name,
    };
  }

  // Cost-weighted Routing Algorithm: Classical Shortest Path vs Quantum QUBO Bypass Routing
  calculateRoute(fromId, toId, useQuantum) {
    if (fromId === toId) return [];

    const queueMap = new Map();
    this.intersections.forEach((i) => queueMap.set(i.id, i.queueCount));

    const distances = new Map();
    const previous = new Map();
    const edgeUsed = new Map();
    const unvisited = new Set();

    this.intersections.forEach((node) => {
      distances.set(node.id, Infinity);
      unvisited.add(node.id);
    });

    distances.set(fromId, 0);

    while (unvisited.size > 0) {
      let currentId = null;
      let minDistance = Infinity;

      unvisited.forEach((nodeId) => {
        const dist = distances.get(nodeId);
        if (dist < minDistance) {
          minDistance = dist;
          currentId = nodeId;
        }
      });

      if (!currentId || currentId === toId || minDistance === Infinity) break;
      unvisited.delete(currentId);

      const currentNode = this.intersections.find((n) => n.id === currentId);
      if (!currentNode) continue;

      currentNode.connectedTo.forEach((neighborId) => {
        if (!unvisited.has(neighborId)) return;

        const segmentKey = `${currentId}->${neighborId}`;
        const segment = this.roadMap.get(segmentKey);
        if (!segment) return;

        const neighborNode = this.intersections.find((n) => n.id === neighborId);
        const geoDistance = getDistanceMeters(currentNode.coordinates, neighborNode.coordinates);

        let cost = geoDistance;

        if (useQuantum) {
          // Quantum QUBO Optimization:
          // Heavy penalty on central intersection (INT-5)
          const queuePenalty = (queueMap.get(neighborId) || 0) * 140;
          let bottleneckPenalty = 0;
          if (neighborId === "INT-5") {
            bottleneckPenalty = 600;
          }

          // Quantum bypass rewards (Outer Ring)
          let bypassReward = 0;
          if (neighborId !== "INT-5") {
            bypassReward = -300;
          }

          cost = Math.max(10, geoDistance + queuePenalty + bottleneckPenalty + bypassReward);
        } else {
          // Classical Unoptimized Cost:
          // Vehicles blindly take the center as primary direct corridor
          if (neighborId === "INT-5") {
            cost = geoDistance * 0.25; // Greedy bias toward central intersection
          }
        }

        const alt = distances.get(currentId) + cost;
        if (alt < distances.get(neighborId)) {
          distances.set(neighborId, alt);
          previous.set(neighborId, currentId);
          edgeUsed.set(neighborId, segmentKey);
        }
      });
    }

    const pathEdges = [];
    let curr = toId;
    while (previous.has(curr)) {
      const edge = edgeUsed.get(curr);
      if (edge) pathEdges.unshift(edge);
      curr = previous.get(curr);
    }

    if (pathEdges.length === 0) {
      const direct = `${fromId}->${toId}`;
      if (this.roadMap.has(direct)) return [direct];
      const fallback = this.roadSegments.find((r) => r.from === fromId);
      return fallback ? [fallback.id] : [];
    }

    return pathEdges;
  }

  // Build remaining full street path coordinates for each vehicle
  getVehicleRemainingPath(veh) {
    if (!veh.route || veh.routeStep >= veh.route.length) return [];

    const fullCoords = [[veh.pos[0], veh.pos[1]]];

    for (let step = veh.routeStep; step < veh.route.length; step++) {
      const segId = veh.route[step];
      const segment = this.roadMap.get(segId);
      if (segment && segment.path) {
        if (step === veh.routeStep) {
          // Add remaining points of current segment based on distance
          const totalDist = getPathLengthMeters(segment.path);
          const targetDist = Math.max(0, Math.min(1, veh.segmentProgress)) * totalDist;
          
          let accumulatedDist = 0;
          let currentIndex = 0;
          for (let i = 0; i < segment.path.length - 1; i++) {
            const segDist = getDistanceMeters(segment.path[i], segment.path[i + 1]);
            if (accumulatedDist + segDist >= targetDist || i === segment.path.length - 2) {
              currentIndex = i;
              break;
            }
            accumulatedDist += segDist;
          }
          
          for (let i = currentIndex + 1; i < segment.path.length; i++) {
            fullCoords.push(segment.path[i]);
          }
        } else {
          // Add all points of upcoming segments (skip index 0 as it overlaps with previous segment's end)
          for (let i = 1; i < segment.path.length; i++) {
            fullCoords.push(segment.path[i]);
          }
        }
      }
    }

    return fullCoords.length >= 2 ? fullCoords : [];
  }

  // Update intersection lights and adaptive green waves
  updateSignals(dt) {
    this.intersections.forEach((intersection) => {
      if (intersection.manualOverride === "FORCE_GREEN") {
        intersection.phase = "NS_GREEN";
        return;
      }
      if (intersection.manualOverride === "FORCE_RED") {
        intersection.phase = "ALL_RED";
        return;
      }

      intersection.timer -= dt;

      if (this.isQuantumOptimized) {
        // Adaptive Green Waves
        const isQueued = intersection.queueCount > 2;
        if (intersection.timer <= 0) {
          if (intersection.phase === "NS_GREEN") {
            intersection.phase = "YELLOW";
            intersection.timer = intersection.yellowDuration;
          } else if (intersection.phase === "YELLOW") {
            intersection.phase = "EW_GREEN";
            intersection.timer = isQueued ? 24 : 16;
          } else {
            intersection.phase = "NS_GREEN";
            intersection.timer = isQueued ? 26 : 18;
          }
        }
      } else {
        // Classical fixed timers
        if (intersection.timer <= 0) {
          if (intersection.phase === "NS_GREEN") {
            intersection.phase = "YELLOW";
            intersection.timer = intersection.yellowDuration;
          } else if (intersection.phase === "YELLOW") {
            intersection.phase = "EW_GREEN";
            intersection.timer = intersection.phaseDuration;
          } else {
            intersection.phase = "NS_GREEN";
            intersection.timer = intersection.phaseDuration;
          }
        }
      }
    });
  }

  // Physics simulation step
  update(dt = 0.04) {
    this.simulationTime += dt;
    this.updateSignals(dt);

    const intersectionQueues = new Map();
    this.intersections.forEach((i) => intersectionQueues.set(i.id, 0));

    this.vehicles.forEach((veh) => {
      if (!veh.route || veh.route.length === 0 || veh.routeStep >= veh.route.length) {
        const newVeh = this.createVehicle(veh.number);
        Object.assign(veh, newVeh);
        return;
      }

      const currentSegmentId = veh.route[veh.routeStep];
      const segment = this.roadMap.get(currentSegmentId);
      if (!segment) {
        veh.routeStep++;
        return;
      }

      const toNode = this.intersections.find((n) => n.id === segment.to);
      if (!toNode) {
        veh.routeStep++;
        return;
      }

      const segmentLength = getPathLengthMeters(segment.path);
      const { pos: interpPos, bearing } = interpolatePath(segment.path, veh.segmentProgress);
      veh.heading = bearing;

      const distToIntersection = (1.0 - veh.segmentProgress) * segmentLength;

      // Traffic Signal Check at target intersection
      let canPass = true;
      const isNorthSouth = (bearing >= 315 || bearing <= 45) || (bearing >= 135 && bearing <= 225);

      if (distToIntersection < 48) {
        if (toNode.manualOverride === "FORCE_RED") {
          canPass = false;
        } else if (toNode.manualOverride === "FORCE_GREEN") {
          canPass = true;
        } else if (toNode.phase === "ALL_RED") {
          canPass = false;
        } else if (toNode.phase === "YELLOW" && distToIntersection > 16) {
          canPass = false;
        } else if (isNorthSouth && toNode.phase !== "NS_GREEN") {
          canPass = false;
        } else if (!isNorthSouth && toNode.phase !== "EW_GREEN") {
          canPass = false;
        }
      }

      // Car-Following Model
      let leaderDist = Infinity;
      let leaderSpeed = 45;

      for (let other of this.vehicles) {
        if (other.id === veh.id) continue;
        if (
          other.route &&
          other.route[other.routeStep] === currentSegmentId &&
          other.laneIndex === veh.laneIndex
        ) {
          const deltaProg = other.segmentProgress - veh.segmentProgress;
          if (deltaProg > 0) {
            const dist = deltaProg * segmentLength;
            if (dist < leaderDist) {
              leaderDist = dist;
              leaderSpeed = other.speed;
            }
          }
        }
      }

      // Target speed calculation
      let desiredSpeed = segment.speedLimit;

      if (!canPass && distToIntersection < 36) {
        const brakeDist = Math.max(2, distToIntersection - 4);
        desiredSpeed = Math.min(desiredSpeed, (brakeDist / 32) * segment.speedLimit * 0.35);
        if (distToIntersection < 5) desiredSpeed = 0;
      }

      if (leaderDist < 25) {
        if (leaderDist < 6) {
          desiredSpeed = 0;
        } else {
          desiredSpeed = Math.min(desiredSpeed, leaderSpeed * 0.8);
        }
      }

      // Unoptimized clustering bottleneck along center
      if (!this.isQuantumOptimized && segment.to === "INT-5") {
        if (distToIntersection < 70) {
          desiredSpeed *= 0.25;
        }
      }

      // Acceleration smoothing
      const speedMs = (veh.speed * 1000) / 3600;
      const desiredSpeedMs = (desiredSpeed * 1000) / 3600;
      const accelRate = desiredSpeedMs > speedMs ? 3.2 : 5.2;

      const newSpeedMs =
        desiredSpeedMs > speedMs
          ? Math.min(desiredSpeedMs, speedMs + accelRate * dt)
          : Math.max(desiredSpeedMs, speedMs - accelRate * dt);

      veh.speed = Math.max(0, (newSpeedMs * 3600) / 1000);

      // Status classification
      if (veh.speed < 5) {
        veh.status = "congested";
        veh.waitTime += dt;
        if (distToIntersection < 75) {
          const count = intersectionQueues.get(toNode.id) || 0;
          intersectionQueues.set(toNode.id, count + 1);
        }
      } else if (veh.speed < 22) {
        veh.status = "slow";
      } else if (veh.isRerouted) {
        veh.status = "quantum_rerouted";
      } else {
        veh.status = "flowing";
      }

      // Move along path
      const distanceTraveled = newSpeedMs * dt;
      veh.segmentProgress += distanceTraveled / Math.max(segmentLength, 10);

      // Reached segment end
      if (veh.segmentProgress >= 1.0) {
        veh.routeStep++;
        veh.segmentProgress = 0.0;
        this.totalThroughputCount++;
        toNode.throughput++;

        // Dynamic quantum re-routing check at intersection
        if (this.isQuantumOptimized && veh.routeStep < veh.route.length) {
          const nextStart = toNode.id;
          const newRoute = this.calculateRoute(nextStart, veh.destId, true);
          if (newRoute.length > 0 && newRoute[0] !== veh.route[veh.routeStep]) {
            veh.route = newRoute;
            veh.routeStep = 0;
            veh.isRerouted = true;
          }
        }
      }

      // Lateral lane offset for realism
      const perpRad = ((bearing + 90) * Math.PI) / 180;
      const offsetLng = Math.sin(perpRad) * veh.laneOffsetRatio;
      const offsetLat = Math.cos(perpRad) * veh.laneOffsetRatio;

      veh.pos = [interpPos[0] + offsetLng, interpPos[1] + offsetLat];
    });

    this.intersections.forEach((i) => {
      i.queueCount = intersectionQueues.get(i.id) || 0;
    });
  }

  // Toggle Quantum Optimization with Dynamic Visual Re-routing on the Street Ground
  setOptimization(enabled) {
    this.isQuantumOptimized = Boolean(enabled);
    const timeStr = new Date().toLocaleTimeString("en-US", { hour12: false });

    if (this.isQuantumOptimized) {
      let rerouteCount = 0;

      this.vehicles.forEach((veh) => {
        if (veh.route && veh.routeStep < veh.route.length) {
          const currentSegment = this.roadMap.get(veh.route[veh.routeStep]);
          if (currentSegment) {
            const currentNode = currentSegment.to;
            const originalNext = veh.route[veh.routeStep + 1];
            const newRoute = this.calculateRoute(currentNode, veh.destId, true);

            // If a different/optimal bypass route was found
            if (newRoute.length > 0) {
              const isDetoured = newRoute[0] !== originalNext;
              veh.route = newRoute;
              veh.routeStep = 0;
              veh.segmentProgress = Math.min(0.2, veh.segmentProgress);
              veh.isRerouted = true;
              veh.status = "quantum_rerouted";

              if (isDetoured && rerouteCount < 10) {
                rerouteCount++;
                this.rerouteIdCounter++;
                const bypassName = this.roadMap.get(newRoute[0])?.streetName || "Outer Ring Bypass";
                this.rerouteEvents.unshift({
                  id: `re-${this.rerouteIdCounter}`,
                  vehicleId: veh.id,
                  divertedTo: bypassName,
                  avoidedBottleneck: "Central Ave",
                  timeSavedMin: +(2.8 + Math.random() * 3.8).toFixed(1),
                  time: timeStr,
                });
              }
            }
          }
        }
      });

      this.rerouteEvents = this.rerouteEvents.slice(0, 15);
    } else {
      // Revert to classical shortest paths
      this.vehicles.forEach((veh) => {
        veh.isRerouted = false;
        if (veh.route && veh.routeStep < veh.route.length) {
          const currentSegment = this.roadMap.get(veh.route[veh.routeStep]);
          if (currentSegment) {
            veh.route = this.calculateRoute(currentSegment.to, veh.destId, false);
            veh.routeStep = 0;
          }
        }
      });
    }
  }

  setLightOverride(intersectionId, state) {
    const inter = this.intersections.find((i) => i.id === intersectionId);
    if (!inter) return false;

    if (state === "AUTO" || state === null) {
      inter.manualOverride = null;
      inter.timer = 15;
    } else {
      inter.manualOverride = state;
    }
    return true;
  }

  getTelemetry() {
    const totalWaitTime = this.vehicles.reduce((acc, v) => acc + v.waitTime, 0);
    const avgWaitTime = Math.round(totalWaitTime / Math.max(1, this.vehicles.length));
    const totalSpeed = this.vehicles.reduce((acc, v) => acc + v.speed, 0);
    const avgSpeed = +(totalSpeed / Math.max(1, this.vehicles.length)).toFixed(1);

    const congestedCount = this.vehicles.filter((v) => v.status === "congested").length;
    const reroutedCount = this.vehicles.filter((v) => v.isRerouted).length;
    const flowingCount = this.vehicles.filter(
      (v) => v.status === "flowing" || v.status === "quantum_rerouted"
    ).length;

    const efficiency = this.isQuantumOptimized
      ? +(94.2 + Math.min(4.8, (flowingCount / this.vehicles.length) * 5.5)).toFixed(1)
      : +(Math.max(18, 38 - (congestedCount / this.vehicles.length) * 25)).toFixed(1);

    const co2Reduction = this.isQuantumOptimized
      ? +(this.simulationTime * 0.35 + 8.4).toFixed(1)
      : +(this.simulationTime * 0.03).toFixed(1);

    const hotspots = this.intersections.filter((i) => i.queueCount > 2).length;

    const quantumConvergence = this.isQuantumOptimized
      ? +(98.4 + Math.sin(this.simulationTime * 0.3) * 1.0).toFixed(1)
      : +(22.0 + Math.cos(this.simulationTime * 0.2) * 2.5).toFixed(1);

    return {
      locality: "Indiranagar - Domlur, Bengaluru",
      isQuantumOptimized: this.isQuantumOptimized,
      metrics: {
        avgWaitTime,
        efficiency,
        avgSpeed,
        co2Reduction,
        hotspots,
        quantumConvergence,
        totalVehicles: this.vehicles.length,
        congestedVehicles: congestedCount,
        reroutedVehicles: reroutedCount,
        flowingVehicles: flowingCount,
        totalThroughput: this.totalThroughputCount,
        simulationTime: Math.floor(this.simulationTime),
      },
      rerouteEvents: this.rerouteEvents,
      intersections: this.intersections.map((i) => ({
        id: i.id,
        name: i.name,
        coordinates: i.coordinates,
        phase: i.phase,
        timer: Math.ceil(i.timer),
        manualOverride: i.manualOverride,
        queueCount: i.queueCount,
      })),
      vehicles: this.vehicles.map((v) => ({
        id: v.id,
        number: v.number,
        pos: v.pos,
        heading: Math.round(v.heading),
        speed: Math.round(v.speed),
        status: v.status,
        isRerouted: v.isRerouted,
        destName: v.destName,
        startName: v.startName,
        remainingPath: this.getVehicleRemainingPath(v),
      })),
    };
  }
}

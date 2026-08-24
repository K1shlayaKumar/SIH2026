// Bangalore Locality: Small Dense Grid (Indiranagar 100ft Rd Core)
// Realistic GPS coordinates but packed into a 600m x 600m dense 3x3 grid

export const CITY_CENTER = [77.6412, 12.9715]; // [longitude, latitude] - Indiranagar 100ft Rd & 12th Main

export const INTERSECTIONS = [
  { id: "INT-1", name: "NW Cross", coordinates: [77.6385, 12.9740], connectedTo: ["INT-2", "INT-4"], cycleLength: 36, baseSplit: 0.5 },
  { id: "INT-2", name: "North Main", coordinates: [77.6412, 12.9740], connectedTo: ["INT-1", "INT-3", "INT-5"], cycleLength: 40, baseSplit: 0.5 },
  { id: "INT-3", name: "NE Cross", coordinates: [77.6440, 12.9740], connectedTo: ["INT-2", "INT-6"], cycleLength: 36, baseSplit: 0.5 },
  
  { id: "INT-4", name: "West Main", coordinates: [77.6385, 12.9715], connectedTo: ["INT-1", "INT-5", "INT-7"], cycleLength: 40, baseSplit: 0.5 },
  { id: "INT-5", name: "City Center (Bottleneck)", coordinates: [77.6412, 12.9715], connectedTo: ["INT-2", "INT-4", "INT-6", "INT-8"], cycleLength: 50, baseSplit: 0.5 },
  { id: "INT-6", name: "East Main", coordinates: [77.6440, 12.9715], connectedTo: ["INT-3", "INT-5", "INT-9"], cycleLength: 40, baseSplit: 0.5 },
  
  { id: "INT-7", name: "SW Cross", coordinates: [77.6385, 12.9690], connectedTo: ["INT-4", "INT-8"], cycleLength: 36, baseSplit: 0.5 },
  { id: "INT-8", name: "South Main", coordinates: [77.6412, 12.9690], connectedTo: ["INT-7", "INT-5", "INT-9"], cycleLength: 40, baseSplit: 0.5 },
  { id: "INT-9", name: "SE Cross", coordinates: [77.6440, 12.9690], connectedTo: ["INT-8", "INT-6"], cycleLength: 36, baseSplit: 0.5 },
];

// In a tight grid, we don't need complex curved waypoints, straight lines are fine
const ROAD_WAYPOINTS = {};

// Road Network Builder
export function buildRoadNetwork() {
  const nodeMap = new Map();
  INTERSECTIONS.forEach((node) => nodeMap.set(node.id, node));

  const roadSegments = [];
  const added = new Set();

  INTERSECTIONS.forEach((nodeA) => {
    nodeA.connectedTo.forEach((nodeBId) => {
      const nodeB = nodeMap.get(nodeBId);
      if (!nodeB) return;

      const keyForward = `${nodeA.id}->${nodeB.id}`;
      const keyReverse = `${nodeB.id}->${nodeA.id}`;

      let waypoints = [nodeA.coordinates, nodeB.coordinates];
      let waypointsRev = [nodeB.coordinates, nodeA.coordinates];

      // Make roads connected to INT-5 the bottleneck
      const isBottleneckCorridor = nodeA.id === "INT-5" || nodeB.id === "INT-5";
      
      // Outer ring as bypass
      const isQuantumBypass = !isBottleneckCorridor;

      if (!added.has(keyForward)) {
        roadSegments.push({
          id: keyForward,
          from: nodeA.id,
          to: nodeB.id,
          fromCoord: nodeA.coordinates,
          toCoord: nodeB.coordinates,
          path: waypoints,
          lanes: 2,
          speedLimit: 40, // km/h
          isBottleneck: isBottleneckCorridor,
          isBypass: isQuantumBypass,
          streetName: getStreetName(nodeA.id, nodeB.id),
        });
        added.add(keyForward);
      }

      if (!added.has(keyReverse)) {
        roadSegments.push({
          id: keyReverse,
          from: nodeB.id,
          to: nodeA.id,
          fromCoord: nodeB.coordinates,
          toCoord: nodeA.coordinates,
          path: waypointsRev,
          lanes: 2,
          speedLimit: 40,
          isBottleneck: isBottleneckCorridor,
          isBypass: isQuantumBypass,
          streetName: getStreetName(nodeB.id, nodeA.id),
        });
        added.add(keyReverse);
      }
    });
  });

  return { intersections: INTERSECTIONS, roadSegments };
}

function getStreetName(fromId, toId) {
  const isCenter = fromId === "INT-5" || toId === "INT-5";
  if (isCenter) return "Central Ave";
  return "Outer Ring Bypass";
}

// Distance helper in meters between two lat/lng pairs
export function getDistanceMeters(coordA, coordB) {
  const [lon1, lat1] = coordA;
  const [lon2, lat2] = coordB;
  const R = 6371e3;
  const phi1 = (lat1 * Math.PI) / 180;
  const phi2 = (lat2 * Math.PI) / 180;
  const deltaPhi = ((lat2 - lat1) * Math.PI) / 180;
  const deltaLambda = ((lon2 - lon1) * Math.PI) / 180;

  const a =
    Math.sin(deltaPhi / 2) * Math.sin(deltaPhi / 2) +
    Math.cos(phi1) * Math.cos(phi2) * Math.sin(deltaLambda / 2) * Math.sin(deltaLambda / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

  return R * c;
}

export function getPathLengthMeters(path = []) {
  if (!path || path.length < 2) return 10;
  let total = 0;
  for (let i = 0; i < path.length - 1; i++) {
    total += getDistanceMeters(path[i], path[i + 1]);
  }
  return Math.max(total, 10);
}

export function interpolatePath(path = [], progress = 0) {
  if (!path || path.length === 0) return { pos: [77.6412, 12.9715], bearing: 0 };
  if (path.length === 1) return { pos: path[0], bearing: 0 };

  const clampedProgress = Math.max(0, Math.min(1, progress));
  const totalDist = getPathLengthMeters(path);
  const targetDist = clampedProgress * totalDist;

  let accumulatedDist = 0;
  for (let i = 0; i < path.length - 1; i++) {
    const segDist = getDistanceMeters(path[i], path[i + 1]);
    if (accumulatedDist + segDist >= targetDist || i === path.length - 2) {
      const subT = segDist > 0 ? (targetDist - accumulatedDist) / segDist : 0;
      const subProgress = Math.max(0, Math.min(1, subT));

      const lng = path[i][0] + (path[i + 1][0] - path[i][0]) * subProgress;
      const lat = path[i][1] + (path[i + 1][1] - path[i][1]) * subProgress;
      const bearing = getBearing(path[i], path[i + 1]);

      return { pos: [lng, lat], bearing };
    }
    accumulatedDist += segDist;
  }

  return { pos: path[path.length - 1], bearing: 0 };
}

export function getBearing(coordA, coordB) {
  const [lon1, lat1] = coordA;
  const [lon2, lat2] = coordB;
  const y = Math.sin(((lon2 - lon1) * Math.PI) / 180) * Math.cos((lat2 * Math.PI) / 180);
  const x =
    Math.cos((lat1 * Math.PI) / 180) * Math.sin((lat2 * Math.PI) / 180) -
    Math.sin((lat1 * Math.PI) / 180) * Math.cos((lat2 * Math.PI) / 180) * Math.cos(((lon2 - lon1) * Math.PI) / 180);
  const bearing = (Math.atan2(y, x) * 180) / Math.PI;
  return (bearing + 360) % 360;
}

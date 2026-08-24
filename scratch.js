function getDistanceMeters(coordA, coordB) {
  const [lon1, lat1] = coordA;
  const [lon2, lat2] = coordB;
  const R = 6371e3;
  const phi1 = (lat1 * Math.PI) / 180;
  const phi2 = (lat2 * Math.PI) / 180;
  const deltaPhi = ((lat2 - lat1) * Math.PI) / 180;
  const deltaLambda = ((lon2 - lon1) * Math.PI) / 180;
  const a = Math.sin(deltaPhi / 2) * Math.sin(deltaPhi / 2) +
            Math.cos(phi1) * Math.cos(phi2) * Math.sin(deltaLambda / 2) * Math.sin(deltaLambda / 2);
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}
console.log(getDistanceMeters([77.6412, 12.9715], [77.6440, 12.9715])); // East
console.log(getDistanceMeters([77.6412, 12.9715], [77.6413, 12.9740])); // North

// gis/maps/mapUtils.js

import { riskColors } from "./riskColors";

export function getRiskColor(riskCategory) {
  if (typeof riskCategory === "number") {
    if (riskCategory >= 80) return riskColors.critical;
    if (riskCategory >= 60) return riskColors.high;
    if (riskCategory >= 30) return riskColors.medium;
    return riskColors.low;
  }
  const category = riskCategory?.toLowerCase();

  return riskColors[category] || "#6b7280";
}

export function getRiskLabel(probability) {
  if (probability < 30) {
    return "Low";
  } else if (probability < 60) {
    return "Medium";
  } else if (probability < 80) {
    return "High";
  } else {
    return "Critical";
  }
}

function getOuterRings(geometry) {
  if (!geometry) return [];
  if (geometry.type === 'Polygon') return geometry.coordinates.length ? [geometry.coordinates[0]] : [];
  if (geometry.type === 'MultiPolygon') return geometry.coordinates.map((polygon) => polygon[0]).filter(Boolean);
  return [];
}

export function createOutsideIndiaMask(geojson) {
  const indiaRings = (geojson?.features || [])
    .flatMap((feature) => getOuterRings(feature.geometry))
    .map((ring) => ring.map(([longitude, latitude]) => [latitude, longitude]));

  const worldRing = [[85, -180], [85, 180], [-85, 180], [-85, -180]];
  return [worldRing, ...indiaRings];
}

export function getProjectProbability(project) {
  const value = Number(project?.delay_probability ?? project?.delayProbability ?? project?.delay_percentage / 100);
  return Number.isFinite(value) ? Math.max(0, Math.min(1, value)) : null;
}

export function getProjectRiskCategory(project) {
  const category = String(project?.risk_category || '').toUpperCase();
  if (['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'].includes(category)) return category;
  const probability = getProjectProbability(project);
  return getRiskLabel((probability === null ? 0 : probability) * 100).toUpperCase();
}

export function getRiskPercentage(project) {
  const probability = getProjectProbability(project);
  return probability === null ? 'N/A' : `${(probability * 100).toFixed(2)}%`;
}
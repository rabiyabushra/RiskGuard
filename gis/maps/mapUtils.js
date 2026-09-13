// gis/maps/mapUtils.js

import { riskColors } from "./riskColors";

export function getRiskColor(riskCategory) {
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
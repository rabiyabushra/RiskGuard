import { riskColors } from '@gis/maps/riskColors';
import { getRiskColor as getMapRiskColor } from '@gis/maps/mapUtils';

export { riskColors, getMapRiskColor };

export function formatCurrency(value) {
  if (value === null || value === undefined || isNaN(value)) return '₹ 0.00 Cr';
  return `₹ ${Number(value).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} Cr`;
}

export function formatPercent(value) {
  if (value === null || value === undefined || isNaN(value)) return '0.0%';
  return `${Number(value).toFixed(1)}%`;
}

export function formatNumber(value) {
  if (value === null || value === undefined || isNaN(value)) return '0';
  return Number(value).toLocaleString('en-IN');
}

export function getRiskBadgeClasses(category) {
  const cat = String(category || '').toUpperCase();
  switch (cat) {
    case 'HIGH':
      return 'bg-amber-500/20 text-amber-400 border border-amber-500/40';
    case 'CRITICAL':
      return 'bg-red-500/20 text-red-400 border border-red-500/40';
    case 'MEDIUM':
      return 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/40';
    case 'LOW':
      return 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40';
    default:
      return 'bg-slate-700 text-slate-300 border border-slate-600';
  }
}

// Approximate State Centroids for map markers when district GPS is omitted in master data
export const STATE_CENTROIDS = {
  "Andhra Pradesh": [15.9129, 79.7400],
  "Arunachal Pradesh": [28.2180, 94.7278],
  "Assam": [26.2006, 92.9376],
  "Bihar": [25.0961, 85.3131],
  "Chhattisgarh": [21.2787, 81.8661],
  "Goa": [15.2993, 74.1240],
  "Gujarat": [22.2587, 71.1924],
  "Haryana": [29.0588, 76.0856],
  "Himachal Pradesh": [31.1048, 77.1734],
  "Jharkhand": [23.6102, 85.2799],
  "Karnataka": [15.3173, 75.7139],
  "Kerala": [10.8505, 76.2711],
  "Madhya Pradesh": [22.9734, 78.6569],
  "Maharashtra": [19.7515, 75.7139],
  "Manipur": [24.6637, 93.9063],
  "Meghalaya": [25.4670, 91.3662],
  "Mizoram": [23.1645, 92.9376],
  "Nagaland": [26.1584, 94.5624],
  "Odisha": [20.9517, 85.0985],
  "Punjab": [31.1471, 75.3412],
  "Rajasthan": [27.0238, 74.2179],
  "Sikkim": [27.5330, 88.5122],
  "Tamil Nadu": [11.1271, 78.6569],
  "Telangana": [18.1124, 79.0193],
  "Tripura": [23.9408, 91.9882],
  "Uttar Pradesh": [26.8467, 80.9462],
  "Uttarakhand": [30.0668, 79.0193],
  "West Bengal": [22.9868, 87.8550],
  "Delhi": [28.7041, 77.1025],
  "Jammu & Kashmir": [33.7782, 76.5762],
  "Ladakh": [34.1526, 77.5771],
  "Puducherry": [11.9416, 79.8083],
  "Chandigarh": [30.7333, 76.7794],
  "Andaman & Nicobar": [11.7401, 92.6586],
  "Andaman and Nicobar Islands": [11.7401, 92.6586],
  "Dadra & Nagar Haveli And Daman & Diu": [20.4283, 72.8397],
};

export function normalizeStateName(stateName) {
  if (!stateName) return '';
  const clean = stateName.trim();
  if (clean === 'Andaman & Nicobar') return 'Andaman and Nicobar Islands';
  if (clean.includes('Daman') || clean.includes('Diu') || clean.includes('Dadra')) return 'Daman and Diu';
  if (clean === 'Jammu & Kashmir') return 'Jammu & Kashmir';
  return clean;
}

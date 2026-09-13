// gis/maps/mapConfig.js

// Default map configuration for RiskGuard
export const mapConfig = {
  center: [20.5937, 78.9629], // Center of India
  zoom: 5,

  minZoom: 4,
  maxZoom: 18,

  scrollWheelZoom: true,
  zoomControl: true,

  attribution:
    '&copy; OpenStreetMap contributors'
};

// OpenStreetMap tile configuration
export const tileConfig = {
  url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',

  attribution:
    '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',

  maxZoom: 19
};
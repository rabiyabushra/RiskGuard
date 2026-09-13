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

// Public dark basemap configuration; no frontend API key is required.
export const tileConfig = {
  url: 'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}',

  attribution:
    'Tiles &copy; <a href="https://www.esri.com/">Esri</a> &mdash; Data &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',

  maxZoom: 19
};
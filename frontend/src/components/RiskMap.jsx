import React, { useState, useMemo, useRef } from 'react';
import { MapContainer, TileLayer, GeoJSON, Marker, Popup, Polygon, Pane, Tooltip, useMap } from 'react-leaflet';
import L from 'leaflet';
import { Link } from 'react-router-dom';
import { ExternalLink, Filter, RotateCcw, Layers } from 'lucide-react';

import { mapConfig, tileConfig } from '@gis/maps/mapConfig';
import { riskColors } from '@gis/maps/riskColors';
import { createOutsideIndiaMask, getRiskColor, getProjectProbability, getProjectRiskCategory, getRiskPercentage } from '@gis/maps/mapUtils';
import indiaGeoData from '@gis/geojson/india.json';
import statesGeoData from '@gis/geojson/states.json';
import districtsGeoData from '@gis/geojson/districts.json';

import { STATE_CENTROIDS, normalizeStateName, formatCurrency } from '../utils/riskUtils';
import MapLegend from './MapLegend';
import RiskBadge from './RiskBadge';

// Helper component to programmatic flyTo when state selection changes
const indiaBounds = L.geoJSON(indiaGeoData).getBounds();
const indiaMaxBounds = indiaBounds.pad(0.2);

function getStateBounds(stateName) {
  const normalizedName = canonicalStateName(stateName);
  const features = indiaGeoData.features.filter((feature) => {
    const featureName = feature.properties?.st_nm || feature.properties?.ST_NM || '';
    return canonicalStateName(featureName) === normalizedName;
  });
  return features.length ? L.geoJSON({ type: 'FeatureCollection', features }).getBounds() : null;
}

function canonicalStateName(stateName) {
  return normalizeStateName(stateName).toLowerCase().replace(/&/g, 'and').replace(/[^a-z0-9]/g, '');
}

function MapController({ center, zoom, selectedState, indiaLayerRef }) {
  const map = useMap();
  const lastView = React.useRef(null);
  React.useEffect(() => {
    const viewKey = selectedState || 'INDIA';
    if (lastView.current === viewKey || !indiaLayerRef.current) return;

    if (selectedState) {
      const stateBounds = getStateBounds(selectedState);
      if (stateBounds?.isValid()) {
        map.fitBounds(stateBounds, { padding: [24, 24], maxZoom: zoom });
      } else if (center) {
        map.flyTo(center, zoom, { duration: 1.2 });
      }
    } else {
      const bounds = indiaLayerRef.current.getBounds();
      if (!bounds.isValid()) return;
      map.fitBounds(bounds, { padding: [30, 30] });
      map.setMaxBounds(bounds.pad(0.2));
    }
    lastView.current = viewKey;
  }, [center, zoom, map, selectedState, indiaLayerRef]);
  return null;
}

function ZoomTracker({ onZoomChange }) {
  const map = useMap();
  React.useEffect(() => {
    const updateZoom = () => onZoomChange(map.getZoom());
    updateZoom();
    map.on('zoomend', updateZoom);
    return () => map.off('zoomend', updateZoom);
  }, [map, onZoomChange]);
  return null;
}

// Create custom SVG Leaflet divIcon for project markers
function createCustomPin(riskCategory) {
  const cat = String(riskCategory || 'MEDIUM').toLowerCase();
  const color = riskColors[cat] || riskColors.medium;
  const isCritical = cat === 'critical';
  const size = cat === 'critical' ? 18 : cat === 'high' ? 16 : cat === 'medium' ? 14 : 12;

  return L.divIcon({
    className: 'custom-map-pin',
    html: `
      <div style="position: relative; display: flex; align-items: center; justify-content: center;">
        ${isCritical ? `<div style="position: absolute; width: ${size + 8}px; height: ${size + 8}px; border-radius: 9999px; background-color: ${color}; opacity: 0.28;"></div>` : ''}
        <div style="width: ${size}px; height: ${size}px; border-radius: 9999px; background-color: ${color}; border: 1.5px solid #f8fafc; box-shadow: 0 0 ${isCritical ? 10 : 6}px ${color}; display: flex; align-items: center; justify-content: center;">
        </div>
      </div>
    `,
    iconSize: [24, 24],
    iconAnchor: [12, 12],
    popupAnchor: [0, -12],
  });
}

export default function RiskMap({
  projects = [],
  selectedState = '',
  onStateSelect = null,
  height = '560px',
  showControls = true,
  showLegend = true
}) {
  const [filterRisk, setFilterRisk] = useState('ALL');
  const [showChoropleth, setShowChoropleth] = useState(true);
  const [showMarkers, setShowMarkers] = useState(true);
  const [mapCenter, setMapCenter] = useState(mapConfig.center);
  const [mapZoom, setMapZoom] = useState(mapConfig.zoom);
  const [currentZoom, setCurrentZoom] = useState(mapConfig.zoom);
  const indiaLayerRef = useRef(null);
  const outsideIndiaMask = useMemo(() => createOutsideIndiaMask(indiaGeoData), []);

  // 1. Calculate state-level risk aggregations from actual project data
  const stateStats = useMemo(() => {
    const stats = {};
    projects.forEach((p) => {
      const stateName = normalizeStateName(p.state_std || p.state || 'Unknown');
      if (!stats[stateName]) {
        stats[stateName] = {
          total: 0,
          highRisk: 0,
          mediumRisk: 0,
          lowRisk: 0,
          totalScore: 0,
          projects: [],
        };
      }
      stats[stateName].total += 1;
      const probability = getProjectProbability(p);
      stats[stateName].totalScore += probability === null ? Number(p.risk_score || 50) : probability * 100;
      const cat = getProjectRiskCategory(p);
      if (cat === 'HIGH' || cat === 'CRITICAL') stats[stateName].highRisk += 1;
      else if (cat === 'LOW') stats[stateName].lowRisk += 1;
      else stats[stateName].mediumRisk += 1;

      stats[stateName].projects.push(p);
    });

    Object.keys(stats).forEach((k) => {
      stats[k].avgRisk = stats[k].total > 0 ? stats[k].totalScore / stats[k].total : 0;
    });

    return stats;
  }, [projects]);

  // 2. Filter projects for markers based on risk level and selected state
  const filteredProjects = useMemo(() => {
    return projects.filter((p) => {
      const matchesState = !selectedState || canonicalStateName(p.state_std || p.state) === canonicalStateName(selectedState);
      const cat = getProjectRiskCategory(p);
      const matchesRisk = filterRisk === 'ALL' || cat === filterRisk;
      return matchesState && matchesRisk;
    });
  }, [projects, selectedState, filterRisk]);

  // 3. Position markers based on real available state coordinates with deterministic dispersion
  const markerPositions = useMemo(() => {
    const positions = [];
    const stateCounts = {};

    filteredProjects.forEach((p, idx) => {
      const stateName = normalizeStateName(p.state_std || p.state);
      const centroid = STATE_CENTROIDS[stateName] || STATE_CENTROIDS[p.state] || null;

      if (centroid) {
        if (!stateCounts[stateName]) stateCounts[stateName] = 0;
        const count = stateCounts[stateName]++;

        // Deterministic radial jitter around centroid so multiple projects in same state don't fully overlap
        const angle = (count * 137.5 * Math.PI) / 180; // golden angle
        const radius = count === 0 ? 0 : 0.15 + (count % 8) * 0.12;
        const lat = centroid[0] + radius * Math.cos(angle);
        const lng = centroid[1] + radius * Math.sin(angle);

        positions.push({
          project: p,
          position: [lat, lng],
        });
      }
    });

    return positions;
  }, [filteredProjects]);

  // 4. Handle State Polygon Styling (Choropleth based on average risk)
  const getFeatureStyle = (feature) => {
    const stName = normalizeStateName(feature.properties?.st_nm || feature.properties?.ST_NM || '');
    const data = Object.entries(stateStats).find(([name]) => canonicalStateName(name) === canonicalStateName(stName))?.[1];

    let fillColor = '#334155'; // default slate if no projects
    let fillOpacity = 0.25;

    if (data && data.total > 0) {
      fillColor = getRiskColor(data.avgRisk);
      fillOpacity = data.avgRisk >= 80 ? 0.70 : 0.65;
    }

    if (selectedState && canonicalStateName(selectedState) === canonicalStateName(stName)) {
      fillOpacity = 0.75;
      return {
        fillColor,
        weight: 3,
        opacity: 1,
        color: '#38bdf8', // bright sky border for active selection
        fillOpacity,
      };
    }

    return {
      fillColor,
      weight: 1,
      opacity: 0.95,
      color: '#94a3b8',
      fillOpacity: showChoropleth ? fillOpacity : 0.1,
    };
  };

  const onEachFeature = (feature, layer) => {
    const stName = normalizeStateName(feature.properties?.st_nm || feature.properties?.ST_NM || '');
    const data = Object.entries(stateStats).find(([name]) => canonicalStateName(name) === canonicalStateName(stName))?.[1];

    if (data && data.total > 0) {
      layer.bindTooltip(
        `
        <div style="font-family: Inter, sans-serif; font-size: 11px;">
          <strong style="color: #f8fafc; font-size: 12px;">${stName}</strong><br/>
          <span style="color: #94a3b8;">Total Projects:</span> <b>${data.total}</b><br/>
          <span style="color: #f97316;">High Risk:</span> <b>${data.highRisk}</b><br/>
          <span style="color: #38bdf8;">Avg Risk Score:</span> <b>${data.avgRisk.toFixed(1)} / 100</b>
        </div>
      `,
        { sticky: true, className: 'leaflet-tooltip-dark' }
      );
    } else {
      layer.bindTooltip(`<strong>${stName}</strong><br/><span style="color:#94a3b8;">No tracked projects</span>`, { sticky: true });
    }
    const riskLevel = data ? (data.avgRisk >= 80 ? 'CRITICAL' : data.avgRisk >= 60 ? 'HIGH' : data.avgRisk >= 30 ? 'MEDIUM' : 'LOW') : 'N/A';
    layer.bindPopup(data
      ? `<strong>Region: ${stName}</strong><br/>Risk Score: ${data.avgRisk.toFixed(1)} / 100<br/>Risk Level: ${riskLevel}<br/>Projects: ${data.total}<br/>High Risk Projects: ${data.highRisk}`
      : `<strong>Region: ${stName}</strong><br/>No tracked project risk data`);

    layer.on({
      click: () => {
        if (onStateSelect) {
          onStateSelect(stName === selectedState ? '' : stName);
        }
        const centroid = STATE_CENTROIDS[stName];
        if (centroid) {
          setMapCenter(centroid);
          setMapZoom(7);
        }
      },
      mouseover: (e) => {
        const l = e.target;
        l.setStyle({ weight: 2.5, color: '#f8fafc', fillOpacity: 0.65 });
      },
      mouseout: (e) => {
        const l = e.target;
        l.setStyle(getFeatureStyle(feature));
      },
    });
  };

  const handleResetView = () => {
    setMapCenter(mapConfig.center);
    setMapZoom(mapConfig.zoom);
    if (onStateSelect) onStateSelect('');
    setFilterRisk('ALL');
  };

  const uniqueStates = Object.keys(stateStats).sort();
  const showDistricts = showChoropleth && currentZoom >= 7;

  return (
    <div className="relative rounded-xl overflow-hidden border border-slate-800 shadow-2xl bg-slate-950" style={{ height }}>
      {/* Map Header / Controls Toolbar */}
      {showControls && (
        <div className="absolute top-3 left-3 z-[1000] flex flex-wrap items-center gap-2 bg-slate-900/90 backdrop-blur-md p-2 rounded-xl border border-slate-700/80 shadow-xl text-xs">
          {/* State Filter */}
          <div className="flex items-center space-x-1.5 pl-1">
            <Filter className="w-3.5 h-3.5 text-sky-400" />
            <select
              value={selectedState}
              onChange={(e) => {
                const st = e.target.value;
                if (onStateSelect) onStateSelect(st);
                if (st && STATE_CENTROIDS[st]) {
                  setMapCenter(STATE_CENTROIDS[st]);
                  setMapZoom(7);
                } else {
                  setMapCenter(mapConfig.center);
                  setMapZoom(mapConfig.zoom);
                }
              }}
              className="bg-slate-800 border border-slate-700 text-slate-200 rounded-lg px-2.5 py-1 text-xs focus:outline-none focus:border-sky-500"
            >
              <option value="">All States ({projects.length} Projects)</option>
              {uniqueStates.map((st) => (
                <option key={st} value={st}>
                  {st} ({stateStats[st]?.total})
                </option>
              ))}
            </select>
          </div>

          {/* Risk Filter */}
          <div className="flex items-center space-x-1 bg-slate-800/80 p-0.5 rounded-lg border border-slate-700">
            {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map((lvl) => (
              <button
                key={lvl}
                onClick={() => setFilterRisk(lvl)}
                className={`px-2 py-0.5 rounded text-[11px] font-medium transition-colors ${
                  filterRisk === lvl ? 'bg-sky-500 text-white shadow-sm' : 'text-slate-400 hover:text-white'
                }`}
              >
                {lvl}
              </button>
            ))}
          </div>

          {/* Layer Toggles */}
          <button
            onClick={() => setShowChoropleth(!showChoropleth)}
            className={`px-2 py-1 rounded text-[11px] font-medium border transition-colors flex items-center space-x-1 ${
              showChoropleth
                ? 'bg-slate-800 text-sky-400 border-sky-500/30'
                : 'bg-slate-900 text-slate-400 border-slate-700'
            }`}
          >
            <Layers className="w-3 h-3" />
            <span>{showChoropleth ? 'Boundaries: ON' : 'Boundaries: OFF'}</span>
          </button>

          {/* Reset View */}
          <button
            onClick={handleResetView}
            title="Reset Map View"
            className="p-1 rounded bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 transition-colors"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Floating Map Legend */}
      {showLegend && (
        <div className="absolute bottom-4 right-4 z-[1000]">
          <MapLegend />
        </div>
      )}

      {/* Primary Leaflet Map Container */}
      <MapContainer
        center={mapConfig.center}
        zoom={mapConfig.zoom}
        minZoom={mapConfig.minZoom}
        maxZoom={mapConfig.maxZoom}
        maxBounds={indiaMaxBounds}
        maxBoundsViscosity={0.85}
        scrollWheelZoom={mapConfig.scrollWheelZoom}
        zoomControl={mapConfig.zoomControl}
        style={{ height: '100%', width: '100%' }}
      >
        <MapController center={mapCenter} zoom={mapZoom} selectedState={selectedState} indiaLayerRef={indiaLayerRef} />
        <ZoomTracker onZoomChange={setCurrentZoom} />

        {/* OpenStreetMap Tiles */}
        <TileLayer
          url={tileConfig.url}
          attribution={tileConfig.attribution}
          maxZoom={tileConfig.maxZoom}
        />

        <Pane name="outsideIndiaMask" style={{ zIndex: 300 }}>
          <Polygon
            positions={outsideIndiaMask}
            pathOptions={{ color: '#020617', weight: 0, fillColor: '#020617', fillOpacity: 0.9, fillRule: 'evenodd' }}
          />
        </Pane>

        {/* State Boundary GeoJSON Choropleth */}
        {showChoropleth && (
          <GeoJSON
            ref={indiaLayerRef}
            key={`geojson-states-${selectedState}-${showChoropleth}`}
            data={indiaGeoData}
            style={getFeatureStyle}
            onEachFeature={onEachFeature}
          />
        )}

        {showDistricts && (
          <GeoJSON
            key={`geojson-districts-${selectedState}-${showDistricts}`}
            data={districtsGeoData}
            style={{ color: '#475569', weight: 0.6, opacity: 0.72, fillOpacity: 0 }}
            onEachFeature={(feature, layer) => {
              const districtName = feature.properties?.district || feature.properties?.DISTRICT || 'District';
              layer.bindPopup(`<strong>District</strong><br/>${districtName}`);
            }}
          />
        )}

        {/* Interactive Project Markers */}
        {showMarkers && (
          markerPositions.slice(0, 150).map(({ project, position }, idx) => {
            const cat = getProjectRiskCategory(project);
            const riskPercentage = getRiskPercentage(project);
            return (
              <Marker
                key={`marker-${project.project_id}-${idx}`}
                position={position}
                icon={createCustomPin(cat)}
              >
                <Tooltip direction="top" offset={[0, -8]}>
                  <span>{project.project_name || 'Unnamed project'}<br />{riskPercentage} • {cat}</span>
                </Tooltip>
                <Popup>
                  <div className="p-3.5 max-w-xs space-y-2 text-slate-100">
                    <div className="flex items-center justify-between border-b border-slate-700/80 pb-2">
                      <span className="font-mono text-[11px] text-slate-400">ID: {project.project_id}</span>
                      <RiskBadge category={cat} score={project.risk_score} size="sm" />
                    </div>

                    <div>
                      <h4 className="font-semibold text-xs text-white line-clamp-2 leading-tight">
                        {project.project_name}
                      </h4>
                      <p className="text-[11px] text-slate-400 mt-1">
                        Sector: <span className="text-slate-200 font-medium">{project.sector}</span>
                      </p>
                      <p className="text-[11px] text-slate-400">
                        State: <span className="text-slate-200 font-medium">{project.state}</span>
                      </p>
                    </div>

                    <div className="grid grid-cols-2 gap-2 bg-slate-900/60 p-2 rounded-lg border border-slate-800 text-[11px]">
                      <div>
                        <span className="text-slate-400 block text-[10px]">Delay Prob:</span>
                        <span className="font-mono font-bold text-sky-400">
                          {riskPercentage}
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-400 block text-[10px]">Physical Prog:</span>
                        <span className="font-mono font-bold text-emerald-400">
                          {Number(project.physical_progress || 0).toFixed(1)}%
                        </span>
                      </div>
                    </div>

                    <Link
                      to={`/projects/${project.project_id}`}
                      className="mt-2 w-full inline-flex items-center justify-center space-x-1 py-1.5 px-3 bg-sky-600 hover:bg-sky-500 text-white rounded-lg text-xs font-medium transition-colors"
                    >
                      <span>View Full Project Dossier</span>
                      <ExternalLink className="w-3 h-3" />
                    </Link>
                  </div>
                </Popup>
              </Marker>
            );
          })
        )}
      </MapContainer>
    </div>
  );
}

import React, { useState, useMemo, useRef } from 'react';
import { MapContainer, TileLayer, GeoJSON, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import { Link } from 'react-router-dom';
import { ExternalLink, Filter, RotateCcw, Layers } from 'lucide-react';

import { mapConfig, tileConfig } from '@gis/maps/mapConfig';
import { riskColors } from '@gis/maps/riskColors';
import { getRiskColor } from '@gis/maps/mapUtils';
import indiaGeoData from '@gis/geojson/india.json';
import statesGeoData from '@gis/geojson/states.json';

import { STATE_CENTROIDS, normalizeStateName, formatCurrency } from '../utils/riskUtils';
import MapLegend from './MapLegend';
import RiskBadge from './RiskBadge';

// Helper component to programmatic flyTo when state selection changes
function MapController({ center, zoom }) {
  const map = useMap();
  React.useEffect(() => {
    if (center) {
      map.flyTo(center, zoom, { duration: 1.2 });
    }
  }, [center, zoom, map]);
  return null;
}

// Create custom SVG Leaflet divIcon for project markers
function createCustomPin(riskCategory, count = 1) {
  const cat = String(riskCategory || 'MEDIUM').toLowerCase();
  const color = riskColors[cat] || riskColors.medium;
  const isHigh = cat === 'high' || cat === 'critical';

  return L.divIcon({
    className: 'custom-map-pin',
    html: `
      <div style="position: relative; display: flex; align-items: center; justify-content: center;">
        ${isHigh ? `<div style="position: absolute; width: 26px; height: 26px; border-radius: 9999px; background-color: ${color}; opacity: 0.4; animation: ping 1.5s cubic-bezier(0, 0, 0.2, 1) infinite;"></div>` : ''}
        <div style="width: 18px; height: 18px; border-radius: 9999px; background-color: ${color}; border: 2px solid #ffffff; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.5); display: flex; align-items: center; justify-content: center;">
          ${count > 1 ? `<span style="font-size: 9px; font-weight: 700; color: #ffffff;">${count}</span>` : ''}
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
  showControls = true
}) {
  const [filterRisk, setFilterRisk] = useState('ALL');
  const [showChoropleth, setShowChoropleth] = useState(true);
  const [showMarkers, setShowMarkers] = useState(true);
  const [mapCenter, setMapCenter] = useState(mapConfig.center);
  const [mapZoom, setMapZoom] = useState(mapConfig.zoom);

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
      stats[stateName].totalScore += Number(p.risk_score || 50);
      const cat = (p.risk_category || '').toUpperCase();
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
      const matchesState = !selectedState || normalizeStateName(p.state_std || p.state) === normalizeStateName(selectedState);
      const cat = (p.risk_category || '').toUpperCase();
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
    const data = stateStats[stName];

    let fillColor = '#334155'; // default slate if no projects
    let fillOpacity = 0.25;

    if (data && data.total > 0) {
      if (data.avgRisk >= 65) fillColor = riskColors.high;
      else if (data.avgRisk >= 35) fillColor = riskColors.medium;
      else fillColor = riskColors.low;
      fillOpacity = 0.45;
    }

    if (selectedState && normalizeStateName(selectedState) === stName) {
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
      weight: 1.2,
      opacity: 0.8,
      color: '#475569',
      fillOpacity: showChoropleth ? fillOpacity : 0.1,
    };
  };

  const onEachFeature = (feature, layer) => {
    const stName = normalizeStateName(feature.properties?.st_nm || feature.properties?.ST_NM || '');
    const data = stateStats[stName];

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
            {['ALL', 'HIGH', 'MEDIUM', 'LOW'].map((lvl) => (
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
      <div className="absolute bottom-4 right-4 z-[1000]">
        <MapLegend />
      </div>

      {/* Primary Leaflet Map Container */}
      <MapContainer
        center={mapConfig.center}
        zoom={mapConfig.zoom}
        minZoom={mapConfig.minZoom}
        maxZoom={mapConfig.maxZoom}
        scrollWheelZoom={mapConfig.scrollWheelZoom}
        zoomControl={mapConfig.zoomControl}
        style={{ height: '100%', width: '100%' }}
      >
        <MapController center={mapCenter} zoom={mapZoom} />

        {/* OpenStreetMap Tiles */}
        <TileLayer
          url={tileConfig.url}
          attribution={tileConfig.attribution}
          maxZoom={tileConfig.maxZoom}
        />

        {/* State Boundary GeoJSON Choropleth */}
        {showChoropleth && (
          <GeoJSON
            key={`geojson-states-${selectedState}-${showChoropleth}`}
            data={indiaGeoData}
            style={getFeatureStyle}
            onEachFeature={onEachFeature}
          />
        )}

        {/* Interactive Project Markers */}
        {showMarkers &&
          markerPositions.slice(0, 150).map(({ project, position }, idx) => {
            const cat = String(project.risk_category || 'MEDIUM').toUpperCase();
            return (
              <Marker
                key={`marker-${project.project_id}-${idx}`}
                position={position}
                icon={createCustomPin(cat)}
              >
                <Popup>
                  <div className="p-3.5 max-w-xs space-y-2 text-slate-100">
                    <div className="flex items-center justify-between border-b border-slate-700/80 pb-2">
                      <span className="font-mono text-[11px] text-slate-400">ID: {project.project_id}</span>
                      <RiskBadge category={project.risk_category} score={project.risk_score} size="sm" />
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
                          {((project.delay_probability || 0) * 100).toFixed(1)}%
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
          })}
      </MapContainer>
    </div>
  );
}

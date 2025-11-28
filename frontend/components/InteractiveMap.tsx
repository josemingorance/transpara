'use client';

/**
 * Interactive Map Component using Leaflet
 *
 * Displays a visual map of Spanish regions with color-coded risk/budget data
 * Click on regions to filter the detailed table below
 */

import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, GeoJSON } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

interface RegionSummary {
  total_budget: number;
  avg_risk_score: number;
  high_risk_count: number;
  total_contracts: number;
}

interface InteractiveMapProps {
  regionData: Record<string, RegionSummary>;
  onRegionClick: (regionName: string) => void;
  selectedRegion: string | null;
}

export const InteractiveMap: React.FC<InteractiveMapProps> = ({
  regionData,
  onRegionClick,
  selectedRegion,
}) => {
  const [geoJson, setGeoJson] = useState<any>(null);

  useEffect(() => {
    // Load GeoJSON
    fetch('/spanish-regions.geojson')
      .then((res) => res.json())
      .then((data) => setGeoJson(data))
      .catch((err) => console.error('Error loading GeoJSON:', err));
  }, []);

  // Get color based on risk score
  const getRiskColor = (avgRisk: number): string => {
    if (avgRisk >= 70) return '#dc2626'; // Dark red
    if (avgRisk >= 60) return '#ef4444'; // Red
    if (avgRisk >= 40) return '#f97316'; // Orange
    if (avgRisk >= 20) return '#eab308'; // Yellow
    return '#22c55e'; // Green
  };

  // Style function for GeoJSON features
  const onEachFeature = (feature: any, layer: L.Layer) => {
    const regionName = feature.properties.name;
    const data = regionData[regionName];

    let fillColor = '#cccccc'; // Gray default
    let weight = 1;

    if (data) {
      fillColor = getRiskColor(data.avg_risk_score);
      weight = selectedRegion === regionName ? 3 : 1;
    }

    (layer as L.Path).setStyle({
      fillColor,
      weight,
      opacity: 0.8,
      color: selectedRegion === regionName ? '#000' : '#555',
      dashArray: '',
      fillOpacity: 0.7,
    });

    // Add popup and click handler
    const popupContent = data
      ? `
        <div class="p-2">
          <strong>${regionName}</strong><br/>
          Contracts: ${data.total_contracts}<br/>
          Budget: €${(data.total_budget / 1000000).toFixed(1)}M<br/>
          Avg Risk: ${data.avg_risk_score.toFixed(1)}/100<br/>
          High Risk: ${data.high_risk_count}
        </div>
      `
      : `<div class="p-2"><strong>${regionName}</strong><br/>No data</div>`;

    layer.bindPopup(popupContent);

    layer.on('click', () => {
      onRegionClick(regionName);
    });
  };

  if (!geoJson) {
    return (
      <div className="w-full h-96 bg-gray-100 rounded-lg flex items-center justify-center">
        <div className="text-gray-500">Loading map...</div>
      </div>
    );
  }

  return (
    <div className="w-full rounded-lg overflow-hidden shadow-lg">
      <MapContainer
        center={[40.46, -3.75]}
        zoom={6}
        style={{ height: '500px', width: '100%' }}
        dragging={true}
        zoomControl={true}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; OpenStreetMap contributors'
          maxZoom={19}
        />
        <GeoJSON data={geoJson} onEachFeature={onEachFeature} />
      </MapContainer>

      {/* Legend */}
      <div className="bg-white p-4 border-t">
        <div className="text-sm font-semibold mb-3">Risk Level Legend</div>
        <div className="grid grid-cols-2 gap-3 text-xs">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded" style={{ backgroundColor: '#22c55e' }} />
            <span>Minimal (&lt; 20)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded" style={{ backgroundColor: '#eab308' }} />
            <span>Low (20-40)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded" style={{ backgroundColor: '#f97316' }} />
            <span>Medium (40-60)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded" style={{ backgroundColor: '#ef4444' }} />
            <span>High (60-70)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded" style={{ backgroundColor: '#dc2626' }} />
            <span>Critical (≥70)</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default InteractiveMap;
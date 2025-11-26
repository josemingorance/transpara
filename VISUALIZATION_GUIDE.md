# Visualization Components Guide

This guide provides React components for the heatmap and Spain geographic visualizations.

## 1. Installation Dependencies

```bash
npm install recharts leaflet react-leaflet geojson-bounds
npm install --save-dev @types/geojson
```

## 2. API Endpoints

### Temporal Heatmap Endpoint
```
GET /api/v1/analytics/temporal_heatmap/?granularity=daily&days=180
```

**Response:**
```json
[
  {
    "date": "2025-08-01",
    "total_contracts": 1,
    "high_risk": 0,
    "medium_risk": 0,
    "low_risk": 1,
    "total_budget": 2500000.0,
    "avg_risk": 21.75
  }
]
```

### Geographical Distribution Endpoint
```
GET /api/v1/analytics/geographical_distribution/
```

**Response:**
```json
{
  "detailed": [
    {
      "region": "La Rioja",
      "province": "La Rioja",
      "municipality": "Logroño",
      "total_contracts": 6,
      "total_budget": 15000000.0,
      "awarded_amount": 14500000.0,
      "avg_risk_score": 16.79,
      "high_risk_count": 1
    }
  ],
  "summary_by_region": {
    "La Rioja": {
      "total_budget": 15000000.0,
      "avg_risk_score": 16.79,
      "high_risk_count": 1,
      "total_contracts": 6
    }
  }
}
```

## 3. React Components

### TemporalHeatmap Component

```jsx
// components/TemporalHeatmap.tsx
import React, { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';

interface HeatmapData {
  date: string;
  total_contracts: number;
  high_risk: number;
  medium_risk: number;
  low_risk: number;
  total_budget: number;
  avg_risk: number;
}

interface TemporalHeatmapProps {
  granularity?: 'daily' | 'weekly';
  days?: number;
}

export const TemporalHeatmap: React.FC<TemporalHeatmapProps> = ({
  granularity = 'daily',
  days = 180
}) => {
  const [data, setData] = useState<HeatmapData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(
          `/api/v1/analytics/temporal_heatmap/?granularity=${granularity}&days=${days}`
        );
        if (!response.ok) throw new Error('Failed to fetch heatmap data');
        const result = await response.json();
        setData(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [granularity, days]);

  if (loading) return <div className="p-4">Loading heatmap...</div>;
  if (error) return <div className="p-4 text-red-600">Error: {error}</div>;

  // Get color based on risk level
  const getRiskColor = (avg_risk: number): string => {
    if (avg_risk >= 60) return '#ef4444'; // Red - High
    if (avg_risk >= 40) return '#f97316'; // Orange - Medium
    return '#22c55e'; // Green - Low
  };

  // Calculate intensity based on total contracts
  const maxContracts = Math.max(...data.map(d => d.total_contracts));

  return (
    <div className="w-full h-full bg-white rounded-lg shadow-lg p-6">
      <h2 className="text-2xl font-bold mb-4">Temporal Activity Heatmap</h2>

      <div className="mb-4 text-sm text-gray-600">
        {data.length} days of contract activity
      </div>

      {/* Grid Heatmap */}
      <div className="mb-8">
        <h3 className="text-lg font-semibold mb-4">Daily Activity Grid</h3>
        <div className="grid gap-1" style={{
          gridTemplateColumns: 'repeat(auto-fit, minmax(20px, 1fr))',
          maxWidth: '100%'
        }}>
          {data.map((day, idx) => (
            <div
              key={idx}
              className="w-5 h-5 rounded cursor-pointer hover:ring-2 hover:ring-blue-500 transition-all"
              style={{
                backgroundColor: getRiskColor(day.avg_risk),
                opacity: 0.3 + (day.total_contracts / maxContracts) * 0.7,
              }}
              title={`${day.date}: ${day.total_contracts} contracts, Risk: ${day.avg_risk.toFixed(1)}`}
            />
          ))}
        </div>
      </div>

      {/* Bar Chart */}
      <div className="mb-8">
        <h3 className="text-lg font-semibold mb-4">Contract Activity Over Time</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 12 }}
              interval={Math.floor(data.length / 10)}
            />
            <YAxis />
            <Tooltip
              formatter={(value: any) => value.toLocaleString()}
              labelFormatter={(label) => `Date: ${label}`}
            />
            <Legend />
            <Bar dataKey="low_risk" stackId="a" fill="#22c55e" name="Low Risk" />
            <Bar dataKey="medium_risk" stackId="a" fill="#f97316" name="Medium Risk" />
            <Bar dataKey="high_risk" stackId="a" fill="#ef4444" name="High Risk" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Risk Score Trend */}
      <div>
        <h3 className="text-lg font-semibold mb-4">Average Risk Score Trend</h3>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 12 }}
              interval={Math.floor(data.length / 10)}
            />
            <YAxis domain={[0, 100]} />
            <Tooltip />
            <Bar dataKey="avg_risk" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
```

### SpainGeographicMap Component

```jsx
// components/SpainGeographicMap.tsx
import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, GeoJSON, Popup } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

interface RegionData {
  region: string;
  province: string;
  municipality: string;
  total_contracts: number;
  total_budget: number;
  awarded_amount: number;
  avg_risk_score: number;
  high_risk_count: number;
}

interface GeoData {
  detailed: RegionData[];
  summary_by_region: Record<string, {
    total_budget: number;
    avg_risk_score: number;
    high_risk_count: number;
    total_contracts: number;
  }>;
}

// Spanish regions GeoJSON (simplified)
const SPAIN_GEOJSON = {
  type: 'FeatureCollection',
  features: [
    // This should be replaced with actual Spanish regions GeoJSON
    // Download from: https://github.com/nvkelso/natural-earth-vector/blob/master/geojson/
  ]
};

export const SpainGeographicMap: React.FC = () => {
  const [geoData, setGeoData] = useState<GeoData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch('/api/v1/analytics/geographical_distribution/');
        if (!response.ok) throw new Error('Failed to fetch geographic data');
        const result = await response.json();
        setGeoData(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const getRiskColor = (riskScore: number): string => {
    if (riskScore >= 60) return '#ef4444'; // Red
    if (riskScore >= 40) return '#f97316'; // Orange
    if (riskScore >= 20) return '#eab308'; // Yellow
    return '#22c55e'; // Green
  };

  if (loading) return <div className="p-4">Loading map...</div>;
  if (error) return <div className="p-4 text-red-600">Error: {error}</div>;
  if (!geoData) return <div className="p-4">No data available</div>;

  return (
    <div className="w-full h-full bg-white rounded-lg shadow-lg p-6">
      <h2 className="text-2xl font-bold mb-4">Spain - Geographic Budget Distribution</h2>

      {/* Regional Summary Cards */}
      <div className="mb-6">
        <h3 className="text-lg font-semibold mb-4">Regional Summary</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Object.entries(geoData.summary_by_region).map(([region, data]) => (
            <div key={region} className="p-4 border rounded-lg hover:shadow-lg transition-shadow">
              <div className="flex items-center mb-2">
                <div
                  className="w-4 h-4 rounded mr-2"
                  style={{ backgroundColor: getRiskColor(data.avg_risk_score) }}
                />
                <h4 className="font-semibold text-sm">{region}</h4>
              </div>
              <div className="text-sm space-y-1 text-gray-600">
                <p>💰 Budget: €{(data.total_budget / 1000000).toFixed(1)}M</p>
                <p>📋 Contracts: {data.total_contracts}</p>
                <p>⚠️ High Risk: {data.high_risk_count}</p>
                <p>📊 Avg Risk: {data.avg_risk_score.toFixed(1)}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Detailed Location List */}
      <div>
        <h3 className="text-lg font-semibold mb-4">Detailed Locations</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full border-collapse text-sm">
            <thead className="bg-gray-100">
              <tr>
                <th className="border p-2 text-left">Region</th>
                <th className="border p-2 text-left">Province</th>
                <th className="border p-2 text-left">Municipality</th>
                <th className="border p-2 text-right">Contracts</th>
                <th className="border p-2 text-right">Budget</th>
                <th className="border p-2 text-right">Avg Risk</th>
              </tr>
            </thead>
            <tbody>
              {geoData.detailed.map((location, idx) => (
                <tr key={idx} className="hover:bg-gray-50">
                  <td className="border p-2">{location.region}</td>
                  <td className="border p-2">{location.province}</td>
                  <td className="border p-2">{location.municipality}</td>
                  <td className="border p-2 text-right">{location.total_contracts}</td>
                  <td className="border p-2 text-right">
                    €{(location.total_budget / 1000000).toFixed(1)}M
                  </td>
                  <td className="border p-2 text-right">
                    <span
                      className="px-2 py-1 rounded text-white text-xs"
                      style={{ backgroundColor: getRiskColor(location.avg_risk_score) }}
                    >
                      {location.avg_risk_score.toFixed(1)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Map Container (requires Spanish regions GeoJSON) */}
      <div className="mt-6 h-96 rounded-lg overflow-hidden border">
        <MapContainer
          center={[40, -3.7]}
          zoom={5}
          style={{ height: '100%', width: '100%' }}
        >
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution='&copy; OpenStreetMap contributors'
          />
          {/* GeoJSON layer would go here with coloring based on data */}
        </MapContainer>
      </div>
    </div>
  );
};
```

### Combined Dashboard Component

```jsx
// components/VisualizationDashboard.tsx
import React, { useState } from 'react';
import { TemporalHeatmap } from './TemporalHeatmap';
import { SpainGeographicMap } from './SpainGeographicMap';

export const VisualizationDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'heatmap' | 'map'>('heatmap');
  const [granularity, setGranularity] = useState<'daily' | 'weekly'>('daily');
  const [days, setDays] = useState(180);

  return (
    <div className="w-full min-h-screen bg-gray-50 p-6">
      <h1 className="text-4xl font-bold mb-8">Contract Analysis Visualizations</h1>

      {/* Tab Navigation */}
      <div className="flex gap-4 mb-6">
        <button
          onClick={() => setActiveTab('heatmap')}
          className={`px-6 py-2 rounded-lg font-semibold transition-colors ${
            activeTab === 'heatmap'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-200 text-gray-800 hover:bg-gray-300'
          }`}
        >
          📊 Temporal Heatmap
        </button>
        <button
          onClick={() => setActiveTab('map')}
          className={`px-6 py-2 rounded-lg font-semibold transition-colors ${
            activeTab === 'map'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-200 text-gray-800 hover:bg-gray-300'
          }`}
        >
          🗺️ Spain Geographic Map
        </button>
      </div>

      {/* Heatmap Tab */}
      {activeTab === 'heatmap' && (
        <div>
          <div className="mb-6 flex gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">Granularity</label>
              <select
                value={granularity}
                onChange={(e) => setGranularity(e.target.value as 'daily' | 'weekly')}
                className="border rounded px-4 py-2"
              >
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Days to Show</label>
              <select
                value={days}
                onChange={(e) => setDays(Number(e.target.value))}
                className="border rounded px-4 py-2"
              >
                <option value={30}>Last 30 days</option>
                <option value={90}>Last 90 days</option>
                <option value={180}>Last 6 months</option>
                <option value={365}>Last year</option>
              </select>
            </div>
          </div>
          <TemporalHeatmap granularity={granularity} days={days} />
        </div>
      )}

      {/* Map Tab */}
      {activeTab === 'map' && (
        <SpainGeographicMap />
      )}
    </div>
  );
};

// Usage in your main app:
// <VisualizationDashboard />
```

## 4. Integration Steps

1. **Install dependencies:**
   ```bash
   npm install recharts leaflet react-leaflet
   ```

2. **Add components to your frontend project:**
   - Place the component files in your `src/components/` directory

3. **Import and use:**
   ```jsx
   import { VisualizationDashboard } from './components/VisualizationDashboard';

   function App() {
    return <VisualizationDashboard />;
   }
   ```

4. **For full Spain map visualization:**
   - Download Spanish regions GeoJSON from: [Natural Earth Vector](https://github.com/nvkelso/natural-earth-vector)
   - Or use: [Spanish provinces GeoJSON](https://github.com/deldersveld/topojson/blob/master/countries/spain/spain-provinces.json)

## 5. Styling Notes

- Uses Tailwind CSS classes - adjust as needed for your CSS framework
- Color coding:
  - 🟢 Green: Low risk (< 40)
  - 🟡 Yellow: Medium-low (40-60)
  - 🟠 Orange: Medium-high (40-60 continued)
  - 🔴 Red: High risk (≥ 60)

## 6. API Testing

Test the endpoints directly:

```bash
# Heatmap
curl "http://localhost:8000/api/v1/analytics/temporal_heatmap/?granularity=daily&days=180"

# Geographic distribution
curl "http://localhost:8000/api/v1/analytics/geographical_distribution/"
```

---

**Ready to integrate!** The backend API is ready and returns all necessary data for these visualizations.

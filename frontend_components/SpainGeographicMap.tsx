/**
 * Spain Geographic Map Component
 *
 * Displays contract distribution across Spanish regions with:
 * - Regional data cards showing budget and risk metrics
 * - Detailed table of all locations
 * - Color-coded risk levels
 * - Budget visualization
 *
 * Features:
 * - Sortable table
 * - Regional summary with key metrics
 * - Risk-based color coding
 */

import React, { useEffect, useState } from 'react';

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

interface RegionSummary {
  total_budget: number;
  avg_risk_score: number;
  high_risk_count: number;
  total_contracts: number;
}

interface GeoData {
  detailed: RegionData[];
  summary_by_region: Record<string, RegionSummary>;
}

type SortField = 'region' | 'contracts' | 'budget' | 'risk';
type SortOrder = 'asc' | 'desc';

export const SpainGeographicMap: React.FC = () => {
  const [geoData, setGeoData] = useState<GeoData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortField, setSortField] = useState<SortField>('budget');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');
  const [selectedRegion, setSelectedRegion] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const response = await fetch(
          '/api/v1/analytics/geographical_distribution/'
        );
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

  // Get color based on risk level
  const getRiskColor = (riskScore: number): string => {
    if (riskScore >= 70) return '#dc2626'; // Dark red
    if (riskScore >= 60) return '#ef4444'; // Red
    if (riskScore >= 40) return '#f97316'; // Orange
    if (riskScore >= 20) return '#eab308'; // Yellow
    return '#22c55e'; // Green
  };

  const getRiskLabel = (riskScore: number): string => {
    if (riskScore >= 70) return 'CRITICAL';
    if (riskScore >= 60) return 'HIGH';
    if (riskScore >= 40) return 'MEDIUM';
    if (riskScore >= 20) return 'LOW';
    return 'MINIMAL';
  };

  // Format budget
  const formatBudget = (budget: number): string => {
    if (budget >= 1000000) return `€${(budget / 1000000).toFixed(1)}M`;
    if (budget >= 1000) return `€${(budget / 1000).toFixed(1)}K`;
    return `€${budget.toFixed(0)}`;
  };

  // Sort detailed data
  const getSortedData = (): RegionData[] => {
    if (!geoData) return [];

    let data = [...geoData.detailed];

    data.sort((a, b) => {
      let aValue: any, bValue: any;

      switch (sortField) {
        case 'region':
          aValue = a.region;
          bValue = b.region;
          break;
        case 'contracts':
          aValue = a.total_contracts;
          bValue = b.total_contracts;
          break;
        case 'budget':
          aValue = a.total_budget;
          bValue = b.total_budget;
          break;
        case 'risk':
          aValue = a.avg_risk_score;
          bValue = b.avg_risk_score;
          break;
      }

      if (sortOrder === 'asc') {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });

    return data;
  };

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('desc');
    }
  };

  if (loading) {
    return (
      <div className="w-full h-64 bg-white rounded-lg shadow-lg p-6 flex items-center justify-center">
        <div className="text-gray-500">Loading geographic data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="w-full bg-white rounded-lg shadow-lg p-6 text-red-600">
        Error: {error}
      </div>
    );
  }

  if (!geoData) {
    return (
      <div className="w-full bg-white rounded-lg shadow-lg p-6 text-gray-500">
        No geographic data available
      </div>
    );
  }

  const sortedData = getSortedData();
  const filteredData = selectedRegion
    ? sortedData.filter((d) => d.region === selectedRegion)
    : sortedData;

  // Calculate totals
  const totalBudget = Object.values(geoData.summary_by_region).reduce(
    (sum, region) => sum + region.total_budget,
    0
  );
  const totalContracts = Object.values(geoData.summary_by_region).reduce(
    (sum, region) => sum + region.total_contracts,
    0
  );
  const avgRisk =
    Object.values(geoData.summary_by_region).reduce((sum, region) => {
      return sum + region.avg_risk_score * region.total_contracts;
    }, 0) / totalContracts;

  return (
    <div className="w-full bg-white rounded-lg shadow-lg p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold mb-2">🗺️ Spain - Geographic Budget Distribution</h2>
        <p className="text-gray-600 text-sm">
          Contract distribution across Spanish autonomous communities
        </p>
      </div>

      {/* Overview Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <div className="p-4 bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg border border-blue-200">
          <div className="text-sm text-blue-600 font-medium">Total Budget</div>
          <div className="text-2xl font-bold text-blue-900">
            {formatBudget(totalBudget)}
          </div>
        </div>
        <div className="p-4 bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg border border-purple-200">
          <div className="text-sm text-purple-600 font-medium">Total Contracts</div>
          <div className="text-2xl font-bold text-purple-900">
            {totalContracts.toLocaleString()}
          </div>
        </div>
        <div className="p-4 bg-gradient-to-br from-orange-50 to-orange-100 rounded-lg border border-orange-200">
          <div className="text-sm text-orange-600 font-medium">Avg Risk</div>
          <div className="text-2xl font-bold text-orange-900">
            {avgRisk.toFixed(2)}/100
          </div>
        </div>
        <div className="p-4 bg-gradient-to-br from-green-50 to-green-100 rounded-lg border border-green-200">
          <div className="text-sm text-green-600 font-medium">Regions</div>
          <div className="text-2xl font-bold text-green-900">
            {Object.keys(geoData.summary_by_region).length}
          </div>
        </div>
      </div>

      {/* Regional Summary Cards */}
      <div className="mb-8">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          📍 Regional Summary
          {selectedRegion && (
            <button
              onClick={() => setSelectedRegion(null)}
              className="ml-auto text-sm px-3 py-1 bg-gray-200 hover:bg-gray-300 rounded transition-colors"
            >
              Clear Filter
            </button>
          )}
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-h-96 overflow-y-auto">
          {Object.entries(geoData.summary_by_region)
            .sort((a, b) => b[1].total_budget - a[1].total_budget)
            .map(([region, data]) => (
              <div
                key={region}
                onClick={() =>
                  setSelectedRegion(selectedRegion === region ? null : region)
                }
                className={`p-4 border-2 rounded-lg cursor-pointer transition-all hover:shadow-lg ${
                  selectedRegion === region
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <h4 className="font-semibold text-sm">{region}</h4>
                  </div>
                  <div
                    className="w-4 h-4 rounded ml-2 flex-shrink-0"
                    style={{
                      backgroundColor: getRiskColor(data.avg_risk_score),
                    }}
                    title={getRiskLabel(data.avg_risk_score)}
                  />
                </div>

                <div className="space-y-2 text-sm">
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">💰 Budget:</span>
                    <span className="font-semibold">
                      {formatBudget(data.total_budget)}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">📋 Contracts:</span>
                    <span className="font-semibold">
                      {data.total_contracts}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">⚠️ Avg Risk:</span>
                    <span
                      className="font-semibold px-2 py-1 rounded text-white text-xs"
                      style={{
                        backgroundColor: getRiskColor(data.avg_risk_score),
                      }}
                    >
                      {data.avg_risk_score.toFixed(1)}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">🚨 High Risk:</span>
                    <span className="font-semibold">
                      {data.high_risk_count}
                    </span>
                  </div>
                </div>

                {/* Budget bar */}
                <div className="mt-3 w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-500 h-2 rounded-full transition-all"
                    style={{
                      width: `${(data.total_budget / totalBudget) * 100}%`,
                    }}
                  />
                </div>
              </div>
            ))}
        </div>
      </div>

      {/* Detailed Location Table */}
      <div>
        <h3 className="text-lg font-semibold mb-4">📊 Detailed Locations</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full border-collapse">
            <thead className="bg-gray-100 border-b-2 border-gray-300">
              <tr>
                <th
                  className="border p-3 text-left cursor-pointer hover:bg-gray-200 font-semibold"
                  onClick={() => handleSort('region')}
                >
                  Region{' '}
                  {sortField === 'region' &&
                    (sortOrder === 'asc' ? '↑' : '↓')}
                </th>
                <th className="border p-3 text-left font-semibold">Province</th>
                <th className="border p-3 text-left font-semibold">
                  Municipality
                </th>
                <th
                  className="border p-3 text-right cursor-pointer hover:bg-gray-200 font-semibold"
                  onClick={() => handleSort('contracts')}
                >
                  Contracts{' '}
                  {sortField === 'contracts' &&
                    (sortOrder === 'asc' ? '↑' : '↓')}
                </th>
                <th
                  className="border p-3 text-right cursor-pointer hover:bg-gray-200 font-semibold"
                  onClick={() => handleSort('budget')}
                >
                  Budget {sortField === 'budget' && (sortOrder === 'asc' ? '↑' : '↓')}
                </th>
                <th className="border p-3 text-right font-semibold">Awarded</th>
                <th
                  className="border p-3 text-right cursor-pointer hover:bg-gray-200 font-semibold"
                  onClick={() => handleSort('risk')}
                >
                  Avg Risk{' '}
                  {sortField === 'risk' && (sortOrder === 'asc' ? '↑' : '↓')}
                </th>
                <th className="border p-3 text-right font-semibold">High Risk</th>
              </tr>
            </thead>
            <tbody>
              {filteredData.map((location, idx) => (
                <tr
                  key={idx}
                  className="hover:bg-blue-50 border-b transition-colors"
                >
                  <td className="border p-3 font-medium">{location.region}</td>
                  <td className="border p-3 text-gray-700">{location.province}</td>
                  <td className="border p-3 text-gray-700">
                    {location.municipality}
                  </td>
                  <td className="border p-3 text-right font-semibold">
                    {location.total_contracts}
                  </td>
                  <td className="border p-3 text-right font-semibold text-blue-600">
                    {formatBudget(location.total_budget)}
                  </td>
                  <td className="border p-3 text-right text-gray-600">
                    {formatBudget(location.awarded_amount)}
                  </td>
                  <td className="border p-3 text-right">
                    <span
                      className="px-2 py-1 rounded text-white text-xs font-semibold"
                      style={{
                        backgroundColor: getRiskColor(
                          location.avg_risk_score
                        ),
                      }}
                    >
                      {location.avg_risk_score.toFixed(1)}
                    </span>
                  </td>
                  <td className="border p-3 text-right font-semibold text-red-600">
                    {location.high_risk_count}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {filteredData.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            No data for the selected region
          </div>
        )}
      </div>

      {/* Note about actual map */}
      <div className="mt-8 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <p className="text-sm text-blue-800">
          <strong>💡 Note:</strong> For an interactive Leaflet map with Spanish
          regions overlay, download the GeoJSON from{' '}
          <a
            href="https://github.com/deldersveld/topojson/blob/master/countries/spain/spain-provinces.json"
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 hover:underline"
          >
            Spanish provinces GeoJSON
          </a>
          {' '}and integrate with react-leaflet.
        </p>
      </div>
    </div>
  );
};

export default SpainGeographicMap;

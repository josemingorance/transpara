'use client';

/**
 * Temporal Heatmap Component
 *
 * Displays contract activity over time with risk-based color coding.
 * Similar to GitHub contribution heatmap or crypto market heatmaps.
 *
 * Features:
 * - Grid heatmap showing daily/weekly activity
 * - Bar chart showing risk distribution
 * - Average risk score trend line
 * - Configurable time range
 */

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  LineChart,
  Line,
} from 'recharts';

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
  days = 180,
}) => {
  const router = useRouter();
  const [data, setData] = useState<HeatmapData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hoveredCell, setHoveredCell] = useState<number | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
        const response = await fetch(
          `${apiUrl}/analytics/temporal_heatmap/?granularity=${granularity}&days=${days}`
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

  // Get color based on risk level (GitHub-style)
  const getRiskColor = (avg_risk: number): string => {
    if (avg_risk >= 70) return '#dc2626'; // Dark red - Critical
    if (avg_risk >= 60) return '#ef4444'; // Red - High
    if (avg_risk >= 40) return '#f97316'; // Orange - Medium
    if (avg_risk >= 20) return '#eab308'; // Yellow - Low
    return '#22c55e'; // Green - Minimal
  };

  // Format budget in readable format
  const formatBudget = (budget: number): string => {
    if (budget >= 1000000) return `€${(budget / 1000000).toFixed(1)}M`;
    if (budget >= 1000) return `€${(budget / 1000).toFixed(1)}K`;
    return `€${budget.toFixed(0)}`;
  };

  if (loading) {
    return (
      <div className="w-full h-64 bg-white rounded-lg shadow-lg p-6 flex items-center justify-center">
        <div className="text-gray-500">Loading heatmap data...</div>
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

  const maxContracts = Math.max(...data.map((d) => d.total_contracts), 1);
  const cellsPerRow = 26; // ~6 months per row for daily view

  return (
    <div className="w-full bg-white rounded-lg shadow-lg p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold mb-2">📊 Temporal Activity Heatmap</h2>
        <p className="text-gray-600 text-sm">
          {data.length} days of contract activity • Color intensity shows risk level and contract volume
        </p>
      </div>

      {/* Grid Heatmap - GitHub Style */}
      <div className="mb-8">
        <h3 className="text-lg font-semibold mb-4">Daily Activity Grid</h3>
        <div className="overflow-x-auto">
          <div className="flex flex-col gap-1 pb-2">
            {/* Create grid layout */}
            <div className="flex gap-1 flex-wrap">
              {data.map((day, idx) => {
                const intensity =
                  0.3 + (day.total_contracts / maxContracts) * 0.7;
                return (
                  <div
                    key={idx}
                    className="group relative"
                    onMouseEnter={() => setHoveredCell(idx)}
                    onMouseLeave={() => setHoveredCell(null)}
                  >
                    <button
                      onClick={() => {
                        router.push(`/contracts/filtered?date=${day.date}`);
                      }}
                      className="w-4 h-4 rounded-sm cursor-pointer hover:ring-2 hover:ring-blue-500 hover:ring-offset-2 transition-all block"
                      style={{
                        backgroundColor: getRiskColor(day.avg_risk),
                        opacity: intensity,
                      }}
                      title={`Click to view contracts from ${day.date}`}
                    />
                    {/* Tooltip */}
                    {hoveredCell === idx && (
                      <div className="absolute z-10 bottom-full left-1/2 transform -translate-x-1/2 mb-2 bg-gray-900 text-white text-xs px-3 py-2 rounded whitespace-nowrap cursor-default pointer-events-none">
                        <div className="font-semibold">{day.date}</div>
                        <div>Contracts: {day.total_contracts}</div>
                        <div>
                          Risk: {day.avg_risk.toFixed(1)}/100 (
                          {day.high_risk} high)
                        </div>
                        <div>Budget: {formatBudget(day.total_budget)}</div>
                        <div className="text-xs mt-1 text-blue-200">Click to view contracts</div>
                        <div className="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-gray-900"></div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Color legend */}
        <div className="mt-6 flex items-center gap-6 text-sm">
          <div>Legend:</div>
          <div className="flex gap-4">
            {[
              { color: '#22c55e', label: 'Minimal (< 20)' },
              { color: '#eab308', label: 'Low (20-40)' },
              { color: '#f97316', label: 'Medium (40-60)' },
              { color: '#ef4444', label: 'High (≥ 60)' },
            ].map((item) => (
              <div key={item.label} className="flex items-center gap-2">
                <div
                  className="w-3 h-3 rounded-sm"
                  style={{ backgroundColor: item.color }}
                />
                <span className="text-gray-600">{item.label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Bar Chart - Risk Distribution */}
      <div className="mb-8">
        <h3 className="text-lg font-semibold mb-4">📈 Risk Distribution Over Time</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data} margin={{ top: 20, right: 30, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 12, fill: '#6b7280' }}
              interval={Math.floor(data.length / 10) || 0}
              angle={-45}
              textAnchor="end"
              height={60}
            />
            <YAxis stroke="#6b7280" />
            <Tooltip
              contentStyle={{
                backgroundColor: '#fff',
                border: '1px solid #d1d5db',
                borderRadius: '8px',
              }}
              formatter={(value: number | string) => {
                if (typeof value === 'number') {
                  return value.toLocaleString();
                }
                return value;
              }}
              labelFormatter={(label: string) => `📅 ${label}`}
            />
            <Legend />
            <Bar
              dataKey="low_risk"
              stackId="a"
              fill="#22c55e"
              name="Low Risk"
            />
            <Bar
              dataKey="medium_risk"
              stackId="a"
              fill="#f97316"
              name="Medium Risk"
            />
            <Bar
              dataKey="high_risk"
              stackId="a"
              fill="#ef4444"
              name="High Risk"
            />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Average Risk Score Trend */}
      <div>
        <h3 className="text-lg font-semibold mb-4">⚠️ Average Risk Score Trend</h3>
        <ResponsiveContainer width="100%" height={250}>
          <LineChart data={data} margin={{ top: 20, right: 30, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 12, fill: '#6b7280' }}
              interval={Math.floor(data.length / 10) || 0}
              angle={-45}
              textAnchor="end"
              height={60}
            />
            <YAxis domain={[0, 100]} stroke="#6b7280" />
            <Tooltip
              contentStyle={{
                backgroundColor: '#fff',
                border: '1px solid #d1d5db',
                borderRadius: '8px',
              }}
              formatter={(value: number | string) => {
                if (typeof value === 'number') {
                  return [value.toFixed(2), 'Avg Risk Score'];
                }
                return [value, 'Avg Risk Score'];
              }}
              labelFormatter={(label: string) => `📅 ${label}`}
            />
            <Line
              type="monotone"
              dataKey="avg_risk"
              stroke="#8b5cf6"
              strokeWidth={2}
              dot={false}
              name="Avg Risk"
              isAnimationActive={true}
            />
            {/* Reference lines */}
            <Line
              dataKey={() => 60}
              stroke="#ef4444"
              strokeDasharray="5 5"
              dot={false}
              isAnimationActive={false}
            />
            <Line
              dataKey={() => 40}
              stroke="#f97316"
              strokeDasharray="5 5"
              dot={false}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
        <div className="mt-2 text-xs text-gray-500">
          📌 Dashed lines show risk thresholds (Orange: 40, Red: 60)
        </div>
      </div>

      {/* Summary Stats */}
      <div className="mt-8 grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 bg-gray-50 rounded-lg">
          <div className="text-sm text-gray-600">Total Contracts</div>
          <div className="text-2xl font-bold">
            {data.reduce((sum, d) => sum + d.total_contracts, 0).toLocaleString()}
          </div>
        </div>
        <div className="p-4 bg-gray-50 rounded-lg">
          <div className="text-sm text-gray-600">Total Budget</div>
          <div className="text-2xl font-bold">
            {formatBudget(data.reduce((sum, d) => sum + d.total_budget, 0))}
          </div>
        </div>
        <div className="p-4 bg-gray-50 rounded-lg">
          <div className="text-sm text-gray-600">Avg Risk Score</div>
          <div className="text-2xl font-bold">
            {(
              data.reduce((sum, d) => sum + d.avg_risk, 0) / data.length
            ).toFixed(2)}
          </div>
        </div>
        <div className="p-4 bg-gray-50 rounded-lg">
          <div className="text-sm text-gray-600">High Risk Contracts</div>
          <div className="text-2xl font-bold">
            {data.reduce((sum, d) => sum + d.high_risk, 0)}
          </div>
        </div>
      </div>
    </div>
  );
};

export default TemporalHeatmap;

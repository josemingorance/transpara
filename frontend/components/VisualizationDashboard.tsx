/**
 * Main Visualization Dashboard Component
 *
 * Combines temporal heatmap and geographic map visualizations
 * into a unified dashboard with tab navigation and controls.
 */

import React, { useState } from 'react';
import Link from 'next/link';
import { TemporalHeatmap } from './TemporalHeatmap';
import { SpainGeographicMap } from './SpainGeographicMap';

type TabType = 'heatmap' | 'map';

export const VisualizationDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('heatmap');
  const [granularity, setGranularity] = useState<'daily' | 'weekly'>('daily');
  const [days, setDays] = useState(180);

  return (
    <div className="w-full min-h-screen bg-gray-100 p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-gray-900 mb-2">
          📊 Contract Analysis Visualizations
        </h1>
        <p className="text-gray-600">
          Interactive analysis of contract distribution, risk metrics, and geographic spread
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="mb-6 flex gap-3 items-center">
        <button
          onClick={() => setActiveTab('heatmap')}
          className={`px-6 py-3 rounded-lg font-semibold transition-all flex items-center gap-2 ${
            activeTab === 'heatmap'
              ? 'bg-blue-600 text-white shadow-lg scale-105'
              : 'bg-white text-gray-800 hover:bg-gray-50 border border-gray-200'
          }`}
        >
          <span>📊</span>
          Temporal Heatmap
        </button>
        <button
          onClick={() => setActiveTab('map')}
          className={`px-6 py-3 rounded-lg font-semibold transition-all flex items-center gap-2 ${
            activeTab === 'map'
              ? 'bg-blue-600 text-white shadow-lg scale-105'
              : 'bg-white text-gray-800 hover:bg-gray-50 border border-gray-200'
          }`}
        >
          <span>🗺️</span>
          Spain Geographic Map
        </button>

        {/* Separator */}
        <div className="mx-4 h-6 border-r border-gray-300"></div>

        {/* Link to view all contracts */}
        <Link
          href="/contracts"
          className="px-6 py-3 rounded-lg font-semibold transition-all flex items-center gap-2 bg-white text-gray-800 hover:bg-gray-50 border border-gray-200"
        >
          <span>📋</span>
          All Contracts
        </Link>
      </div>

      {/* Heatmap Tab with Controls */}
      {activeTab === 'heatmap' && (
        <div>
          {/* Controls */}
          <div className="mb-6 bg-white rounded-lg shadow p-4 flex gap-4 flex-wrap">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                View Granularity
              </label>
              <select
                value={granularity}
                onChange={(e) =>
                  setGranularity(e.target.value as 'daily' | 'weekly')
                }
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
              >
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Time Period
              </label>
              <select
                value={days}
                onChange={(e) => setDays(Number(e.target.value))}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
              >
                <option value={30}>Last 30 days</option>
                <option value={90}>Last 90 days</option>
                <option value={180}>Last 6 months</option>
                <option value={365}>Last year</option>
              </select>
            </div>

            {/* Help text */}
            <div className="ml-auto flex items-center gap-2 text-sm text-gray-600">
              <span>💡</span>
              <span>
                Hover over cells to see details • Larger cells = more contracts
              </span>
            </div>
          </div>

          {/* Heatmap Component */}
          <TemporalHeatmap granularity={granularity} days={days} />
        </div>
      )}

      {/* Map Tab */}
      {activeTab === 'map' && (
        <div>
          {/* Info banner */}
          <div className="mb-6 bg-white border-l-4 border-green-500 rounded-lg shadow p-4">
            <p className="text-gray-700">
              <strong>✨ Geographic Analysis:</strong> This view shows how your budget is
              distributed across Spanish regions. Click on a region card to filter the
              detailed table below.
            </p>
          </div>

          {/* Geographic Map Component */}
          <SpainGeographicMap />
        </div>
      )}

      {/* Footer with API info */}
      <div className="mt-12 text-center text-sm text-gray-500">
        <p>
          Data powered by{' '}
          <span className="font-semibold text-gray-700">PublicWorks Analytics API</span>
        </p>
        <p className="mt-2">
          Last updated:{' '}
          {new Date().toLocaleDateString('es-ES', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
          })}
        </p>
      </div>
    </div>
  );
};

export default VisualizationDashboard;

/**
 * USAGE EXAMPLE:
 *
 * In your main App.tsx or dashboard page:
 *
 * ```tsx
 * import { VisualizationDashboard } from './components/VisualizationDashboard';
 *
 * function Dashboard() {
 *   return (
 *     <div>
 *       <VisualizationDashboard />
 *     </div>
 *   );
 * }
 *
 * export default Dashboard;
 * ```
 *
 * DEPENDENCIES:
 * - npm install recharts leaflet react-leaflet
 *
 * STYLING:
 * - Uses Tailwind CSS classes
 * - If you're using a different CSS framework, replace Tailwind classes
 */

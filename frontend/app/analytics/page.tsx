/**
 * Analytics Page
 *
 * View trends, charts, and insights about contracts and risks
 */

'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  api,
  RegionalStats,
  TrendData,
  Provider,
} from '@/lib/api';
import { Loading } from '@/components/Loading';
import { StatCard } from '@/components/StatCard';
import { formatCurrency, formatNumber } from '@/lib/utils';

export default function AnalyticsPage() {
  const [regionalStats, setRegionalStats] = useState<RegionalStats[]>([]);
  const [trends, setTrends] = useState<TrendData[]>([]);
  const [riskDistribution, setRiskDistribution] = useState<Record<string, number>>({});
  const [topProviders, setTopProviders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [trendDays, setTrendDays] = useState<30 | 60 | 90>(90);
  const [topBy, setTopBy] = useState<'contracts' | 'amount'>('contracts');

  useEffect(() => {
    async function loadAnalytics() {
      try {
        setLoading(true);
        const [regional, trendsData, risk, providers] = await Promise.all([
          api.getRegionalStats(),
          api.getTrends(trendDays),
          api.getRiskDistribution(),
          api.getTopProviders(topBy, 10),
        ]);

        setRegionalStats(regional);
        setTrends(trendsData);
        setRiskDistribution(risk);
        setTopProviders(providers);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load analytics');
      } finally {
        setLoading(false);
      }
    }

    loadAnalytics();
  }, [trendDays, topBy]);

  if (loading && regionalStats.length === 0) {
    return <Loading />;
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600">Error: {error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Analytics</h1>
        <p className="mt-2 text-gray-600">
          Insights and trends from contract data analysis
        </p>
      </div>

      {/* Risk Distribution */}
      <div className="card">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Risk Distribution</h2>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {Object.entries(riskDistribution).map(([level, count]) => (
            <div key={level} className="text-center">
              <p className="text-3xl font-bold text-gray-900">{count}</p>
              <p className="text-sm text-gray-600 capitalize">{level}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Trends */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">Contract Trends</h2>
          <div className="flex gap-2">
            <button
              onClick={() => setTrendDays(30)}
              className={`btn ${trendDays === 30 ? 'btn-primary' : 'btn-secondary'}`}
            >
              30 Days
            </button>
            <button
              onClick={() => setTrendDays(60)}
              className={`btn ${trendDays === 60 ? 'btn-primary' : 'btn-secondary'}`}
            >
              60 Days
            </button>
            <button
              onClick={() => setTrendDays(90)}
              className={`btn ${trendDays === 90 ? 'btn-primary' : 'btn-secondary'}`}
            >
              90 Days
            </button>
          </div>
        </div>

        {trends.length === 0 ? (
          <p className="text-center py-8 text-gray-500">No trend data available</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Contracts</th>
                  <th>Total Amount</th>
                  <th>Avg Risk Score</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {trends.slice(0, 10).map((trend) => (
                  <tr key={trend.date}>
                    <td className="font-medium">{trend.date}</td>
                    <td>{trend.count}</td>
                    <td>{formatCurrency(trend.total_amount)}</td>
                    <td>{parseFloat(trend.avg_risk_score).toFixed(1)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Regional Statistics */}
      <div className="card">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Regional Statistics</h2>

        {regionalStats.length === 0 ? (
          <p className="text-center py-8 text-gray-500">No regional data available</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="table">
              <thead>
                <tr>
                  <th>Region</th>
                  <th>Contracts</th>
                  <th>Total Budget</th>
                  <th>Avg Risk</th>
                  <th>High Risk</th>
                  <th>Overpriced</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {regionalStats
                  .sort((a, b) => parseFloat(b.total_budget) - parseFloat(a.total_budget))
                  .map((region) => (
                    <tr key={region.region}>
                      <td className="font-medium">{region.region}</td>
                      <td>{region.total_contracts}</td>
                      <td>{formatCurrency(region.total_budget)}</td>
                      <td>
                        <span
                          className={`badge ${
                            parseFloat(region.avg_risk_score) >= 60
                              ? 'bg-red-100 text-red-800'
                              : parseFloat(region.avg_risk_score) >= 40
                              ? 'bg-yellow-100 text-yellow-800'
                              : 'bg-green-100 text-green-800'
                          }`}
                        >
                          {parseFloat(region.avg_risk_score).toFixed(1)}
                        </span>
                      </td>
                      <td>{region.high_risk_count}</td>
                      <td>{region.overpriced_count}</td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Top Providers */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">Top Providers</h2>
          <div className="flex gap-2">
            <button
              onClick={() => setTopBy('contracts')}
              className={`btn ${topBy === 'contracts' ? 'btn-primary' : 'btn-secondary'}`}
            >
              By Contracts
            </button>
            <button
              onClick={() => setTopBy('amount')}
              className={`btn ${topBy === 'amount' ? 'btn-primary' : 'btn-secondary'}`}
            >
              By Amount
            </button>
          </div>
        </div>

        {topProviders.length === 0 ? (
          <p className="text-center py-8 text-gray-500">No provider data available</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="table">
              <thead>
                <tr>
                  <th>Rank</th>
                  <th>Provider</th>
                  <th>Tax ID</th>
                  <th>Contracts</th>
                  <th>Total Amount</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {topProviders.map((provider, index) => (
                  <tr key={provider.id}>
                    <td className="font-bold text-gray-900">#{index + 1}</td>
                    <td className="font-medium">{provider.name}</td>
                    <td className="font-mono text-sm text-gray-600">{provider.tax_id}</td>
                    <td>{provider.total_contracts}</td>
                    <td>{formatCurrency(provider.total_awarded_amount)}</td>
                    <td>
                      <Link
                        href={`/providers/${provider.id}`}
                        className="text-primary-600 hover:text-primary-700 font-medium"
                      >
                        View Profile
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Dashboard Page
 *
 * Main overview with key statistics and recent high-risk contracts
 */

'use client';

import { useEffect, useState } from 'react';
import { api, DashboardStats, Contract } from '@/lib/api';
import { StatCard } from '@/components/StatCard';
import { RiskBadge } from '@/components/RiskBadge';
import { Loading } from '@/components/Loading';
import { formatCurrency, formatDate, truncate } from '@/lib/utils';
import Link from 'next/link';

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recentHighRisk, setRecentHighRisk] = useState<Contract[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const [statsData, highRiskData] = await Promise.all([
          api.getDashboardStats(),
          api.getRecentHighRisk(),
        ]);
        setStats(statsData);
        setRecentHighRisk(highRiskData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load data');
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, []);

  if (loading) {
    return <Loading />;
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600">Error: {error}</p>
        <button
          onClick={() => window.location.reload()}
          className="mt-4 btn btn-primary"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!stats) {
    return null;
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-2 text-gray-600">
          Overview of public contract analysis and risk detection
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Total Contracts"
          value={stats.total_contracts}
          format="number"
          color="blue"
          icon={
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          }
        />

        <StatCard
          title="Total Budget"
          value={parseFloat(stats.total_budget)}
          format="currency"
          color="green"
          icon={
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
        />

        <StatCard
          title="High Risk Contracts"
          value={stats.high_risk_contracts}
          format="number"
          color="red"
          icon={
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          }
        />

        <StatCard
          title="Critical Alerts"
          value={stats.critical_alerts}
          format="number"
          color="red"
          icon={
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            </svg>
          }
        />
      </div>

      {/* Secondary Stats */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
        <StatCard
          title="Overpriced Contracts"
          value={stats.overpriced_contracts}
          format="number"
          color="yellow"
        />

        <StatCard
          title="Flagged Providers"
          value={stats.flagged_providers}
          format="number"
          color="red"
        />

        <StatCard
          title="Average Risk Score"
          value={parseFloat(stats.avg_risk_score).toFixed(1)}
          format="none"
          color="gray"
        />
      </div>

      {/* Recent High-Risk Contracts */}
      <div className="card">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-gray-900">
            Recent High-Risk Contracts
          </h2>
          <Link href="/contracts?high_risk=true" className="text-sm text-primary-600 hover:text-primary-700">
            View all →
          </Link>
        </div>

        {recentHighRisk.length === 0 ? (
          <p className="text-gray-500 text-center py-8">No high-risk contracts found</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="table">
              <thead>
                <tr>
                  <th>Contract ID</th>
                  <th>Title</th>
                  <th>Authority</th>
                  <th>Budget</th>
                  <th>Risk Score</th>
                  <th>Date</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {recentHighRisk.slice(0, 10).map((contract) => (
                  <tr key={contract.id}>
                    <td>
                      <Link
                        href={`/contracts/${contract.id}`}
                        className="text-primary-600 hover:text-primary-700 font-medium"
                      >
                        {contract.external_id}
                      </Link>
                    </td>
                    <td className="max-w-xs">
                      <div className="font-medium text-gray-900">
                        {truncate(contract.title, 60)}
                      </div>
                    </td>
                    <td className="text-gray-500">
                      {truncate(contract.contracting_authority, 30)}
                    </td>
                    <td className="text-gray-900">
                      {formatCurrency(contract.budget)}
                    </td>
                    <td>
                      <RiskBadge score={contract.risk_score} showLabel={false} />
                    </td>
                    <td className="text-gray-500">
                      {formatDate(contract.publication_date)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Activity Stats */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Contracts (Last 30 days)</span>
              <span className="text-2xl font-semibold text-gray-900">
                {stats.contracts_last_30_days}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Analyzed (Last 24h)</span>
              <span className="text-2xl font-semibold text-gray-900">
                {stats.analyzed_last_24_hours}
              </span>
            </div>
          </div>
        </div>

        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">System Health</h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Total Providers</span>
              <span className="text-2xl font-semibold text-gray-900">
                {stats.total_providers}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">System Status</span>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                Operational
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

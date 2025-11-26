/**
 * Dashboard Page
 */

'use client';

import { useEffect, useState } from 'react';
import { api, DashboardStats } from '@/lib/api';
import { Loading } from '@/components/Loading';
import { formatCurrency } from '@/lib/utils';

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const statsData = await api.getDashboardStats();
        setStats(statsData);
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
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-2 text-gray-600">Overview of contracts and risk detection</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <div className="card">
          <div className="text-3xl font-bold text-gray-900">{stats.total_contracts}</div>
          <div className="text-gray-600 text-sm mt-1">Total Contracts</div>
        </div>
        <div className="card">
          <div className="text-3xl font-bold text-green-600">{formatCurrency(stats.total_budget)}</div>
          <div className="text-gray-600 text-sm mt-1">Total Budget</div>
        </div>
        <div className="card">
          <div className="text-3xl font-bold text-red-600">{stats.high_risk_contracts}</div>
          <div className="text-gray-600 text-sm mt-1">High Risk Contracts</div>
        </div>
        <div className="card">
          <div className="text-3xl font-bold text-gray-900">{stats.total_providers}</div>
          <div className="text-gray-600 text-sm mt-1">Providers</div>
        </div>
      </div>
    </div>
  );
}

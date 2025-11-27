/**
 * Providers Page
 *
 * Browse and analyze public contract providers/suppliers
 */

'use client';

import { useEffect, useState, Suspense } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { api, Provider, PaginatedResponse } from '@/lib/api';
import { Loading } from '@/components/Loading';
import { RiskBadge } from '@/components/RiskBadge';
import {
  formatCurrency,
  truncate,
} from '@/lib/utils';

interface ProviderStats {
  total_providers: number;
  total_contracts: number;
  total_awarded: number;
  flagged_count: number;
  high_risk_count: number;
  avg_success_rate: number;
}

function ProvidersContent() {
  const router = useRouter();
  const [data, setData] = useState<PaginatedResponse<Provider> | null>(null);
  const [stats, setStats] = useState<ProviderStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<'awarded' | 'contracts' | 'risk'>('awarded');

  // Filters
  const [search, setSearch] = useState('');
  const [region, setRegion] = useState('');
  const [highRiskOnly, setHighRiskOnly] = useState(false);
  const [flaggedOnly, setFlaggedOnly] = useState(false);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const params: Record<string, string> = {};

        if (search) params.search = search;
        if (region) params.region = region;
        if (highRiskOnly) params.risk_score_min = '70';
        if (flaggedOnly) params.is_flagged = 'true';

        // Sort parameter
        if (sortBy === 'awarded') params.ordering = '-total_awarded_amount';
        if (sortBy === 'contracts') params.ordering = '-total_contracts';
        if (sortBy === 'risk') params.ordering = '-risk_score';

        const [providersData, statsData] = await Promise.all([
          api.getProviders(params),
          api.getProviderStats(),
        ]);

        setData(providersData);
        setStats(statsData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load providers');
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, [search, region, highRiskOnly, flaggedOnly, sortBy]);

  if (loading && !data) {
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
        <h1 className="text-3xl font-bold text-gray-900">Providers</h1>
        <p className="mt-2 text-gray-600">
          Browse and analyze public contract suppliers and service providers
        </p>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-6">
          <div className="card">
            <p className="text-sm text-gray-600 mb-1">Total Providers</p>
            <p className="text-2xl font-bold text-gray-900">{stats.total_providers}</p>
          </div>
          <div className="card">
            <p className="text-sm text-gray-600 mb-1">Total Contracts</p>
            <p className="text-2xl font-bold text-gray-900">
              {stats.total_contracts.toLocaleString()}
            </p>
          </div>
          <div className="card">
            <p className="text-sm text-gray-600 mb-1">Total Awarded</p>
            <p className="text-2xl font-bold text-blue-600">
              {formatCurrency(stats.total_awarded)}
            </p>
          </div>
          <div className="card">
            <p className="text-sm text-gray-600 mb-1">High Risk</p>
            <p className="text-2xl font-bold text-red-600">{stats.high_risk_count}</p>
          </div>
          <div className="card">
            <p className="text-sm text-gray-600 mb-1">Flagged</p>
            <p className="text-2xl font-bold text-orange-600">{stats.flagged_count}</p>
          </div>
          <div className="card">
            <p className="text-sm text-gray-600 mb-1">Avg Success Rate</p>
            <p className="text-2xl font-bold text-green-600">
              {(typeof stats.avg_success_rate === 'string'
                ? parseFloat(stats.avg_success_rate)
                : stats.avg_success_rate).toFixed(1)}%
            </p>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="card">
        <form className="space-y-4">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {/* Search */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Search
              </label>
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Provider name or tax ID..."
                className="input"
              />
            </div>

            {/* Region */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Region
              </label>
              <input
                type="text"
                value={region}
                onChange={(e) => setRegion(e.target.value)}
                placeholder="e.g., Madrid, Cataluña"
                className="input"
              />
            </div>

            {/* Sort */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Sort By
              </label>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as 'awarded' | 'contracts' | 'risk')}
                className="input"
              >
                <option value="awarded">Total Awarded (High to Low)</option>
                <option value="contracts">Contracts (High to Low)</option>
                <option value="risk">Risk Score (High to Low)</option>
              </select>
            </div>

            {/* Quick Filters */}
            <div className="flex flex-col justify-end space-y-2">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={highRiskOnly}
                  onChange={(e) => setHighRiskOnly(e.target.checked)}
                  className="rounded border-gray-300 text-primary-600"
                />
                <span className="ml-2 text-sm text-gray-700">High Risk Only</span>
              </label>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={flaggedOnly}
                  onChange={(e) => setFlaggedOnly(e.target.checked)}
                  className="rounded border-gray-300 text-primary-600"
                />
                <span className="ml-2 text-sm text-gray-700">Flagged Only</span>
              </label>
            </div>
          </div>

          <div className="flex gap-2">
            <button type="button" className="btn btn-primary">
              Apply Filters
            </button>
            <button
              type="button"
              onClick={() => {
                setSearch('');
                setRegion('');
                setHighRiskOnly(false);
                setFlaggedOnly(false);
              }}
              className="btn btn-secondary"
            >
              Clear
            </button>
          </div>
        </form>
      </div>

      {/* Results */}
      <div className="card">
        <div className="mb-4 flex items-center justify-between">
          <p className="text-sm text-gray-700">
            {data?.count || 0} provider(s) found
          </p>
        </div>

        {!data?.results.length ? (
          <p className="text-center py-12 text-gray-500">
            No providers found matching your filters
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Tax ID</th>
                  <th>Region</th>
                  <th>Contracts</th>
                  <th>Total Awarded</th>
                  <th>Risk</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {data.results.map((provider) => (
                  <tr
                    key={provider.id}
                    className="hover:bg-blue-50 transition-colors cursor-pointer"
                    onClick={() => router.push(`/providers/${provider.id}`)}
                  >
                    <td className="text-primary-600 hover:text-primary-700 font-medium">
                      {truncate(provider.name, 50)}
                    </td>
                    <td className="text-gray-700">{provider.tax_id}</td>
                    <td className="text-gray-700">{provider.region || '—'}</td>
                    <td className="text-gray-900 font-medium">
                      {provider.total_contracts}
                    </td>
                    <td className="text-gray-900 font-medium text-blue-600">
                      {formatCurrency(provider.total_awarded_amount)}
                    </td>
                    <td>
                      {provider.risk_score !== null && provider.risk_score !== undefined ? (
                        <RiskBadge score={provider.risk_score} showLabel={false} />
                      ) : (
                        <span className="text-gray-400">—</span>
                      )}
                    </td>
                    <td>
                      {provider.is_flagged && (
                        <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-red-100 text-red-800">
                          Flagged
                        </span>
                      )}
                      {!provider.is_flagged && (
                        <span className="text-sm text-gray-500">Active</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Links */}
      <div className="flex gap-4">
        <Link href="/analytics" className="text-blue-600 hover:text-blue-700">
          ← Back to Analytics
        </Link>
        <Link href="/contracts" className="text-blue-600 hover:text-blue-700">
          View Contracts →
        </Link>
      </div>
    </div>
  );
}

export default function ProvidersPage() {
  return (
    <Suspense fallback={<Loading />}>
      <ProvidersContent />
    </Suspense>
  );
}

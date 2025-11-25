/**
 * Providers Page
 *
 * Browse and search healthcare providers
 */

'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api, Provider, PaginatedResponse } from '@/lib/api';
import { Loading } from '@/components/Loading';
import { RiskBadge } from '@/components/RiskBadge';

export default function ProvidersPage() {
  const [data, setData] = useState<PaginatedResponse<Provider> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [flaggedOnly, setFlaggedOnly] = useState(false);

  useEffect(() => {
    async function loadProviders() {
      try {
        setLoading(true);
        const params: Record<string, string> = {};

        if (search) {
          params.search = search;
        }

        if (flaggedOnly) {
          params.is_flagged = 'true';
        }

        const response = await api.getProviders(params);
        setData(response);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load providers');
      } finally {
        setLoading(false);
      }
    }

    loadProviders();
  }, [search, flaggedOnly]);

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
          Browse and analyze contractor profiles and performance
        </p>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="search" className="block text-sm font-medium text-gray-700 mb-2">
              Search
            </label>
            <input
              id="search"
              type="text"
              placeholder="Search by name or tax ID..."
              className="input"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          <div className="flex items-end">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={flaggedOnly}
                onChange={(e) => setFlaggedOnly(e.target.checked)}
                className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              />
              <span className="text-sm font-medium text-gray-700">Flagged Providers Only</span>
            </label>
          </div>
        </div>
      </div>

      {/* Results */}
      <div className="card">
        <div className="mb-4">
          <p className="text-sm text-gray-700">
            {data?.count || 0} provider(s) found
          </p>
        </div>

        {!data?.results.length ? (
          <p className="text-center py-12 text-gray-500">
            No providers found matching your criteria
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="table">
              <thead>
                <tr>
                  <th>Provider</th>
                  <th>Tax ID</th>
                  <th>Risk Score</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {data.results.map((provider) => (
                  <tr key={provider.id}>
                    <td>
                      <div className="font-medium text-gray-900">{provider.name}</div>
                    </td>
                    <td>
                      <span className="font-mono text-sm text-gray-600">{provider.tax_id}</span>
                    </td>
                    <td>
                      {provider.risk_score ? (
                        <RiskBadge score={provider.risk_score} />
                      ) : (
                        <span className="text-gray-400 text-sm">Not analyzed</span>
                      )}
                    </td>
                    <td>
                      {provider.is_flagged && (
                        <span className="badge bg-red-100 text-red-800">Flagged</span>
                      )}
                    </td>
                    <td>
                      <Link
                        href={`/providers/${provider.id}`}
                        className="text-primary-600 hover:text-primary-700 font-medium"
                      >
                        View Details
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

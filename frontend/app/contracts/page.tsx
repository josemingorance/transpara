/**
 * Contracts List Page
 *
 * Browse and filter public contracts
 */

'use client';

import { useEffect, useState, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { api, Contract, PaginatedResponse } from '@/lib/api';
import { RiskBadge } from '@/components/RiskBadge';
import { Loading } from '@/components/Loading';
import {
  formatCurrency,
  formatDate,
  truncate,
  getStatusBadgeClass,
  getStatusLabel,
  getContractTypeLabel,
} from '@/lib/utils';

function ContractsContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [data, setData] = useState<PaginatedResponse<Contract> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [search, setSearch] = useState(searchParams.get('search') || '');
  const [region, setRegion] = useState(searchParams.get('region') || '');
  const [contractType, setContractType] = useState(searchParams.get('contract_type') || '');
  const [highRisk, setHighRisk] = useState(searchParams.get('high_risk') === 'true');
  const [isOverpriced, setIsOverpriced] = useState(searchParams.get('is_overpriced') === 'true');

  useEffect(() => {
    async function loadContracts() {
      try {
        setLoading(true);
        const params: Record<string, string> = {};

        if (search) params.search = search;
        if (region) params.region = region;
        if (contractType) params.contract_type = contractType;
        if (highRisk) params.high_risk = 'true';
        if (isOverpriced) params.is_overpriced = 'true';

        const response = await api.getContracts(params);
        setData(response);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load contracts');
      } finally {
        setLoading(false);
      }
    }

    loadContracts();
  }, [search, region, contractType, highRisk, isOverpriced]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    // Trigger reload with new filters
  };

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
        <h1 className="text-3xl font-bold text-gray-900">Contracts</h1>
        <p className="mt-2 text-gray-600">
          Browse and analyze public procurement contracts
        </p>
      </div>

      {/* Filters */}
      <div className="card">
        <form onSubmit={handleSearch} className="space-y-4">
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
                placeholder="Contract ID, title..."
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
                placeholder="e.g., Madrid"
                className="input"
              />
            </div>

            {/* Contract Type */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Type
              </label>
              <select
                value={contractType}
                onChange={(e) => setContractType(e.target.value)}
                className="input"
              >
                <option value="">All Types</option>
                <option value="WORKS">Works</option>
                <option value="SERVICES">Services</option>
                <option value="SUPPLIES">Supplies</option>
                <option value="MIXED">Mixed</option>
                <option value="OTHER">Other</option>
              </select>
            </div>

            {/* Quick Filters */}
            <div className="flex flex-col justify-end space-y-2">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={highRisk}
                  onChange={(e) => setHighRisk(e.target.checked)}
                  className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                />
                <span className="ml-2 text-sm text-gray-700">High Risk Only</span>
              </label>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={isOverpriced}
                  onChange={(e) => setIsOverpriced(e.target.checked)}
                  className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                />
                <span className="ml-2 text-sm text-gray-700">Overpriced Only</span>
              </label>
            </div>
          </div>

          <div className="flex gap-2">
            <button type="submit" className="btn btn-primary">
              Apply Filters
            </button>
            <button
              type="button"
              onClick={() => {
                setSearch('');
                setRegion('');
                setContractType('');
                setHighRisk(false);
                setIsOverpriced(false);
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
            {data?.count || 0} contract(s) found
          </p>
        </div>

        {!data?.results.length ? (
          <p className="text-center py-12 text-gray-500">
            No contracts found matching your filters
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Title</th>
                  <th>Type</th>
                  <th>Authority</th>
                  <th>Budget</th>
                  <th>Risk</th>
                  <th>Status</th>
                  <th>Date</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {data.results.map((contract) => (
                  <tr key={contract.id}>
                    <td>
                      <Link
                        href={`/contracts/${contract.id}`}
                        className="text-primary-600 hover:text-primary-700 font-medium"
                      >
                        {contract.external_id}
                      </Link>
                    </td>
                    <td className="max-w-md">
                      <div className="font-medium text-gray-900">
                        {truncate(contract.title, 80)}
                      </div>
                      {contract.is_overpriced && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800 mt-1">
                          Overpriced
                        </span>
                      )}
                    </td>
                    <td>
                      <span className="text-sm text-gray-600">
                        {getContractTypeLabel(contract.contract_type)}
                      </span>
                    </td>
                    <td className="text-gray-500 max-w-xs">
                      {truncate(contract.contracting_authority, 30)}
                    </td>
                    <td className="text-gray-900 font-medium">
                      {formatCurrency(contract.budget)}
                    </td>
                    <td>
                      <RiskBadge score={contract.risk_score} showLabel={false} />
                    </td>
                    <td>
                      <span className={`badge ${getStatusBadgeClass(contract.status)}`}>
                        {getStatusLabel(contract.status)}
                      </span>
                    </td>
                    <td className="text-gray-500 text-sm">
                      {formatDate(contract.publication_date)}
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

export default function ContractsPage() {
  return (
    <Suspense fallback={<Loading />}>
      <ContractsContent />
    </Suspense>
  );
}

/**
 * Contracts Viewer Component
 *
 * Enhanced view for displaying contracts with filtering and quick access.
 * Can be used in a modal or dedicated page to view contracts by:
 * - Date (from TemporalHeatmap)
 * - Region (from SpainGeographicMap)
 * - Municipality (from SpainGeographicMap)
 */

'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { api, Contract, PaginatedResponse } from '@/lib/api';
import { RiskBadge } from './RiskBadge';
import {
  formatCurrency,
  formatDate,
  truncate,
  getStatusBadgeClass,
  getStatusLabel,
  getContractTypeLabel,
} from '@/lib/utils';

interface ContractsViewerProps {
  filters?: {
    date?: string;
    region?: string;
    municipality?: string;
  };
  title?: string;
}

export const ContractsViewer: React.FC<ContractsViewerProps> = ({
  filters = {},
  title = 'Contracts',
}) => {
  const [data, setData] = useState<PaginatedResponse<Contract> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<'date' | 'budget' | 'risk'>('date');

  useEffect(() => {
    async function loadContracts() {
      try {
        setLoading(true);
        const params: Record<string, string> = {};

        if (filters.date) {
          params.publication_date = filters.date;
        }
        if (filters.region) {
          params.region = filters.region;
        }
        if (filters.municipality) {
          params.municipality = filters.municipality;
        }

        const response = await api.getContracts(params);
        setData(response);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load contracts');
      } finally {
        setLoading(false);
      }
    }

    loadContracts();
  }, [filters]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <p className="text-gray-500">Loading contracts...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-700 text-sm">Error: {error}</p>
      </div>
    );
  }

  if (!data || data.results.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">No contracts found</p>
        {filters.date && (
          <p className="text-sm text-gray-400 mt-2">
            No contracts published on {filters.date}
          </p>
        )}
        {filters.region && (
          <p className="text-sm text-gray-400 mt-2">
            No contracts in {filters.region}
          </p>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header with filter info */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-gray-900">{title}</h2>
          <p className="text-sm text-gray-600 mt-1">
            {data.count} contract(s) found
          </p>
        </div>
        <div className="text-sm text-gray-500">
          {filters.date && <span className="badge badge-info">Date: {filters.date}</span>}
          {filters.region && <span className="badge badge-info">Region: {filters.region}</span>}
          {filters.municipality && (
            <span className="badge badge-info">Municipality: {filters.municipality}</span>
          )}
        </div>
      </div>

      {/* Contracts Grid - Card view for better visibility */}
      <div className="grid grid-cols-1 gap-4">
        {data.results.map((contract) => (
          <Link
            key={contract.id}
            href={`/contracts/${contract.id}`}
            className="block card hover:shadow-lg hover:border-blue-200 transition-all"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="font-semibold text-gray-900 text-sm">
                    {truncate(contract.title, 100)}
                  </h3>
                  {/* Risk badge */}
                  <RiskBadge score={contract.risk_score} showLabel={false} />
                </div>

                <p className="text-xs text-gray-500 mb-3">
                  ID: {contract.external_id}
                </p>

                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-gray-500 text-xs">Type</p>
                    <p className="text-gray-900 font-medium">
                      {getContractTypeLabel(contract.contract_type)}
                    </p>
                  </div>
                  <div>
                    <p className="text-gray-500 text-xs">Authority</p>
                    <p className="text-gray-900 font-medium">
                      {truncate(contract.contracting_authority, 40)}
                    </p>
                  </div>
                  <div>
                    <p className="text-gray-500 text-xs">Budget</p>
                    <p className="text-gray-900 font-semibold text-blue-600">
                      {formatCurrency(contract.budget)}
                    </p>
                  </div>
                  <div>
                    <p className="text-gray-500 text-xs">Published</p>
                    <p className="text-gray-900 font-medium">
                      {formatDate(contract.publication_date)}
                    </p>
                  </div>
                </div>
              </div>

              {/* Status badge */}
              <div className="ml-4 flex-shrink-0">
                <span className={`badge ${getStatusBadgeClass(contract.status)}`}>
                  {getStatusLabel(contract.status)}
                </span>
              </div>
            </div>

            {/* Arrow indicating clickability */}
            <div className="mt-3 text-xs text-blue-600 font-medium">
              View Details →
            </div>
          </Link>
        ))}
      </div>

      {/* Pagination info */}
      {data.count > data.results.length && (
        <div className="text-center py-4">
          <p className="text-sm text-gray-500">
            Showing {data.results.length} of {data.count} contracts
          </p>
          <Link href="/contracts" className="text-blue-600 hover:text-blue-700 text-sm mt-2 inline-block">
            View all contracts →
          </Link>
        </div>
      )}
    </div>
  );
};

export default ContractsViewer;

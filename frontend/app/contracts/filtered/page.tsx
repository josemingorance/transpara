/**
 * Filtered Contracts Page
 *
 * Access contracts from:
 * - Temporal Heatmap (by date)
 * - Geographic Map (by region/municipality)
 *
 * Query params:
 * - ?date=YYYY-MM-DD
 * - ?region=Region+Name
 * - ?municipality=City+Name
 */

'use client';

import { useSearchParams } from 'next/navigation';
import { Suspense } from 'react';
import Link from 'next/link';
import { ContractsViewer } from '@/components/ContractsViewer';
import { Loading } from '@/components/Loading';

function FilteredContractsContent() {
  const searchParams = useSearchParams();
  const date = searchParams.get('date') || undefined;
  const region = searchParams.get('region') || undefined;
  const municipality = searchParams.get('municipality') || undefined;

  const hasFilters = date || region || municipality;

  let pageTitle = 'Contracts';
  if (date) pageTitle = `Contracts from ${date}`;
  if (region) pageTitle = `Contracts in ${region}`;
  if (municipality) pageTitle = `Contracts in ${municipality}`;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <Link href="/analytics" className="text-sm text-primary-600 hover:text-primary-700 mb-2 inline-block">
          ← Back to Analytics
        </Link>
        <h1 className="text-3xl font-bold text-gray-900">{pageTitle}</h1>
        <p className="mt-2 text-gray-600">
          {hasFilters
            ? 'Filtered contracts from your analytics dashboard'
            : 'No filters applied'}
        </p>
      </div>

      {/* Main Content */}
      {hasFilters ? (
        <div className="card">
          <ContractsViewer
            filters={{ date, region, municipality }}
            title={pageTitle}
          />
        </div>
      ) : (
        <div className="card text-center py-12">
          <p className="text-gray-500 mb-4">No filters applied</p>
          <Link href="/analytics" className="text-blue-600 hover:text-blue-700">
            Go back to analytics dashboard
          </Link>
        </div>
      )}

      {/* Links to other pages */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <Link
          href="/contracts"
          className="card text-center py-6 hover:shadow-lg hover:border-blue-200 transition-all"
        >
          <p className="text-gray-600 mb-2">📋 View All Contracts</p>
          <p className="text-sm text-gray-500">Browse and search all contracts with filters</p>
        </Link>
        <Link
          href="/analytics"
          className="card text-center py-6 hover:shadow-lg hover:border-blue-200 transition-all"
        >
          <p className="text-gray-600 mb-2">📊 Back to Analytics</p>
          <p className="text-sm text-gray-500">View temporal heatmap and geographic distribution</p>
        </Link>
      </div>
    </div>
  );
}

export default function FilteredContractsPage() {
  return (
    <Suspense fallback={<Loading />}>
      <FilteredContractsContent />
    </Suspense>
  );
}

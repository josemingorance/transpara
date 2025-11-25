/**
 * Contract Detail Page
 *
 * Displays comprehensive contract information and risk analysis
 */

'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { api, ContractDetail } from '@/lib/api';
import { RiskBadge } from '@/components/RiskBadge';
import { Loading } from '@/components/Loading';
import {
  formatCurrency,
  formatDate,
  formatPercentage,
  getStatusBadgeClass,
  getStatusLabel,
  getContractTypeLabel,
} from '@/lib/utils';

export default function ContractDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const [contract, setContract] = useState<ContractDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadContract() {
      try {
        setLoading(true);
        const data = await api.getContract(parseInt(id));
        setContract(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load contract');
      } finally {
        setLoading(false);
      }
    }

    loadContract();
  }, [id]);

  if (loading) {
    return <Loading />;
  }

  if (error || !contract) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600">Error: {error || 'Contract not found'}</p>
        <Link href="/contracts" className="mt-4 btn btn-primary">
          Back to Contracts
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <Link href="/contracts" className="text-sm text-primary-600 hover:text-primary-700 mb-2 inline-block">
          ← Back to Contracts
        </Link>
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{contract.title}</h1>
            <p className="mt-2 text-gray-600">
              {contract.external_id} • {getContractTypeLabel(contract.contract_type)}
            </p>
          </div>
          <span className={`badge ${getStatusBadgeClass(contract.status)}`}>
            {getStatusLabel(contract.status)}
          </span>
        </div>
      </div>

      {/* Risk Overview */}
      <div className="card bg-gradient-to-r from-red-50 to-orange-50 border-red-200">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Risk Analysis</h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <p className="text-sm text-gray-600 mb-1">Overall Risk</p>
            <RiskBadge score={contract.risk_score} size="lg" />
          </div>
          <div>
            <p className="text-sm text-gray-600 mb-1">Corruption Risk</p>
            <RiskBadge score={contract.corruption_risk} size="lg" />
          </div>
          <div>
            <p className="text-sm text-gray-600 mb-1">Delay Risk</p>
            <RiskBadge score={contract.delay_risk} size="lg" />
          </div>
          <div>
            <p className="text-sm text-gray-600 mb-1">Financial Risk</p>
            <RiskBadge score={contract.financial_risk} size="lg" />
          </div>
        </div>

        {contract.analyzed_at && (
          <p className="mt-4 text-sm text-gray-600">
            Last analyzed: {formatDate(contract.analyzed_at)}
          </p>
        )}
      </div>

      {/* Basic Information */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Contract Details</h2>
          <dl className="space-y-3">
            <div>
              <dt className="text-sm font-medium text-gray-500">Budget</dt>
              <dd className="mt-1 text-lg font-semibold text-gray-900">
                {formatCurrency(contract.budget)}
              </dd>
            </div>

            {contract.awarded_amount && (
              <div>
                <dt className="text-sm font-medium text-gray-500">Awarded Amount</dt>
                <dd className="mt-1 text-lg font-semibold text-gray-900">
                  {formatCurrency(contract.awarded_amount)}
                  {contract.overpricing_percentage && (
                    <span className={`ml-2 text-sm ${parseFloat(contract.overpricing_percentage) > 0 ? 'text-red-600' : 'text-green-600'}`}>
                      ({parseFloat(contract.overpricing_percentage) > 0 ? '+' : ''}
                      {formatPercentage(contract.overpricing_percentage)})
                    </span>
                  )}
                </dd>
              </div>
            )}

            <div>
              <dt className="text-sm font-medium text-gray-500">Procedure Type</dt>
              <dd className="mt-1 text-sm text-gray-900">{contract.procedure_type}</dd>
            </div>

            <div>
              <dt className="text-sm font-medium text-gray-500">Source</dt>
              <dd className="mt-1 text-sm text-gray-900">{contract.source_platform}</dd>
            </div>
          </dl>
        </div>

        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Timeline</h2>
          <dl className="space-y-3">
            <div>
              <dt className="text-sm font-medium text-gray-500">Publication Date</dt>
              <dd className="mt-1 text-sm text-gray-900">
                {formatDate(contract.publication_date)}
              </dd>
            </div>

            <div>
              <dt className="text-sm font-medium text-gray-500">Deadline</dt>
              <dd className="mt-1 text-sm text-gray-900">
                {formatDate(contract.deadline_date)}
              </dd>
            </div>

            {contract.award_date && (
              <div>
                <dt className="text-sm font-medium text-gray-500">Award Date</dt>
                <dd className="mt-1 text-sm text-gray-900">
                  {formatDate(contract.award_date)}
                </dd>
              </div>
            )}
          </dl>

          {/* Flags */}
          <div className="mt-4 flex flex-wrap gap-2">
            {contract.is_overpriced && (
              <span className="badge badge-danger">Overpriced</span>
            )}
            {contract.has_amendments && (
              <span className="badge badge-warning">Has Amendments</span>
            )}
            {contract.has_delays && (
              <span className="badge badge-warning">Has Delays</span>
            )}
            {contract.has_high_risk && (
              <span className="badge badge-danger">High Risk</span>
            )}
          </div>
        </div>
      </div>

      {/* Parties */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Contracting Authority</h2>
          <p className="text-gray-900 font-medium">{contract.contracting_authority}</p>
          <div className="mt-4 text-sm text-gray-600">
            <p>{contract.region}</p>
            {contract.province && <p>{contract.province}</p>}
            {contract.municipality && <p>{contract.municipality}</p>}
          </div>
        </div>

        {contract.awarded_to && (
          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Awarded To</h2>
            <Link
              href={`/providers/${contract.awarded_to.id}`}
              className="text-primary-600 hover:text-primary-700 font-medium"
            >
              {contract.awarded_to.name}
            </Link>
            <p className="text-sm text-gray-600 mt-1">{contract.awarded_to.tax_id}</p>
            {contract.awarded_to.risk_score && (
              <div className="mt-4">
                <p className="text-sm text-gray-600 mb-1">Provider Risk Score</p>
                <RiskBadge score={contract.awarded_to.risk_score} />
              </div>
            )}
          </div>
        )}
      </div>

      {/* Description */}
      {contract.description && (
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Description</h2>
          <p className="text-gray-700 whitespace-pre-wrap">{contract.description}</p>
        </div>
      )}

      {/* Amendments */}
      {contract.amendments && contract.amendments.length > 0 && (
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Amendments ({contract.amendments.length})
          </h2>
          <div className="space-y-4">
            {contract.amendments.map((amendment) => (
              <div key={amendment.id} className="border-l-4 border-yellow-400 pl-4 py-2">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="font-medium text-gray-900">{amendment.amendment_type}</p>
                    <p className="text-sm text-gray-600 mt-1">{amendment.description}</p>
                    {amendment.reason && (
                      <p className="text-sm text-gray-500 mt-1">Reason: {amendment.reason}</p>
                    )}
                  </div>
                  <span className="text-sm text-gray-500">{formatDate(amendment.amendment_date)}</span>
                </div>
                <div className="mt-2 flex gap-4 text-sm">
                  <span className="text-gray-600">
                    Previous: {formatCurrency(amendment.previous_amount)}
                  </span>
                  <span className="text-gray-600">→</span>
                  <span className="text-gray-900 font-medium">
                    New: {formatCurrency(amendment.new_amount)}
                  </span>
                  <span className={`font-medium ${parseFloat(amendment.amount_change_percentage) > 0 ? 'text-red-600' : 'text-green-600'}`}>
                    ({parseFloat(amendment.amount_change_percentage) > 0 ? '+' : ''}
                    {formatPercentage(amendment.amount_change_percentage)})
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* External Link */}
      {contract.source_url && (
        <div className="card">
          <a
            href={contract.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary-600 hover:text-primary-700 flex items-center"
          >
            View on {contract.source_platform} →
          </a>
        </div>
      )}
    </div>
  );
}

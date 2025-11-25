/**
 * Provider Detail Page
 *
 * View detailed information about a specific provider
 */

'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api, ProviderDetail, Contract, Alert, PaginatedResponse } from '@/lib/api';
import { Loading } from '@/components/Loading';
import { RiskBadge } from '@/components/RiskBadge';
import {
  formatCurrency,
  formatDate,
  formatPercentage,
  getAlertSeverityClass,
  getStatusBadgeClass,
  getStatusLabel,
} from '@/lib/utils';

interface PageProps {
  params: {
    id: string;
  };
}

export default function ProviderDetailPage({ params }: PageProps) {
  const [provider, setProvider] = useState<ProviderDetail | null>(null);
  const [contracts, setContracts] = useState<PaginatedResponse<Contract> | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadProvider() {
      try {
        setLoading(true);
        const [providerData, contractsData, alertsData] = await Promise.all([
          api.getProvider(parseInt(params.id)),
          api.getProviderContracts(parseInt(params.id)),
          api.getProviderAlerts(parseInt(params.id)),
        ]);

        setProvider(providerData);
        setContracts(contractsData);
        setAlerts(alertsData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load provider');
      } finally {
        setLoading(false);
      }
    }

    loadProvider();
  }, [params.id]);

  if (loading) {
    return <Loading />;
  }

  if (error || !provider) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600">Error: {error || 'Provider not found'}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center gap-3 mb-2">
          <h1 className="text-3xl font-bold text-gray-900">{provider.name}</h1>
          {provider.is_flagged && (
            <span className="badge bg-red-100 text-red-800">Flagged</span>
          )}
        </div>
        <p className="text-gray-600">Tax ID: {provider.tax_id}</p>
      </div>

      {/* Risk Score */}
      {provider.risk_score && (
        <div className="card">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Risk Assessment</h2>
          <div className="flex items-center gap-4">
            <RiskBadge score={provider.risk_score} size="lg" />
            {provider.flag_reason && (
              <div className="flex-1">
                <p className="text-sm text-gray-600">
                  <span className="font-medium">Flag Reason:</span> {provider.flag_reason}
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Company Information */}
      <div className="card">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Company Information</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-gray-600">Legal Name</p>
            <p className="font-medium text-gray-900">{provider.legal_name || 'N/A'}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Industry</p>
            <p className="font-medium text-gray-900">{provider.industry || 'N/A'}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Company Size</p>
            <p className="font-medium text-gray-900">{provider.company_size || 'N/A'}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Founded Year</p>
            <p className="font-medium text-gray-900">{provider.founded_year || 'N/A'}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Address</p>
            <p className="font-medium text-gray-900">
              {provider.address || 'N/A'}
              {provider.city && `, ${provider.city}`}
              {provider.postal_code && ` ${provider.postal_code}`}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Region</p>
            <p className="font-medium text-gray-900">{provider.region || 'N/A'}</p>
          </div>
          {provider.phone && (
            <div>
              <p className="text-sm text-gray-600">Phone</p>
              <p className="font-medium text-gray-900">{provider.phone}</p>
            </div>
          )}
          {provider.email && (
            <div>
              <p className="text-sm text-gray-600">Email</p>
              <p className="font-medium text-gray-900">{provider.email}</p>
            </div>
          )}
          {provider.website && (
            <div>
              <p className="text-sm text-gray-600">Website</p>
              <a
                href={provider.website}
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary-600 hover:text-primary-700"
              >
                {provider.website}
              </a>
            </div>
          )}
        </div>
      </div>

      {/* Contract Statistics */}
      <div className="card">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Contract Statistics</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <p className="text-sm text-gray-600">Total Contracts</p>
            <p className="text-2xl font-bold text-gray-900">{provider.total_contracts}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Total Awarded Amount</p>
            <p className="text-2xl font-bold text-gray-900">
              {formatCurrency(provider.total_awarded_amount)}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Average Contract</p>
            <p className="text-2xl font-bold text-gray-900">
              {formatCurrency(provider.avg_contract_amount)}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Success Rate</p>
            <p className="text-2xl font-bold text-gray-900">
              {formatPercentage(provider.success_rate)}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Years Active</p>
            <p className="text-2xl font-bold text-gray-900">{provider.years_active || 'N/A'}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Activity Period</p>
            <p className="text-sm font-medium text-gray-900">
              {formatDate(provider.first_contract_date)} - {formatDate(provider.last_contract_date)}
            </p>
          </div>
        </div>
      </div>

      {/* Active Alerts */}
      {alerts.length > 0 && (
        <div className="card">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Active Alerts ({alerts.filter(a => !a.is_resolved).length})
          </h2>
          <div className="space-y-3">
            {alerts
              .filter(alert => !alert.is_resolved)
              .map((alert) => (
                <div
                  key={alert.id}
                  className="border border-gray-200 rounded-lg p-4"
                >
                  <div className="flex items-start gap-3">
                    <span className={`badge ${getAlertSeverityClass(alert.severity)}`}>
                      {alert.severity}
                    </span>
                    <div className="flex-1">
                      <h3 className="font-semibold text-gray-900">{alert.title}</h3>
                      <p className="text-sm text-gray-600 mt-1">{alert.description}</p>
                      <p className="text-xs text-gray-500 mt-2">{alert.alert_type}</p>
                    </div>
                  </div>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* Contracts List */}
      <div className="card">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          Contracts ({contracts?.count || 0})
        </h2>

        {!contracts?.results.length ? (
          <p className="text-center py-8 text-gray-500">No contracts found</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="table">
              <thead>
                <tr>
                  <th>Contract</th>
                  <th>Status</th>
                  <th>Budget</th>
                  <th>Risk</th>
                  <th>Publication Date</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {contracts.results.map((contract) => (
                  <tr key={contract.id}>
                    <td>
                      <div className="font-medium text-gray-900">{contract.title}</div>
                      <div className="text-sm text-gray-500">{contract.contracting_authority}</div>
                    </td>
                    <td>
                      <span className={`badge ${getStatusBadgeClass(contract.status)}`}>
                        {getStatusLabel(contract.status)}
                      </span>
                    </td>
                    <td className="font-medium">{formatCurrency(contract.budget)}</td>
                    <td>
                      {contract.risk_score ? (
                        <RiskBadge score={contract.risk_score} />
                      ) : (
                        <span className="text-gray-400 text-sm">N/A</span>
                      )}
                    </td>
                    <td>{formatDate(contract.publication_date)}</td>
                    <td>
                      <Link
                        href={`/contracts/${contract.id}`}
                        className="text-primary-600 hover:text-primary-700 font-medium"
                      >
                        View
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

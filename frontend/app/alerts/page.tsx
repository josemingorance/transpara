/**
 * Alerts Page
 *
 * View and manage system alerts
 */

'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api, Alert, PaginatedResponse } from '@/lib/api';
import { Loading } from '@/components/Loading';
import { formatDateTime, getAlertSeverityClass, truncate } from '@/lib/utils';

export default function AlertsPage() {
  const [data, setData] = useState<PaginatedResponse<Alert> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<'all' | 'unresolved' | 'critical'>('unresolved');

  useEffect(() => {
    async function loadAlerts() {
      try {
        setLoading(true);
        let response;

        if (filter === 'unresolved') {
          response = await api.getUnresolvedAlerts();
        } else if (filter === 'critical') {
          const criticalAlerts = await api.getCriticalAlerts();
          response = {
            count: criticalAlerts.length,
            next: null,
            previous: null,
            results: criticalAlerts,
          };
        } else {
          response = await api.getAlerts();
        }

        setData(response);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load alerts');
      } finally {
        setLoading(false);
      }
    }

    loadAlerts();
  }, [filter]);

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
        <h1 className="text-3xl font-bold text-gray-900">Alerts</h1>
        <p className="mt-2 text-gray-600">
          Review and manage risk alerts for contracts and providers
        </p>
      </div>

      {/* Filters */}
      <div className="flex gap-2">
        <button
          onClick={() => setFilter('all')}
          className={`btn ${filter === 'all' ? 'btn-primary' : 'btn-secondary'}`}
        >
          All Alerts
        </button>
        <button
          onClick={() => setFilter('unresolved')}
          className={`btn ${filter === 'unresolved' ? 'btn-primary' : 'btn-secondary'}`}
        >
          Unresolved
        </button>
        <button
          onClick={() => setFilter('critical')}
          className={`btn ${filter === 'critical' ? 'btn-primary' : 'btn-secondary'}`}
        >
          Critical
        </button>
      </div>

      {/* Results */}
      <div className="card">
        <div className="mb-4">
          <p className="text-sm text-gray-700">
            {data?.count || 0} alert(s) found
          </p>
        </div>

        {!data?.results.length ? (
          <p className="text-center py-12 text-gray-500">
            No alerts found
          </p>
        ) : (
          <div className="space-y-4">
            {data.results.map((alert) => (
              <div
                key={alert.id}
                className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className={`badge ${getAlertSeverityClass(alert.severity)}`}>
                        {alert.severity}
                      </span>
                      <span className="text-sm text-gray-500">{alert.alert_type}</span>
                      {alert.is_resolved && (
                        <span className="badge bg-green-100 text-green-800">Resolved</span>
                      )}
                    </div>

                    <h3 className="font-semibold text-gray-900">{alert.title}</h3>
                    <p className="text-sm text-gray-600 mt-1">
                      {truncate(alert.description, 150)}
                    </p>

                    <div className="mt-3 flex items-center gap-4 text-sm text-gray-500">
                      <Link
                        href={`/providers/${alert.provider}`}
                        className="text-primary-600 hover:text-primary-700"
                      >
                        {alert.provider_name} ({alert.provider_tax_id})
                      </Link>
                      <span>•</span>
                      <span>{formatDateTime(alert.created_at)}</span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

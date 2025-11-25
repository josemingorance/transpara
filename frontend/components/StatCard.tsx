/**
 * Stat Card Component
 *
 * Displays a statistic with title, value, and optional trend
 */

import { ReactNode } from 'react';
import { formatCurrency, formatNumber } from '@/lib/utils';

interface StatCardProps {
  title: string;
  value: string | number;
  icon?: ReactNode;
  trend?: {
    value: number;
    label: string;
  };
  format?: 'number' | 'currency' | 'percentage' | 'none';
  color?: 'blue' | 'green' | 'red' | 'yellow' | 'gray';
}

export function StatCard({
  title,
  value,
  icon,
  trend,
  format = 'number',
  color = 'blue'
}: StatCardProps) {
  const formatValue = () => {
    if (format === 'currency') {
      return formatCurrency(value);
    }
    if (format === 'percentage') {
      return `${value}%`;
    }
    if (format === 'number' && typeof value === 'number') {
      return formatNumber(value);
    }
    return value;
  };

  const colorClasses = {
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-green-50 text-green-600',
    red: 'bg-red-50 text-red-600',
    yellow: 'bg-yellow-50 text-yellow-600',
    gray: 'bg-gray-50 text-gray-600',
  };

  return (
    <div className="card">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="mt-2 text-3xl font-semibold text-gray-900">
            {formatValue()}
          </p>
          {trend && (
            <p className={`mt-2 text-sm ${trend.value >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {trend.value >= 0 ? '↑' : '↓'} {Math.abs(trend.value)}% {trend.label}
            </p>
          )}
        </div>
        {icon && (
          <div className={`p-3 rounded-lg ${colorClasses[color]}`}>
            {icon}
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Risk Badge Component
 *
 * Displays risk score with appropriate color coding
 */

import { getRiskLevel, getRiskBadgeClass, formatPercentage } from '@/lib/utils';

interface RiskBadgeProps {
  score: string | number | null;
  showLabel?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export function RiskBadge({ score, showLabel = true, size = 'md' }: RiskBadgeProps) {
  const { label } = getRiskLevel(score);
  const badgeClass = getRiskBadgeClass(score);

  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-0.5 text-sm',
    lg: 'px-3 py-1 text-base',
  };

  if (score === null || score === undefined) {
    return (
      <span className={`inline-flex items-center rounded-full font-medium bg-gray-100 text-gray-800 ${sizeClasses[size]}`}>
        N/A
      </span>
    );
  }

  const displayScore = typeof score === 'string' ? parseFloat(score) : score;

  return (
    <span className={`inline-flex items-center rounded-full font-medium ${badgeClass} ${sizeClasses[size]}`}>
      {displayScore.toFixed(1)}
      {showLabel && ` - ${label}`}
    </span>
  );
}

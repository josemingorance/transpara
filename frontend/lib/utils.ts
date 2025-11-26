/**
 * Utility Functions
 *
 * Common formatting and helper functions
 */

/**
 * Format a number as currency
 */
export function formatCurrency(value: string | number | undefined): string {
  if (!value) return '€0.00';

  const num = typeof value === 'string' ? parseFloat(value) : value;

  return new Intl.NumberFormat('es-ES', {
    style: 'currency',
    currency: 'EUR',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(num);
}

/**
 * Format a date string
 */
export function formatDate(dateString: string | undefined): string {
  if (!dateString) return '-';

  const date = new Date(dateString);
  return new Intl.DateTimeFormat('es-ES', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  }).format(date);
}

/**
 * Format a percentage
 */
export function formatPercentage(value: string | number | undefined): string {
  if (value === undefined || value === null) return '0%';

  const num = typeof value === 'string' ? parseFloat(value) : value;
  return `${num.toFixed(1)}%`;
}

/**
 * Truncate text to a maximum length
 */
export function truncate(text: string | undefined, maxLength: number): string {
  if (!text) return '';
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
}

/**
 * Get the label for a contract status
 */
export function getStatusLabel(status: string | undefined): string {
  if (!status) return 'Unknown';

  const labels: Record<string, string> = {
    PUBLISHED: 'Published',
    AWARDED: 'Awarded',
    CANCELLED: 'Cancelled',
    COMPLETED: 'Completed',
    IN_PROGRESS: 'In Progress',
  };

  return labels[status.toUpperCase()] || status;
}

/**
 * Get the CSS class for a contract status badge
 */
export function getStatusBadgeClass(status: string | undefined): string {
  if (!status) return 'badge-secondary';

  const classes: Record<string, string> = {
    PUBLISHED: 'badge-info',
    AWARDED: 'badge-success',
    CANCELLED: 'badge-danger',
    COMPLETED: 'badge-success',
    IN_PROGRESS: 'badge-warning',
  };

  return classes[status.toUpperCase()] || 'badge-secondary';
}

/**
 * Get the label for a contract type
 */
export function getContractTypeLabel(type: string | undefined): string {
  if (!type) return 'Unknown';

  const labels: Record<string, string> = {
    WORKS: 'Works',
    SERVICES: 'Services',
    SUPPLIES: 'Supplies',
    MIXED: 'Mixed',
    OTHER: 'Other',
  };

  return labels[type.toUpperCase()] || type;
}

/**
 * Format a number with thousand separators
 */
export function formatNumber(value: number): string {
  return new Intl.NumberFormat('es-ES').format(value);
}

/**
 * Format date and time
 */
export function formatDateTime(dateString: string | undefined): string {
  if (!dateString) return '-';

  const date = new Date(dateString);
  return new Intl.DateTimeFormat('es-ES', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
}

/**
 * Get risk level and label based on score
 */
export function getRiskLevel(score: string | number | null | undefined): {
  level: 'low' | 'medium' | 'high' | 'critical';
  label: string;
} {
  if (!score && score !== 0) {
    return { level: 'low', label: 'N/A' };
  }

  const numScore = typeof score === 'string' ? parseFloat(score) : score;

  if (numScore < 25) {
    return { level: 'low', label: 'Low' };
  } else if (numScore < 50) {
    return { level: 'medium', label: 'Medium' };
  } else if (numScore < 75) {
    return { level: 'high', label: 'High' };
  } else {
    return { level: 'critical', label: 'Critical' };
  }
}

/**
 * Get CSS class for risk badge based on score
 */
export function getRiskBadgeClass(score: string | number | null | undefined): string {
  const { level } = getRiskLevel(score);

  const classes: Record<string, string> = {
    low: 'bg-green-100 text-green-800',
    medium: 'bg-yellow-100 text-yellow-800',
    high: 'bg-orange-100 text-orange-800',
    critical: 'bg-red-100 text-red-800',
  };

  return classes[level];
}

/**
 * Get CSS class for alert severity badge
 */
export function getAlertSeverityClass(severity: string | undefined): string {
  if (!severity) return 'badge-secondary';

  const classes: Record<string, string> = {
    CRITICAL: 'bg-red-100 text-red-800',
    HIGH: 'bg-orange-100 text-orange-800',
    MEDIUM: 'bg-yellow-100 text-yellow-800',
    LOW: 'bg-blue-100 text-blue-800',
    INFO: 'bg-gray-100 text-gray-800',
  };

  return classes[severity.toUpperCase()] || 'badge-secondary';
}
/**
 * API Client (Minimal Version)
 *
 * Only uses endpoints that exist in the backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

// ============================================================================
// Types
// ============================================================================

export interface DashboardStats {
  total_contracts: number;
  total_budget: string;
  high_risk_contracts: number;
  critical_alerts: number;
  overpriced_contracts: number;
  flagged_providers: number;
  avg_risk_score: string;
  contracts_last_30_days: number;
  total_providers: number;
}

export interface Contract {
  id: number;
  external_id: string;
  title: string;
  budget: string;
  contracting_authority: string;
  publication_date: string;
  risk_score: number;
  status: string;
  contract_type: string;
}

export interface Provider {
  id: number;
  name: string;
  tax_id: string;
  risk_score?: number;
}

export interface PaginatedResponse<T> {
  count: number;
  next?: string | null;
  previous?: string | null;
  results: T[];
}

// ============================================================================
// API Client
// ============================================================================

class APIClient {
  private baseURL: string;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
  }

  private async request<T>(
    endpoint: string,
    options?: RequestInit
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;

    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(
        error.detail || error.message || `API error: ${response.status}`
      );
    }

    return response.json();
  }

  // Dashboard
  async getDashboardStats(): Promise<DashboardStats> {
    return this.request('/analytics/dashboard/');
  }

  // Contracts
  async getContracts(
    params?: Record<string, string>
  ): Promise<PaginatedResponse<Contract>> {
    let url = '/contracts/';
    if (params) {
      const queryString = new URLSearchParams(params).toString();
      url += `?${queryString}`;
    }
    return this.request(url);
  }

  // Providers
  async getProviders(
    params?: Record<string, string>
  ): Promise<PaginatedResponse<Provider>> {
    let url = '/providers/';
    if (params) {
      const queryString = new URLSearchParams(params).toString();
      url += `?${queryString}`;
    }
    return this.request(url);
  }
}

// ============================================================================
// Export
// ============================================================================

export const api = new APIClient(API_BASE_URL);

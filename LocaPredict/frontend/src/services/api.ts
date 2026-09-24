import {
  Incident,
  Forecast,
  Regime,
  Cluster,
  MLOpsStatus,
  MetricsOverview,
  FilterState,
} from '../types';
import { config } from '../config';

const API_BASE = config.apiBaseUrl;

/**
 * Robust fetch wrapper handling JSON, plain text error responses, and injecting Auth tokens
 */
async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('locapredict_token');
  const headers = new Headers(options.headers || {});
  
  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }
  
  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE}${endpoint}`;
  const response = await fetch(url, { ...options, headers });

  const contentType = response.headers.get('content-type') || '';
  const isJson = contentType.includes('application/json');

  if (!response.ok) {
    let errorDetail = `Erro HTTP ${response.status}: ${response.statusText}`;
    try {
      if (isJson) {
        const errorJson = await response.json();
        errorDetail = errorJson.detail || errorJson.message || errorDetail;
      } else {
        const textError = await response.text();
        if (textError) {
          // Truncate if long HTML
          errorDetail = textError.length > 200 ? textError.substring(0, 200) + '...' : textError;
        }
      }
    } catch (parseError) {
      // Fallback
    }
    throw new Error(errorDetail);
  }

  if (isJson) {
    return response.json() as Promise<T>;
  }
  return response.text() as unknown as Promise<T>;
}

export const apiService = {
  async getHealth() {
    return request<{ status: string; service: string; version: string; ml_engine: string; model_version: string }>('/health');
  },

  async getDemoToken(role: string = 'operator') {
    return request<{ access_token: string; token_type: string; expires_in_minutes: number; user: any }>(
      `/auth/demo-token?role=${encodeURIComponent(role)}`,
      { method: 'POST' }
    );
  },

  async getMetricsOverview(): Promise<MetricsOverview> {
    return request<MetricsOverview>('/metrics/overview');
  },

  async getIncidents(filters?: Partial<FilterState>): Promise<Incident[]> {
    const params = new URLSearchParams();
    if (filters) {
      if (filters.search) params.append('search', filters.search);
      if (filters.priority && filters.priority !== 'all') params.append('priority', filters.priority);
      if (filters.group && filters.group !== 'all') params.append('group', filters.group);
      if (filters.product && filters.product !== 'all') params.append('product', filters.product);
      if (filters.status && filters.status !== 'all') params.append('status', filters.status);
      if (filters.minRisk !== undefined) params.append('min_risk', filters.minRisk.toString());
      if (filters.maxRisk !== undefined) params.append('max_risk', filters.maxRisk.toString());
      if (filters.clusterId && filters.clusterId !== 'all') params.append('cluster_id', filters.clusterId);
      if (filters.sortBy) params.append('sort_by', filters.sortBy);
    }

    const query = params.toString() ? `?${params.toString()}` : '';
    return request<Incident[]>(`/incidents${query}`);
  },

  async getIncident(id: string): Promise<Incident> {
    return request<Incident>(`/incidents/${id}`);
  },

  async assignIncident(id: string, group: string, notes?: string): Promise<Incident> {
    return request<Incident>(`/incidents/${id}/assign`, {
      method: 'POST',
      body: JSON.stringify({ group, notes }),
    });
  },

  async escalateIncident(id: string, priority?: string, reason: string = '', targetGroup?: string): Promise<Incident> {
    return request<Incident>(`/incidents/${id}/escalate`, {
      method: 'POST',
      body: JSON.stringify({ priority, reason, target_group: targetGroup }),
    });
  },

  async notifyIncident(id: string): Promise<{ status: string; message: string }> {
    return request<{ status: string; message: string }>(`/incidents/${id}/notify`, {
      method: 'POST',
    });
  },

  async simulateIncident(): Promise<Incident> {
    return request<Incident>('/incidents/simulate', {
      method: 'POST',
    });
  },

  async getForecast(horizon: 'D+1' | 'D+7' = 'D+7'): Promise<Forecast> {
    const encodedHorizon = encodeURIComponent(horizon);
    return request<Forecast>(`/forecast?horizon=${encodedHorizon}`);
  },

  async getRegime(): Promise<Regime> {
    return request<Regime>('/regime');
  },

  async overrideRegime(regime: string): Promise<{ status: string; active_regime: string; message: string }> {
    return request<{ status: string; active_regime: string; message: string }>('/regime/override', {
      method: 'POST',
      body: JSON.stringify({ regime }),
    });
  },

  async getClusters(): Promise<Cluster[]> {
    return request<Cluster[]>('/clusters');
  },

  async getDriftAndMLOps(): Promise<MLOpsStatus> {
    return request<MLOpsStatus>('/drift');
  },

  async retrainModel(): Promise<{ status: string; model_version: string; message: string; roc_auc: number; recall: number; wape: number }> {
    return request<{ status: string; model_version: string; message: string; roc_auc: number; recall: number; wape: number }>('/models/retrain', {
      method: 'POST',
    });
  },

  async getMetadata(): Promise<{ groups: string[]; products: string[]; categories: string[]; priorities: string[] }> {
    return request<{ groups: string[]; products: string[]; categories: string[]; priorities: string[] }>('/metadata');
  },

  getExportUrl(): string {
    return `${API_BASE}/export`;
  },
};

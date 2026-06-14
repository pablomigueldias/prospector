// Prospector — preview/run de lead por CNPJ + histórico.

import { request } from './client';
import type {
  ProspectorManualRequest,
  ProspectorPreviewResponse,
  ProspectorRunResponse,
  LeadHistoryResponse,
} from '../types';

export const prospectorApi = {
  prospectorPreview(
    body: ProspectorManualRequest,
    opts?: { signal?: AbortSignal },
  ): Promise<ProspectorPreviewResponse> {
    return request<ProspectorPreviewResponse>(
      '/api/agents/prospector/preview',
      {
        method: 'POST',
        body,
        timeoutMs: 60_000,
        signal: opts?.signal,
      },
    );
  },

  prospectorRun(
    body: ProspectorManualRequest,
    opts?: { signal?: AbortSignal },
  ): Promise<ProspectorRunResponse> {
    return request<ProspectorRunResponse>('/api/agents/prospector/manual', {
      method: 'POST',
      body,
      signal: opts?.signal,
    });
  },

  prospectorHistory(limit: number = 20): Promise<LeadHistoryResponse> {
    return request<LeadHistoryResponse>(
      `/api/agents/prospector/leads?limit=${limit}`,
      { timeoutMs: 10000 },
    );
  },
};

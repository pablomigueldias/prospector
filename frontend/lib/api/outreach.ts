// Copywriter / Outreach — gerar e-mail, rascunhos em massa, follow-ups, sync.

import { request } from './client';
import type {
  CopywriterRequest,
  CopywriterResponse,
  GerarRascunhosResponse,
  GerarFollowupsRequest,
  GerarFollowupsResponse,
  SyncResponse,
  EmailHistoryResponse,
} from '../types';

export const outreachApi = {
  copywriterGerar(
    body: CopywriterRequest,
    opts?: { signal?: AbortSignal },
  ): Promise<CopywriterResponse> {
    return request<CopywriterResponse>('/api/agents/copywriter/gerar', {
      method: 'POST',
      body,
      timeoutMs: 120_000,
      signal: opts?.signal,
    });
  },

  outreachGerar(
    body: { limit?: number | null; pausa?: number },
    opts?: { signal?: AbortSignal },
  ): Promise<GerarRascunhosResponse> {
    return request<GerarRascunhosResponse>('/api/agents/outreach/gerar', {
      method: 'POST',
      body,
      timeoutMs: 600_000,
      signal: opts?.signal,
    });
  },

  outreachFollowups(
    body: GerarFollowupsRequest,
    opts?: { signal?: AbortSignal },
  ): Promise<GerarFollowupsResponse> {
    return request<GerarFollowupsResponse>('/api/agents/outreach/followups', {
      method: 'POST',
      body,
      timeoutMs: 600_000,
      signal: opts?.signal,
    });
  },

  outreachSync(opts?: { signal?: AbortSignal }): Promise<SyncResponse> {
    return request<SyncResponse>('/api/agents/outreach/sync', {
      method: 'POST',
      timeoutMs: 120_000,
      signal: opts?.signal,
    });
  },

  outreachEmails(limit: number = 50): Promise<EmailHistoryResponse> {
    return request<EmailHistoryResponse>(
      `/api/agents/outreach/emails?limit=${limit}`,
      { timeoutMs: 15_000 },
    );
  },
};

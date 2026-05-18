import { ApiError } from './types';
import type {
  Agent,
  LeadHistoryResponse,
  ProspectorManualRequest,
  ProspectorPreviewResponse,
  ProspectorRunResponse,
} from './types';

const API_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, '') ||
  'http://localhost:8000';


const DEFAULT_TIMEOUT_MS = 180_000; // 3 min

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE';
  body?: unknown;
  timeoutMs?: number;
  signal?: AbortSignal;
}

async function request<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, timeoutMs = DEFAULT_TIMEOUT_MS, signal } = opts;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
  if (signal) {
    if (signal.aborted) controller.abort();
    else signal.addEventListener('abort', () => controller.abort());
  }

  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      method,
      headers: body ? { 'Content-Type': 'application/json' } : undefined,
      body: body ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    });
  } catch (err) {
    clearTimeout(timeoutId);
    if (err instanceof DOMException && err.name === 'AbortError') {
      throw new ApiError(
        'Tempo esgotado. A API demorou mais que o esperado.',
        0,
        `Timeout de ${Math.round(timeoutMs / 1000)}s atingido.`,
      );
    }
    throw new ApiError(
      'Não consegui falar com a API. Está rodando em ' + API_URL + '?',
      0,
      err instanceof Error ? err.message : String(err),
    );
  } finally {
    clearTimeout(timeoutId);
  }

  if (!response.ok) {
    let detail: string | null = null;
    try {
      const errBody = await response.json();
      detail = errBody?.detail ?? errBody?.error ?? null;
    } catch {
    }
    throw new ApiError(
      detail || `Erro HTTP ${response.status}`,
      response.status,
      detail,
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export const api = {
  /** GET /api/health */
  healthcheck(): Promise<{ status: string; service: string }> {
    return request('/api/health', { timeoutMs: 5000 });
  },

  /** GET /api/agents — lista todos os agentes da plataforma */
  listAgents(): Promise<Agent[]> {
    return request<Agent[]>('/api/agents', { timeoutMs: 10000 });
  },

  /** GET /api/agents/{slug} — detalhe de um agente */
  getAgent(slug: string): Promise<Agent> {
    return request<Agent>(`/api/agents/${encodeURIComponent(slug)}`, {
      timeoutMs: 10000,
    });
  },

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

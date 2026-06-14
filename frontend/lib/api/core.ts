// Plataforma: health, catálogo de agentes e ferramentas de dev.

import { request } from './client';
import type { Agent } from '../types';

export const coreApi = {
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

  // ── Dev tools (só habilitado fora de produção) ──────────────────
  /** POST /api/dev/sync-prod-to-dev — copia os dados da produção pro dev.
   *  DESTRUTIVO: substitui o banco de dev inteiro. 404 em produção. */
  devSyncProdToDev(): Promise<{ ok: boolean; mensagem: string; log: string }> {
    return request('/api/dev/sync-prod-to-dev', {
      method: 'POST',
      timeoutMs: 320_000,
    });
  },
};

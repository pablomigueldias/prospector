// Agendamentos (S4) — lista os jobs e dispara on-demand. O liga/desliga e a
// hora são gravados via configApi (S3, /api/config).

import { request } from './client';
import type { Job, JobRunResult } from '../types';

export const agendamentosApi = {
  /** GET /api/agendamentos — jobs com hora e estado (lido do settings) */
  getAgendamentos(): Promise<Job[]> {
    return request<Job[]>('/api/agendamentos');
  },
  /** POST /api/agendamentos/{id}/rodar — dispara o job agora */
  rodarJob(id: string): Promise<JobRunResult> {
    return request<JobRunResult>(
      `/api/agendamentos/${encodeURIComponent(id)}/rodar`,
      { method: 'POST', timeoutMs: 60000 },
    );
  },
};

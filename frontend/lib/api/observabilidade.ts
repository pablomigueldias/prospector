// Observabilidade de IA (S2) — custos/tokens por agente e por dia.

import { request } from './client';
import type { ObsResumo } from '../types';

export const observabilidadeApi = {
  /** GET /api/observability/resumo?dias=N */
  getObservabilidade(dias = 30): Promise<ObsResumo> {
    return request<ObsResumo>(`/api/observability/resumo?dias=${dias}`);
  },
};

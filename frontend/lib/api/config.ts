// Configurações na UI (S3) — lê o catálogo e salva overrides em runtime.

import { request } from './client';
import type { ConfigItem } from '../types';

export const configApi = {
  /** GET /api/config — catálogo editável com valor efetivo, default e flag de override */
  getConfig(): Promise<ConfigItem[]> {
    return request<ConfigItem[]>('/api/config');
  },
  /** PATCH /api/config — salva mudanças (chave→valor) e devolve o catálogo atualizado */
  updateConfig(
    mudancas: Record<string, boolean | number | string>,
  ): Promise<ConfigItem[]> {
    return request<ConfigItem[]>('/api/config', {
      method: 'PATCH',
      body: { mudancas },
    });
  },
};

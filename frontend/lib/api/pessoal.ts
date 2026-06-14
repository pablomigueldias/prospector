// Área pessoal — Perfil Mestre, Vagas e Candidatura.

import { request } from './client';
import type {
  PerfilMestre,
  Vaga,
  VagaCreate,
  VagaListResponse,
  AnalisarVagaResponse,
  GerarCandidaturaResponse,
  CandidaturaEmailItem,
} from '../types';

export const pessoalApi = {
  // ── Perfil Mestre ───────────────────────────────────────────────
  /** GET /api/pessoal/perfil — perfil ativo, ou null se não houver */
  perfilGet(): Promise<PerfilMestre | null> {
    return request<PerfilMestre | null>('/api/pessoal/perfil', {
      timeoutMs: 10_000,
    });
  },

  /** PUT /api/pessoal/perfil — cria/atualiza o perfil */
  perfilSalvar(body: PerfilMestre): Promise<PerfilMestre> {
    return request<PerfilMestre>('/api/pessoal/perfil', {
      method: 'PUT',
      body,
      timeoutMs: 15_000,
    });
  },

  // ── Vagas ───────────────────────────────────────────────────────
  vagasListar(status?: string): Promise<VagaListResponse> {
    const q = status ? `?status=${encodeURIComponent(status)}` : '';
    return request<VagaListResponse>(`/api/pessoal/vagas${q}`, {
      timeoutMs: 10_000,
    });
  },

  vagaCriar(body: VagaCreate): Promise<Vaga> {
    return request<Vaga>('/api/pessoal/vagas', {
      method: 'POST',
      body,
      timeoutMs: 15_000,
    });
  },

  vagaDetalhe(id: string): Promise<Vaga> {
    return request<Vaga>(`/api/pessoal/vagas/${encodeURIComponent(id)}`, {
      timeoutMs: 10_000,
    });
  },

  vagaAtualizar(id: string, body: Partial<Vaga>): Promise<Vaga> {
    return request<Vaga>(`/api/pessoal/vagas/${encodeURIComponent(id)}`, {
      method: 'PATCH',
      body,
      timeoutMs: 10_000,
    });
  },

  vagaRemover(id: string): Promise<void> {
    return request<void>(`/api/pessoal/vagas/${encodeURIComponent(id)}`, {
      method: 'DELETE',
      timeoutMs: 10_000,
    });
  },

  vagaAnalisar(id: string): Promise<AnalisarVagaResponse> {
    return request<AnalisarVagaResponse>(
      `/api/pessoal/vagas/${encodeURIComponent(id)}/analisar`,
      { method: 'POST', timeoutMs: 120_000 },
    );
  },

  vagaGerarCandidatura(
    id: string,
    body: { gerar_carta?: boolean; instrucoes_extra?: string | null },
  ): Promise<GerarCandidaturaResponse> {
    return request<GerarCandidaturaResponse>(
      `/api/pessoal/vagas/${encodeURIComponent(id)}/candidatura`,
      { method: 'POST', body, timeoutMs: 120_000 },
    );
  },

  vagaRascunhos(id: string): Promise<CandidaturaEmailItem[]> {
    return request<CandidaturaEmailItem[]>(
      `/api/pessoal/vagas/${encodeURIComponent(id)}/rascunhos`,
      { timeoutMs: 10_000 },
    );
  },
};

// Área pessoal — Perfil Mestre, Vagas e Candidatura.

import { request } from './client';
import type {
  EstudoVagas,
  PerfilMestre,
  Vaga,
  VagaCreate,
  VagaListResponse,
  VagasFiltro,
  VagasMetricas,
  AnalisarVagaResponse,
  GerarCandidaturaResponse,
  GerarCurriculoResponse,
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
  vagasListar(filtro: VagasFiltro = {}): Promise<VagaListResponse> {
    const p = new URLSearchParams();
    if (filtro.status) p.set('status', filtro.status);
    if (filtro.busca?.trim()) p.set('busca', filtro.busca.trim());
    if (filtro.match_min != null) p.set('match_min', String(filtro.match_min));
    if (filtro.modelo) p.set('modelo', filtro.modelo);
    if (filtro.fonte) p.set('fonte', filtro.fonte);
    if (filtro.tem_rascunho != null)
      p.set('tem_rascunho', String(filtro.tem_rascunho));
    if (filtro.ordenar_por) p.set('ordenar_por', filtro.ordenar_por);
    const q = p.toString();
    return request<VagaListResponse>(
      `/api/pessoal/vagas${q ? `?${q}` : ''}`,
      { timeoutMs: 10_000 },
    );
  },

  vagasMetricas(): Promise<VagasMetricas> {
    return request<VagasMetricas>('/api/pessoal/vagas/metricas', {
      timeoutMs: 10_000,
    });
  },

  vagasEstudo(): Promise<EstudoVagas> {
    return request<EstudoVagas>('/api/pessoal/vagas/estudo', {
      timeoutMs: 12_000,
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

  vagaGerarCurriculo(id: string): Promise<GerarCurriculoResponse> {
    return request<GerarCurriculoResponse>(
      `/api/pessoal/vagas/${encodeURIComponent(id)}/curriculo`,
      { method: 'POST', timeoutMs: 120_000 },
    );
  },

  vagaRascunhos(id: string): Promise<CandidaturaEmailItem[]> {
    return request<CandidaturaEmailItem[]>(
      `/api/pessoal/vagas/${encodeURIComponent(id)}/rascunhos`,
      { timeoutMs: 10_000 },
    );
  },
};

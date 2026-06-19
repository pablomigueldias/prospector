// Agente Freelancer (Workana) — CRM de propostas + precificador.

import { request } from './client';
import type {
  FreelaAnalisarResponse,
  FreelaCliente,
  FreelaChecklist,
  FreelaClienteCreate,
  FreelaExtrairProjeto,
  FreelaKanbanResponse,
  FreelaNegociarResponse,
  FreelaRedigirResponse,
  FreelaMetricas,
  FreelaPlanoMeta,
  FreelaPlanoMetaRequest,
  FreelaPlataforma,
  FreelaPrecificarRequest,
  FreelaPrecificarResponse,
  FreelaCapacidade,
  FreelaProjeto,
  FreelaProjetoCreate,
  FreelaTaxaPorStackResponse,
  FreelaProjetoListResponse,
  FreelaProposta,
  FreelaPropostaCreate,
  FreelaStatus,
} from '../types';

const BASE = '/api/pessoal/freela';
const T = 12_000;

export const freelaApi = {
  // ── Plataformas / painel ───────────────────────────────────────
  freelaPlataformas(): Promise<FreelaPlataforma[]> {
    return request<FreelaPlataforma[]>(`${BASE}/plataformas`, { timeoutMs: T });
  },
  freelaKanban(): Promise<FreelaKanbanResponse> {
    return request<FreelaKanbanResponse>(`${BASE}/kanban`, { timeoutMs: T });
  },
  freelaMetricas(): Promise<FreelaMetricas> {
    return request<FreelaMetricas>(`${BASE}/metricas`, { timeoutMs: T });
  },
  freelaTaxaPorStack(): Promise<FreelaTaxaPorStackResponse> {
    return request<FreelaTaxaPorStackResponse>(`${BASE}/metricas/por-stack`, { timeoutMs: T });
  },
  freelaCapacidade(): Promise<FreelaCapacidade> {
    return request<FreelaCapacidade>(`${BASE}/capacidade`, { timeoutMs: T });
  },
  freelaPrecificar(body: FreelaPrecificarRequest): Promise<FreelaPrecificarResponse> {
    return request<FreelaPrecificarResponse>(`${BASE}/precificar`, {
      method: 'POST',
      body,
      timeoutMs: T,
    });
  },
  freelaPlanoMeta(body: FreelaPlanoMetaRequest): Promise<FreelaPlanoMeta> {
    return request<FreelaPlanoMeta>(`${BASE}/meta/plano`, {
      method: 'POST',
      body,
      timeoutMs: T,
    });
  },

  // ── Clientes ───────────────────────────────────────────────────
  freelaClientes(): Promise<FreelaCliente[]> {
    return request<FreelaCliente[]>(`${BASE}/clientes`, { timeoutMs: T });
  },
  freelaClienteCriar(body: FreelaClienteCreate): Promise<FreelaCliente> {
    return request<FreelaCliente>(`${BASE}/clientes`, { method: 'POST', body, timeoutMs: T });
  },
  freelaClienteAtualizar(id: string, body: Partial<FreelaCliente>): Promise<FreelaCliente> {
    return request<FreelaCliente>(`${BASE}/clientes/${encodeURIComponent(id)}`, {
      method: 'PATCH',
      body,
      timeoutMs: T,
    });
  },
  freelaClienteRemover(id: string): Promise<void> {
    return request<void>(`${BASE}/clientes/${encodeURIComponent(id)}`, {
      method: 'DELETE',
      timeoutMs: T,
    });
  },

  // ── Projetos ───────────────────────────────────────────────────
  freelaProjetos(): Promise<FreelaProjetoListResponse> {
    return request<FreelaProjetoListResponse>(`${BASE}/projetos`, { timeoutMs: T });
  },
  freelaProjetoCriar(body: FreelaProjetoCreate): Promise<FreelaProjeto> {
    return request<FreelaProjeto>(`${BASE}/projetos`, { method: 'POST', body, timeoutMs: T });
  },
  freelaProjetoExtrair(origem: { texto?: string; url?: string }): Promise<FreelaExtrairProjeto> {
    return request<FreelaExtrairProjeto>(`${BASE}/projetos/extrair`, {
      method: 'POST',
      body: origem,
      timeoutMs: 60_000,
    });
  },
  freelaProjetoDetalhe(id: string): Promise<FreelaProjeto> {
    return request<FreelaProjeto>(`${BASE}/projetos/${encodeURIComponent(id)}`, { timeoutMs: T });
  },
  freelaProjetoAtualizar(id: string, body: Partial<FreelaProjeto>): Promise<FreelaProjeto> {
    return request<FreelaProjeto>(`${BASE}/projetos/${encodeURIComponent(id)}`, {
      method: 'PATCH',
      body,
      timeoutMs: T,
    });
  },
  freelaProjetoRemover(id: string): Promise<void> {
    return request<void>(`${BASE}/projetos/${encodeURIComponent(id)}`, {
      method: 'DELETE',
      timeoutMs: T,
    });
  },
  freelaProjetoPropostas(id: string): Promise<FreelaProposta[]> {
    return request<FreelaProposta[]>(`${BASE}/projetos/${encodeURIComponent(id)}/propostas`, {
      timeoutMs: T,
    });
  },
  freelaPropostaChecklist(id: string): Promise<FreelaChecklist> {
    return request<FreelaChecklist>(`${BASE}/propostas/${encodeURIComponent(id)}/checklist`, {
      method: 'POST',
      timeoutMs: 60_000,
    });
  },
  freelaPropostaCorrigir(id: string, correcoes: string[]): Promise<FreelaRedigirResponse> {
    return request<FreelaRedigirResponse>(`${BASE}/propostas/${encodeURIComponent(id)}/corrigir`, {
      method: 'POST',
      body: { correcoes },
      timeoutMs: 90_000,
    });
  },
  freelaPropostaNegociar(id: string, objecao: string): Promise<FreelaNegociarResponse> {
    return request<FreelaNegociarResponse>(`${BASE}/propostas/${encodeURIComponent(id)}/negociar`, {
      method: 'POST',
      body: { objecao },
      timeoutMs: 90_000,
    });
  },
  freelaProjetoAnalisar(id: string): Promise<FreelaAnalisarResponse> {
    return request<FreelaAnalisarResponse>(
      `${BASE}/projetos/${encodeURIComponent(id)}/analisar`,
      { method: 'POST', timeoutMs: 60_000 },
    );
  },

  // ── Propostas ──────────────────────────────────────────────────
  freelaPropostaCriar(body: FreelaPropostaCreate): Promise<FreelaProposta> {
    return request<FreelaProposta>(`${BASE}/propostas`, { method: 'POST', body, timeoutMs: T });
  },
  freelaPropostaDetalhe(id: string): Promise<FreelaProposta> {
    return request<FreelaProposta>(`${BASE}/propostas/${encodeURIComponent(id)}`, { timeoutMs: T });
  },
  freelaPropostaRedigir(id: string, instrucoes_extra?: string | null): Promise<FreelaRedigirResponse> {
    return request<FreelaRedigirResponse>(`${BASE}/propostas/${encodeURIComponent(id)}/redigir`, {
      method: 'POST',
      body: { instrucoes_extra: instrucoes_extra ?? null },
      timeoutMs: 90_000,
    });
  },
  freelaPropostaAtualizar(id: string, body: Partial<FreelaProposta>): Promise<FreelaProposta> {
    return request<FreelaProposta>(`${BASE}/propostas/${encodeURIComponent(id)}`, {
      method: 'PATCH',
      body,
      timeoutMs: T,
    });
  },
  freelaPropostaStatus(
    id: string,
    status: FreelaStatus,
    motivo_perda?: string | null,
  ): Promise<FreelaProposta> {
    return request<FreelaProposta>(`${BASE}/propostas/${encodeURIComponent(id)}/status`, {
      method: 'POST',
      body: { status, motivo_perda: motivo_perda ?? null },
      timeoutMs: T,
    });
  },
  freelaPropostaRemover(id: string): Promise<void> {
    return request<void>(`${BASE}/propostas/${encodeURIComponent(id)}`, {
      method: 'DELETE',
      timeoutMs: T,
    });
  },
};

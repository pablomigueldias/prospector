// CRM — empresas/contatos do Postgres: leitura, filtros e CRUD.

import { request } from './client';
import type {
  AtividadeListItem,
  AtividadeListResponse,
  AtividadeUpsert,
  ContatoListItem,
  ContatoListResponse,
  ContatosFiltro,
  ContatoUpsert,
  CrmDashboard,
  CrmFacetas,
  CrmMetricas,
  CrmOpcao,
  MemoriaEvento,
  MemoriaTimeline,
  OutcomeResumo,
  EmpresaDetalhe,
  EmpresaListResponse,
  EmpresaRelacionados,
  EmpresasFiltro,
  EmpresaUpsert,
  KanbanResponse,
  NegocioListItem,
  NegociosPipeline,
  NegocioUpsert,
  NotionSyncResultado,
  ProjetoListItem,
  ProjetoListResponse,
  ProjetoUpsert,
  RecordDetalhe,
  RecordTipo,
} from '../types';

function qs(params: Record<string, unknown>): string {
  const p = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === null || v === '') continue;
    p.set(k, String(v));
  }
  const s = p.toString();
  return s ? `?${s}` : '';
}

export const crmApi = {
  // ── Empresas ──────────────────────────────────────────────────
  crmEmpresas(filtro: EmpresasFiltro = {}): Promise<EmpresaListResponse> {
    return request<EmpresaListResponse>(`/api/crm/empresas${qs({ ...filtro })}`);
  },
  crmFacetas(): Promise<CrmFacetas> {
    return request<CrmFacetas>('/api/crm/empresas/facetas');
  },
  crmOpcoes(): Promise<CrmFacetas> {
    return request<CrmFacetas>('/api/crm/opcoes');
  },
  crmOpcoesCores(): Promise<Record<string, Record<string, string>>> {
    return request<Record<string, Record<string, string>>>(
      '/api/crm/opcoes/cores',
    );
  },
  crmOpcoesGerenciar(): Promise<CrmOpcao[]> {
    return request<CrmOpcao[]>('/api/crm/opcoes/gerenciar');
  },
  crmOpcaoCriar(body: {
    grupo: string;
    valor: string;
    cor?: string | null;
  }): Promise<CrmOpcao> {
    return request<CrmOpcao>('/api/crm/opcoes', { method: 'POST', body });
  },
  crmOpcaoAtualizar(
    id: string,
    body: { valor?: string; cor?: string | null; ativo?: boolean },
  ): Promise<CrmOpcao> {
    return request<CrmOpcao>(`/api/crm/opcoes/${id}`, { method: 'PATCH', body });
  },
  crmOpcaoExcluir(id: string): Promise<void> {
    return request<void>(`/api/crm/opcoes/${id}`, { method: 'DELETE' });
  },
  crmOpcoesReordenar(grupo: string, ids: string[]): Promise<CrmOpcao[]> {
    return request<CrmOpcao[]>('/api/crm/opcoes/reordenar', {
      method: 'POST',
      body: { grupo, ids },
    });
  },
  crmKanban(): Promise<KanbanResponse> {
    return request<KanbanResponse>('/api/crm/kanban');
  },
  crmMetricas(): Promise<CrmMetricas> {
    return request<CrmMetricas>('/api/crm/metricas');
  },
  crmDashboard(): Promise<CrmDashboard> {
    return request<CrmDashboard>('/api/crm/dashboard');
  },
  crmSincronizarNotion(): Promise<NotionSyncResultado> {
    return request<NotionSyncResultado>('/api/crm/sincronizar-notion', {
      method: 'POST',
      timeoutMs: 180_000,
    });
  },
  crmEmpresa(id: string): Promise<EmpresaDetalhe> {
    return request<EmpresaDetalhe>(`/api/crm/empresas/${id}`);
  },
  crmEmpresaRelacionados(id: string): Promise<EmpresaRelacionados> {
    return request<EmpresaRelacionados>(`/api/crm/empresas/${id}/relacionados`);
  },
  crmRecord(tipo: RecordTipo, id: string): Promise<RecordDetalhe> {
    return request<RecordDetalhe>(`/api/crm/record/${tipo}/${id}`);
  },
  memoriaTimeline(alvoTipo: string, alvoId: string): Promise<MemoriaTimeline> {
    return request<MemoriaTimeline>(`/api/memoria/${alvoTipo}/${alvoId}`);
  },
  memoriaCriarNota(
    alvoTipo: string,
    alvoId: string,
    resumo: string,
  ): Promise<MemoriaEvento> {
    return request<MemoriaEvento>('/api/memoria', {
      method: 'POST',
      body: {
        agente: 'usuario',
        alvo_tipo: alvoTipo,
        alvo_id: alvoId,
        tipo: 'nota',
        resumo,
        origem: 'manual',
      },
    });
  },
  memoriaOutcomeVocab(): Promise<Record<string, number>> {
    return request<Record<string, number>>('/api/memoria/outcomes/vocabulario');
  },
  memoriaRegistrarOutcome(
    alvoTipo: string,
    alvoId: string,
    resultado: string,
    nota?: string,
  ): Promise<{ ok: boolean }> {
    return request<{ ok: boolean }>('/api/memoria/outcome', {
      method: 'POST',
      body: { alvo_tipo: alvoTipo, alvo_id: alvoId, resultado, nota },
    });
  },
  memoriaOutcomesResumo(): Promise<OutcomeResumo> {
    return request<OutcomeResumo>('/api/memoria/outcomes/resumo');
  },
  crmRecordPatch(
    tipo: RecordTipo,
    id: string,
    campos: Record<string, unknown>,
  ): Promise<RecordDetalhe> {
    return request<RecordDetalhe>(`/api/crm/record/${tipo}/${id}`, {
      method: 'PATCH',
      body: { campos },
    });
  },
  crmEmpresaCriar(body: EmpresaUpsert): Promise<EmpresaDetalhe> {
    return request<EmpresaDetalhe>('/api/crm/empresas', { method: 'POST', body });
  },
  crmEmpresaSalvar(id: string, body: EmpresaUpsert): Promise<EmpresaDetalhe> {
    return request<EmpresaDetalhe>(`/api/crm/empresas/${id}`, {
      method: 'PUT',
      body,
    });
  },
  crmEmpresaExcluir(id: string): Promise<void> {
    return request<void>(`/api/crm/empresas/${id}`, { method: 'DELETE' });
  },

  // ── Contatos ──────────────────────────────────────────────────
  crmContatos(filtro: ContatosFiltro = {}): Promise<ContatoListResponse> {
    return request<ContatoListResponse>(`/api/crm/contatos${qs({ ...filtro })}`);
  },
  crmContatoCriar(body: ContatoUpsert): Promise<ContatoListItem> {
    return request<ContatoListItem>('/api/crm/contatos', { method: 'POST', body });
  },
  crmContatoSalvar(id: string, body: ContatoUpsert): Promise<ContatoListItem> {
    return request<ContatoListItem>(`/api/crm/contatos/${id}`, {
      method: 'PUT',
      body,
    });
  },
  crmContatoExcluir(id: string): Promise<void> {
    return request<void>(`/api/crm/contatos/${id}`, { method: 'DELETE' });
  },

  // ── Negócios ──────────────────────────────────────────────────
  crmNegocios(): Promise<NegocioListItem[]> {
    return request<NegocioListItem[]>('/api/crm/negocios');
  },
  crmNegociosPipeline(): Promise<NegociosPipeline> {
    return request<NegociosPipeline>('/api/crm/negocios/pipeline');
  },
  crmNegocioCriar(body: NegocioUpsert): Promise<NegocioListItem> {
    return request<NegocioListItem>('/api/crm/negocios', { method: 'POST', body });
  },
  crmNegocioSalvar(id: string, body: NegocioUpsert): Promise<NegocioListItem> {
    return request<NegocioListItem>(`/api/crm/negocios/${id}`, { method: 'PUT', body });
  },
  crmNegocioExcluir(id: string): Promise<void> {
    return request<void>(`/api/crm/negocios/${id}`, { method: 'DELETE' });
  },
  crmNegocioMoverEstagio(id: string, estagio: string): Promise<NegocioListItem> {
    return request<NegocioListItem>(
      `/api/crm/negocios/${id}/estagio?estagio=${encodeURIComponent(estagio)}`,
      { method: 'PATCH' },
    );
  },

  // ── Atividades ────────────────────────────────────────────────
  crmAtividades(): Promise<AtividadeListResponse> {
    return request<AtividadeListResponse>('/api/crm/atividades');
  },
  crmAtividadeCriar(body: AtividadeUpsert): Promise<AtividadeListItem> {
    return request<AtividadeListItem>('/api/crm/atividades', { method: 'POST', body });
  },
  crmAtividadeSalvar(id: string, body: AtividadeUpsert): Promise<AtividadeListItem> {
    return request<AtividadeListItem>(`/api/crm/atividades/${id}`, { method: 'PUT', body });
  },
  crmAtividadeExcluir(id: string): Promise<void> {
    return request<void>(`/api/crm/atividades/${id}`, { method: 'DELETE' });
  },

  // ── Projetos ──────────────────────────────────────────────────
  crmProjetos(): Promise<ProjetoListResponse> {
    return request<ProjetoListResponse>('/api/crm/projetos');
  },
  crmProjetoCriar(body: ProjetoUpsert): Promise<ProjetoListItem> {
    return request<ProjetoListItem>('/api/crm/projetos', { method: 'POST', body });
  },
  crmProjetoSalvar(id: string, body: ProjetoUpsert): Promise<ProjetoListItem> {
    return request<ProjetoListItem>(`/api/crm/projetos/${id}`, { method: 'PUT', body });
  },
  crmProjetoExcluir(id: string): Promise<void> {
    return request<void>(`/api/crm/projetos/${id}`, { method: 'DELETE' });
  },
};

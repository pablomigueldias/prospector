// Agente LinkedIn (P5 §6.C) — admin no studio: CRUD + publicar. NÃO auto-posta
// no LinkedIn; gera rascunhos pra Página da Reative e pro perfil pessoal.

import { request } from './client';
import type {
  GerarImagemLinkedinRequest,
  LinkedinBriefRequest,
  LinkedinConta,
  LinkedinGerarRequest,
  LinkedinPost,
  LinkedinPostCreate,
  LinkedinPostUpdate,
  LinkedinRedacao,
  LinkedinStatus,
} from '../types';

const BASE = '/api/linkedin';
const T = 12_000;

export const linkedinApi = {
  linkedinListar(
    status?: LinkedinStatus,
    conta?: LinkedinConta,
  ): Promise<LinkedinPost[]> {
    const qs = new URLSearchParams();
    if (status) qs.set('status', status);
    if (conta) qs.set('conta', conta);
    const sufixo = qs.toString() ? `?${qs.toString()}` : '';
    return request<LinkedinPost[]>(`${BASE}/posts${sufixo}`, { timeoutMs: T });
  },

  linkedinGet(id: string): Promise<LinkedinPost> {
    return request<LinkedinPost>(`${BASE}/posts/${id}`, { timeoutMs: T });
  },

  linkedinCriar(body: LinkedinPostCreate): Promise<LinkedinPost> {
    return request<LinkedinPost>(`${BASE}/posts`, {
      method: 'POST',
      body,
      timeoutMs: T,
    });
  },

  linkedinAtualizar(id: string, body: LinkedinPostUpdate): Promise<LinkedinPost> {
    return request<LinkedinPost>(`${BASE}/posts/${id}`, {
      method: 'PUT',
      body,
      timeoutMs: T,
    });
  },

  linkedinMudarStatus(id: string, status: LinkedinStatus): Promise<LinkedinPost> {
    return request<LinkedinPost>(`${BASE}/posts/${id}/status`, {
      method: 'PATCH',
      body: { status },
      timeoutMs: T,
    });
  },

  linkedinRemover(id: string): Promise<void> {
    return request<void>(`${BASE}/posts/${id}`, {
      method: 'DELETE',
      timeoutMs: T,
    });
  },

  // ── Agente (L1) ─────────────────────────────────────────────────
  linkedinRedigir(brief: LinkedinBriefRequest): Promise<LinkedinRedacao> {
    return request<LinkedinRedacao>(`${BASE}/redigir`, {
      method: 'POST',
      body: brief,
      timeoutMs: 90_000, // geração pela LLM é lenta
    });
  },

  // ── Coordenador (L2) ────────────────────────────────────────────
  linkedinGerar(req: LinkedinGerarRequest): Promise<LinkedinPost[]> {
    return request<LinkedinPost[]>(`${BASE}/gerar`, {
      method: 'POST',
      body: req,
      timeoutMs: 180_000, // gera vários posts em sequência
    });
  },

  // ── Direção de arte (L5) ────────────────────────────────────────
  linkedinSugerirMidia(id: string): Promise<LinkedinPost> {
    return request<LinkedinPost>(`${BASE}/posts/${id}/midia/sugerir`, {
      method: 'POST',
      timeoutMs: 90_000,
    });
  },

  linkedinGerarImagem(
    id: string,
    req: GerarImagemLinkedinRequest,
  ): Promise<LinkedinPost> {
    return request<LinkedinPost>(`${BASE}/posts/${id}/imagem`, {
      method: 'POST',
      body: req,
      timeoutMs: 120_000,
    });
  },
};

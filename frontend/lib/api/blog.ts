// Agente Blog (P5 §6) — admin no studio: CRUD + publicar. A leitura pública
// (site) usa /api/public/blog; aqui é a mesa de edição autenticada.

import { request } from './client';
import type {
  BlogBriefRequest,
  BlogPauta,
  BlogPautaGerarRequest,
  BlogPautaManualCreate,
  BlogPautaStatus,
  BlogPautaUpdate,
  BlogPostAdmin,
  BlogPostCreate,
  BlogPostUpdate,
  BlogRedacao,
  BlogStatus,
  CapaSugestoesResponse,
  ChecklistSeo,
  ChecklistSeoRequest,
  GerarImagemConteudoRequest,
  GerarImagemRequest,
  ImagemConteudoSugestoesResponse,
} from '../types';

const BASE = '/api/blog';
const T = 12_000;

export const blogApi = {
  blogListar(status?: BlogStatus): Promise<BlogPostAdmin[]> {
    const qs = status ? `?status=${encodeURIComponent(status)}` : '';
    return request<BlogPostAdmin[]>(`${BASE}/posts${qs}`, { timeoutMs: T });
  },

  blogGet(id: string): Promise<BlogPostAdmin> {
    return request<BlogPostAdmin>(`${BASE}/posts/${id}`, { timeoutMs: T });
  },

  blogCriar(body: BlogPostCreate): Promise<BlogPostAdmin> {
    return request<BlogPostAdmin>(`${BASE}/posts`, {
      method: 'POST',
      body,
      timeoutMs: T,
    });
  },

  blogAtualizar(id: string, body: BlogPostUpdate): Promise<BlogPostAdmin> {
    return request<BlogPostAdmin>(`${BASE}/posts/${id}`, {
      method: 'PUT',
      body,
      timeoutMs: T,
    });
  },

  blogMudarStatus(id: string, status: BlogStatus): Promise<BlogPostAdmin> {
    return request<BlogPostAdmin>(`${BASE}/posts/${id}/status`, {
      method: 'PATCH',
      body: { status },
      timeoutMs: T,
    });
  },

  blogRemover(id: string): Promise<void> {
    return request<void>(`${BASE}/posts/${id}`, {
      method: 'DELETE',
      timeoutMs: T,
    });
  },

  // ── Agente (B2) ─────────────────────────────────────────────────
  blogRedigir(brief: BlogBriefRequest): Promise<BlogRedacao> {
    return request<BlogRedacao>(`${BASE}/redigir`, {
      method: 'POST',
      body: brief,
      timeoutMs: 90_000, // geração de artigo pela LLM é lenta
    });
  },

  blogChecklist(payload: ChecklistSeoRequest): Promise<ChecklistSeo> {
    return request<ChecklistSeo>(`${BASE}/checklist`, {
      method: 'POST',
      body: payload,
      timeoutMs: T,
    });
  },

  // ── Pautas (B3) ─────────────────────────────────────────────────
  blogPautas(status?: BlogPautaStatus): Promise<BlogPauta[]> {
    const qs = status ? `?status=${encodeURIComponent(status)}` : '';
    return request<BlogPauta[]>(`${BASE}/pautas${qs}`, { timeoutMs: T });
  },

  blogGerarPautas(req: BlogPautaGerarRequest): Promise<BlogPauta[]> {
    return request<BlogPauta[]>(`${BASE}/pautas/gerar`, {
      method: 'POST',
      body: req,
      timeoutMs: 90_000,
    });
  },

  /** Coordenador 1-clique: pauta → rascunho completo (IA escreve e salva). */
  blogEscreverPauta(id: string): Promise<BlogPostAdmin> {
    return request<BlogPostAdmin>(`${BASE}/pautas/${id}/escrever`, {
      method: 'POST',
      timeoutMs: 90_000,
    });
  },

  // ── Imagens (B-IMG) ─────────────────────────────────────────────
  blogSugerirCapas(id: string): Promise<CapaSugestoesResponse> {
    return request<CapaSugestoesResponse>(`${BASE}/posts/${id}/imagem/sugestoes`, {
      method: 'POST',
      timeoutMs: 60_000,
    });
  },

  blogGerarImagem(id: string, body: GerarImagemRequest): Promise<BlogPostAdmin> {
    return request<BlogPostAdmin>(`${BASE}/posts/${id}/imagem`, {
      method: 'POST',
      body,
      timeoutMs: 120_000,
    });
  },

  /** Gera as imagens do corpo (marcadores {{IMG}}) — pode levar ~1min p/ 2-3. */
  blogGerarImagensConteudo(id: string): Promise<BlogPostAdmin> {
    return request<BlogPostAdmin>(`${BASE}/posts/${id}/imagem/conteudo`, {
      method: 'POST',
      timeoutMs: 180_000,
    });
  },

  /** Sugere imagens pro corpo (por seção) — igual as capas. */
  blogSugerirImagensConteudo(id: string): Promise<ImagemConteudoSugestoesResponse> {
    return request<ImagemConteudoSugestoesResponse>(
      `${BASE}/posts/${id}/imagem/conteudo/sugestoes`,
      { method: 'POST', timeoutMs: 60_000 },
    );
  },

  /** Gera 1 imagem de conteúdo (sugestão escolhida) e insere na seção. */
  blogInserirImagemConteudo(
    id: string,
    body: GerarImagemConteudoRequest,
  ): Promise<BlogPostAdmin> {
    return request<BlogPostAdmin>(`${BASE}/posts/${id}/imagem/conteudo/inserir`, {
      method: 'POST',
      body,
      timeoutMs: 120_000,
    });
  },

  blogUploadImagem(
    id: string,
    arquivo: File,
    papel: 'cover' | 'secao' = 'cover',
    alt?: string,
  ): Promise<BlogPostAdmin> {
    const fd = new FormData();
    fd.append('arquivo', arquivo);
    fd.append('papel', papel);
    if (alt) fd.append('alt', alt);
    return request<BlogPostAdmin>(`${BASE}/posts/${id}/imagem/upload`, {
      method: 'POST',
      body: fd,
      timeoutMs: 60_000,
    });
  },

  blogCriarPauta(body: BlogPautaManualCreate): Promise<BlogPauta> {
    return request<BlogPauta>(`${BASE}/pautas`, {
      method: 'POST',
      body,
      timeoutMs: T,
    });
  },

  blogAtualizarPauta(id: string, body: BlogPautaUpdate): Promise<BlogPauta> {
    return request<BlogPauta>(`${BASE}/pautas/${id}`, {
      method: 'PUT',
      body,
      timeoutMs: T,
    });
  },

  blogRemoverPauta(id: string): Promise<void> {
    return request<void>(`${BASE}/pautas/${id}`, {
      method: 'DELETE',
      timeoutMs: T,
    });
  },
};

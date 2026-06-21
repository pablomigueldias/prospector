// Blog headless (P5 §6) — admin no studio. Campos em snake_case (espelham a API).

export type BlogStatus = 'rascunho' | 'aprovado' | 'publicado' | 'arquivado';

export interface BlogTocItem {
  id: string;
  label: string;
}

export interface BlogPostAdmin {
  id: string;
  slug: string;
  title: string;
  excerpt?: string | null;
  category?: string | null;
  body_md?: string | null;
  toc: BlogTocItem[];
  cover_url?: string | null;
  cover_alt?: string | null;
  cover_class?: string | null;
  imagens: Record<string, unknown>[];
  status: BlogStatus;
  author: string;
  lang: string;
  tags: string[];
  reading_time?: number | null;
  word_count?: number | null;
  noindex: boolean;
  meta_description?: string | null;
  keyword_alvo?: string | null;
  keywords: string[];
  og_image?: string | null;
  og_title?: string | null;
  og_description?: string | null;
  fonte?: string | null;
  published_at?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface BlogPostCreate {
  title: string;
  slug?: string | null;
  excerpt?: string | null;
  category?: string | null;
  body_md?: string | null;
  cover_url?: string | null;
  cover_alt?: string | null;
  tags?: string[] | null;
  noindex?: boolean | null;
  meta_description?: string | null;
  keyword_alvo?: string | null;
  keywords?: string[] | null;
  og_title?: string | null;
  og_description?: string | null;
  og_image?: string | null;
  published_at?: string | null; // ISO; futuro = agendado (gate esconde até a data)
}

export type BlogPostUpdate = Partial<BlogPostCreate>;

// ── Agente (B2): redator + checklist SEO ─────────────────────────
export interface BlogBriefRequest {
  tema: string;
  keyword_alvo?: string | null;
  intencao?: string | null;
  publico?: string | null;
  tom?: string | null;
  pontos?: string | null;
}

export interface BlogRedacao {
  title: string;
  slug?: string | null;
  excerpt?: string | null;
  meta_description?: string | null;
  keyword_alvo?: string | null;
  keywords: string[];
  category?: string | null;
  tags: string[];
  toc: BlogTocItem[];
  body_md: string;
  og_title?: string | null;
  og_description?: string | null;
}

export interface GerarImagemRequest {
  prompt: string;
  papel?: 'cover' | 'secao';
  aspect_ratio?: string;
}

export interface ChecklistSeoRequest {
  title?: string | null;
  slug?: string | null;
  body_md?: string | null;
  excerpt?: string | null;
  meta_description?: string | null;
  keyword_alvo?: string | null;
}

export interface ChecklistItem {
  id: string;
  label: string;
  status: 'ok' | 'warn' | 'fail';
  dica?: string | null;
}

export interface ChecklistSeo {
  score: number;
  nivel: 'ruim' | 'ok' | 'bom' | 'otimo';
  itens: ChecklistItem[];
}

// ── Motor de pauta (B3) ──────────────────────────────────────────
export type BlogPautaStatus = 'ideia' | 'escolhida' | 'escrita' | 'descartada';

export interface BlogPauta {
  id: string;
  titulo: string;
  resumo?: string | null;
  keyword_alvo?: string | null;
  intencao?: string | null;
  publico?: string | null;
  estagio_funil?: string | null;
  fonte: string;
  score: number;
  status: BlogPautaStatus;
  notas?: string | null;
  post_id?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface BlogPautaGerarRequest {
  quantidade?: number;
  fontes?: string[] | null;
  publico?: string | null;
  sementes?: string | null;
  tendencias?: string | null;
}

export interface BlogPautaManualCreate {
  titulo: string;
  resumo?: string | null;
  keyword_alvo?: string | null;
  intencao?: string | null;
  publico?: string | null;
  estagio_funil?: string | null;
}

export interface BlogPautaUpdate {
  status?: BlogPautaStatus;
  score?: number;
  notas?: string | null;
  titulo?: string | null;
  keyword_alvo?: string | null;
}

// Agente LinkedIn (P5 §6.C) — admin no studio. Campos em snake_case (espelham
// a API). Um só modelo serve às duas contas (Página Reative e perfil pessoal).

export type LinkedinStatus = 'rascunho' | 'aprovado' | 'publicado' | 'arquivado';
export type LinkedinConta = 'reative' | 'pessoal';
export type LinkedinFormato = 'post' | 'carrossel' | 'artigo';
export type LinkedinFonte = 'blog' | 'projeto' | 'tendencia' | 'manual';

export type LinkedinMidiaTipo =
  | 'imagem_ia'
  | 'foto'
  | 'carrossel'
  | 'video_reel'
  | 'screenshot'
  | 'grafico'
  | 'sem_midia';

export interface LinkedinMidia {
  recomendacao: LinkedinMidiaTipo;
  justificativa?: string | null;
  passos: string[];
  dicas: string[];
  prompt_imagem?: string | null;
  alt?: string | null;
  aspect_ratio: string;
}

export interface LinkedinImagem {
  url: string;
  alt?: string | null;
  prompt?: string | null;
  origem: string;
}

export interface LinkedinPost {
  id: string;
  titulo?: string | null;
  conta: LinkedinConta;
  formato: LinkedinFormato;
  hook?: string | null;
  body?: string | null;
  cta?: string | null;
  hashtags: string[];
  status: LinkedinStatus;
  fonte: LinkedinFonte;
  origem_blog_post_id?: string | null;
  scheduled_for?: string | null;
  published_at?: string | null;
  midia?: LinkedinMidia | null;
  imagens: LinkedinImagem[];
  char_count?: number | null;
  notas?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface GerarImagemLinkedinRequest {
  prompt?: string | null;
  alt?: string | null;
  aspect_ratio?: string;
}

export interface LinkedinPostCreate {
  titulo?: string | null;
  conta?: LinkedinConta | null;
  formato?: LinkedinFormato | null;
  hook?: string | null;
  body?: string | null;
  cta?: string | null;
  hashtags?: string[] | null;
  fonte?: LinkedinFonte | null;
  notas?: string | null;
  scheduled_for?: string | null; // ISO
}

export type LinkedinPostUpdate = LinkedinPostCreate & {
  published_at?: string | null; // registrar quando postou na mão
};

// ── Agente (L1): redator ─────────────────────────────────────────
export interface LinkedinBriefRequest {
  tema: string;
  conta?: LinkedinConta | null;
  formato?: LinkedinFormato | null;
  publico?: string | null; // recrutador | cliente
  angulo?: string | null;
  tom?: string | null;
}

export interface LinkedinRedacao {
  titulo?: string | null;
  hook: string;
  body: string;
  cta?: string | null;
  hashtags: string[];
  pendencias: string[];
}

// ── Coordenador (L2): gera rascunhos prontos ─────────────────────
export interface LinkedinGerarRequest {
  fonte: 'projeto' | 'tendencia';
  quantidade: number;
  conta?: LinkedinConta | null;
  publico?: string | null;
}

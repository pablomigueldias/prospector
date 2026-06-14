// Copywriter / Outreach — geração de e-mails, follow-ups e histórico de envio.

export interface CopywriterRequest {
  empresa: string;
  segmento?: string | null;
  nome_contato?: string | null;
  cargo?: string | null;
  tipo: string;
  canal?: string;
  necessidade?: string | null;
  servico?: string | null;
  diferenciais?: string | null;
  contexto_extra?: string | null;
  lead_arquivo?: string | null;
}

export interface EmailGerado {
  assunto: string;
  corpo: string;
  cta: string;
  tom: string;
}

export interface CopywriterResponse {
  success: boolean;
  email: EmailGerado;
  variantes: EmailGerado[];
}

export interface GerarFollowupsRequest {
  dias?: number;
  max_followups?: number;
  limit?: number | null;
  pausa?: number;
}

export interface GerarFollowupsResponse {
  success: boolean;
  gerados: number;
  falhas: number;
}

export interface GerarRascunhosResponse {
  success: boolean;
  gerados: number;
  falhas: number;
  pulados: number;
}

export interface SyncResponse {
  success: boolean;
  enviados_confirmados: number;
  respostas_detectadas: number;
}

export type EmailStatus =
  | 'rascunho'
  | 'enviado'
  | 'respondido'
  | 'sem_resposta'
  | 'erro';

export interface EmailItem {
  id: string;
  destinatario: string;
  assunto: string;
  tom: string | null;
  status: EmailStatus;
  follow_up_num: number;
  draft_criado_em: string | null;
  enviado_em: string | null;
  primeira_resposta_em: string | null;
}

export interface EmailHistoryResponse {
  items: EmailItem[];
  total: number;
}

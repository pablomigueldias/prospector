// Agente Freelancer (Workana) — CRM de propostas + precificador.

export const FREELA_STATUS = [
  'rascunho',
  'enviada',
  'visualizada',
  'respondida',
  'negociando',
  'fechada',
  'perdida',
] as const;

export type FreelaStatus = (typeof FREELA_STATUS)[number];

export interface FreelaPlataforma {
  id: string;
  nome: string;
  url_base?: string | null;
  config_comissao?: Record<string, unknown> | null;
  lance_minimo_padrao?: number | null;
}

export interface FreelaCliente {
  id: string;
  nome: string;
  plataforma_id?: string | null;
  rating?: number | null;
  projetos_publicados?: number | null;
  projetos_pagos?: number | null;
  pagamento_verificado: boolean;
  membro_desde?: string | null;
  ja_me_pagou_usd: number;
  notas?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface FreelaClienteCreate {
  nome: string;
  plataforma_id?: string | null;
  ja_me_pagou_usd?: number;
  pagamento_verificado?: boolean;
  rating?: number | null;
  notas?: string | null;
}

export interface FreelaProjetoCreate {
  titulo: string;
  descricao: string;
  plataforma_id?: string | null;
  cliente_id?: string | null;
  url?: string | null;
  faixa_orcamento_min?: number | null;
  faixa_orcamento_max?: number | null;
  habilidades?: string[];
  prazo_estimado?: string | null;
  status_no_site?: string | null;
  n_propostas_concorrentes?: number | null;
  n_interessados?: number | null;
}

export interface FreelaProjeto extends FreelaProjetoCreate {
  id: string;
  analise_json?: Record<string, unknown> | null;
  coletado_em?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface FreelaProjetoListItem {
  id: string;
  titulo: string;
  cliente_nome?: string | null;
  status_no_site?: string | null;
  faixa_orcamento_min?: number | null;
  faixa_orcamento_max?: number | null;
  n_propostas_concorrentes?: number | null;
  fit_score?: number | null;
  tem_analise: boolean;
  qtd_propostas: number;
  cliente_recorrente: boolean;
  cliente_pago_usd: number;
  created_at?: string | null;
}

export interface FreelaProjetoListResponse {
  items: FreelaProjetoListItem[];
  total: number;
}

export interface FreelaProposta {
  id: string;
  projeto_id: string;
  valor_cotado?: number | null;
  horas_estimadas?: number | null;
  valor_liquido_estimado?: number | null;
  texto_enviado?: string | null;
  projetos_destacados: string[];
  habilidades_destacadas: string[];
  prazo_proposto?: string | null;
  status: FreelaStatus;
  enviada_em?: string | null;
  data_resposta?: string | null;
  data_fechamento?: string | null;
  motivo_perda?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface FreelaPropostaCreate {
  projeto_id: string;
  valor_cotado?: number | null;
  horas_estimadas?: number | null;
  valor_liquido_estimado?: number | null;
  prazo_proposto?: string | null;
  texto_enviado?: string | null;
}

export interface FreelaKanbanItem {
  id: string;
  projeto_id: string;
  projeto_titulo: string;
  cliente_nome?: string | null;
  valor_cotado?: number | null;
  valor_liquido_estimado?: number | null;
  status: FreelaStatus;
  dias_desde_envio?: number | null;
  created_at?: string | null;
}

export interface FreelaKanbanColuna {
  status: FreelaStatus;
  items: FreelaKanbanItem[];
}

export interface FreelaKanbanResponse {
  colunas: FreelaKanbanColuna[];
}

export interface FreelaMetricas {
  total_propostas: number;
  enviadas: number;
  respondidas: number;
  fechadas: number;
  perdidas: number;
  em_aberto: number;
  taxa_resposta: number;
  taxa_fechamento: number;
  liquido_total_fechado: number;
  ticket_medio_fechado: number;
  pipeline_aberto_liquido: number;
  forecast_liquido: number;
  tempo_medio_resposta_horas?: number | null;
  valor_hora_real?: number | null;
}

export interface FreelaPrecificarRequest {
  liquido_desejado: number;
  cliente_id?: string | null;
  ja_me_pagou_usd?: number | null;
  plataforma_id?: string | null;
  horas_estimadas?: number | null;
  valor_hora_alvo?: number | null;
}

export interface FreelaPrecificarResponse {
  pct_comissao: number;
  valor_a_cotar: number;
  cliente_paga: number;
  lance_minimo?: number | null;
  abaixo_do_lance_minimo: boolean;
  liquido_por_hora?: number | null;
  alerta?: string | null;
}

export interface FreelaAnalise {
  fit_score: number;
  recomendacao?: string | null; // vale | talvez | evite
  veredito?: string | null;
  requisitos: string[];
  stack: string[];
  red_flags: string[];
  sinais_cliente: string[];
  ganchos: string[];
}

export interface FreelaAnalisarResponse {
  projeto_id: string;
  analise: FreelaAnalise;
}

export interface FreelaRedacao {
  texto: string;
  prazo_sugerido?: string | null;
  tom?: string | null;
  projetos_destacados: string[];
  habilidades_destacadas: string[];
  variacoes_abertura: string[];
}

export interface FreelaRedigirResponse {
  proposta_id: string;
  redacao: FreelaRedacao;
}

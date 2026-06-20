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
  projetos_publicados?: number | null;
  projetos_pagos?: number | null;
  membro_desde?: string | null;
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
  publicado_em?: string | null;
}

export interface FreelaCapacidade {
  horas_semana: number;
  horas_comprometidas: number;
  horas_livres: number;
}

export interface FreelaTaxaPorStackItem {
  stack: string;
  enviadas: number;
  respondidas: number;
  taxa_resposta: number; // 0..1
  fechadas: number;
  win_rate: number; // 0..1 (fechadas / enviadas)
}

export interface FreelaTaxaPorStackResponse {
  itens: FreelaTaxaPorStackItem[];
}

export interface FreelaChecklistItem {
  criterio: string;
  ok: boolean;
  nota?: string | null;
}

export interface FreelaChecklist {
  proposta_id: string;
  score: number;
  selo?: string | null; // "pronta" | "ajustar" | "fraca"
  itens: FreelaChecklistItem[];
  sugestoes: string[];
  alerta_conformidade?: string | null;
}

export interface FreelaExtrairProjeto {
  titulo?: string | null;
  descricao?: string | null; // texto-fonte (colado ou lido da URL)
  url?: string | null;       // eco da URL quando importado por link
  faixa_orcamento_min?: number | null;
  faixa_orcamento_max?: number | null;
  n_propostas_concorrentes?: number | null;
  n_interessados?: number | null;
  habilidades?: string[];
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
  risco?: string | null;
  quadrante?: string | null; // quick_win | dificil_longo | escopo_vago | padrao
  preco_status?: string | null; // subcotado | justo | acima | sem_orcamento
  estimativa?: FreelaEstimativa | null;
  tem_analise: boolean;
  qtd_propostas: number;
  situacao: string; // sem_proposta | proposta_ativa | fechada | perdida
  cliente_recorrente: boolean;
  cliente_pago_usd: number;
  bom_primeiro: boolean;
  bom_primeiro_motivos: string[];
  publicado_em?: string | null;
  dias_desde_publicacao?: number | null;
  momento?: string | null; // agora | espere | passe
  momento_motivo?: string | null;
  valor_esperado?: number | null; // custo de oportunidade: R$/h esperado
  prob_resposta?: number | null; // prob. de resposta usada no cálculo (0..1)
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
  angulo_abertura?: string | null; // direto | prova | pergunta (A/B)
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

export interface FreelaPlanoMetaRequest {
  meta_liquida: number;
  horas_dia: number;
  dias_mes: number;
  pct_faturavel: number;
}

export interface FreelaFaseRampa {
  nome: string;
  meta_min: number;
  meta_max: number;
  foco: string;
}

export interface FreelaProgressoMes {
  realizado: number;
  meta_ate_hoje: number;
  fechadas_mes: number;
  dia: number;
  dias_no_mes: number;
  pct_meta: number; // 0..1+
  status: string; // na_frente | no_caminho | atras | sem_dados
  resumo: string;
}

export interface FreelaPlanoMeta {
  meta_liquida: number;
  horas_faturaveis_mes: number;
  valor_hora_alvo: number;
  valor_hora_real?: number | null;
  ticket_medio?: number | null;
  projecao_liquida_mes?: number | null;
  projetos_necessarios_mes?: number | null;
  propostas_necessarias_mes?: number | null;
  propostas_por_semana?: number | null;
  alcancavel_por_volume: boolean;
  gargalo: string; // ticket | conversao | volume | no_caminho | sem_dados
  diagnostico: string;
  fase: FreelaFaseRampa;
  progresso_mes?: FreelaProgressoMes | null;
}

export interface FreelaPrecificarRequest {
  liquido_desejado: number;
  cliente_id?: string | null;
  ja_me_pagou_usd?: number | null;
  plataforma_id?: string | null;
  horas_estimadas?: number | null;
  valor_hora_alvo?: number | null;
  orcamento_min?: number | null;
  orcamento_max?: number | null;
}

export interface FreelaPrecificarResponse {
  pct_comissao: number;
  valor_a_cotar: number;
  cliente_paga: number;
  lance_minimo?: number | null;
  abaixo_do_lance_minimo: boolean;
  liquido_por_hora?: number | null;
  alerta?: string | null;
  orcamento_status?: string | null; // abaixo | dentro | acima
  alerta_orcamento?: string | null;
}

export interface FreelaEstimativa {
  horas_estimadas?: number | null;
  prazo_dias?: number | null;
  valor_mercado_min?: number | null;
  valor_mercado_max?: number | null;
  valor_sugerido?: number | null;
}

export interface FreelaTarefa {
  nome: string;
  horas?: number | null;
}

export interface FreelaVeredictoPreco {
  status?: string | null; // subcotado | justo | acima | sem_orcamento
  gap_texto?: string | null;
  rh_orcamento?: number | null;
  rh_vs_alvo?: boolean | null;
}

export interface FreelaAnalise {
  fit_score: number;
  confianca_analise?: string | null; // alta | media | baixa (texto pobre → baixa)
  confianca_motivo?: string | null; // o que falta no texto pra cravar
  recomendacao?: string | null; // vale | talvez | evite
  risco?: string | null; // baixo | medio | alto
  complexidade_tecnica?: string | null; // trivial | media | alta | incerta
  clareza_escopo?: string | null; // claro | parcial | vago
  quadrante?: string | null; // quick_win | dificil_longo | escopo_vago | padrao
  veredito?: string | null;
  veredito_preco?: FreelaVeredictoPreco | null;
  requisitos: string[];
  stack: string[];
  tarefas: FreelaTarefa[];
  perguntas_cliente: string[];
  skills_faltando: string[];
  red_flags: string[];
  sinais_cliente: string[];
  ganchos: string[];
  estimativa?: FreelaEstimativa | null;
}

export interface FreelaAnalisarResponse {
  projeto_id: string;
  analise: FreelaAnalise;
}

export interface FreelaVariacaoAbertura {
  angulo: string; // direto | prova | pergunta
  texto: string;
}

export interface FreelaRedacao {
  texto: string;
  prazo_sugerido?: string | null;
  tom?: string | null;
  projetos_destacados: string[];
  habilidades_destacadas: string[];
  variacoes_abertura: FreelaVariacaoAbertura[];
}

export interface FreelaTaxaPorAnguloItem {
  angulo: string;
  enviadas: number;
  respondidas: number;
  taxa_resposta: number; // 0..1
}

export interface FreelaTaxaPorAnguloResponse {
  itens: FreelaTaxaPorAnguloItem[];
}

export interface FreelaRedigirResponse {
  proposta_id: string;
  redacao: FreelaRedacao;
}

export interface FreelaNegociarResponse {
  proposta_id: string;
  opcoes: string[];
}

// Coordenador (cadeia "proposta de freela") — 2 fases com checkpoint humano.
export interface FreelaPropostaAnalise {
  projeto_id: string;
  titulo?: string | null;
  fit_score: number;
  recomendacao?: string | null;
  risco?: string | null;
  quadrante?: string | null;
  veredito?: string | null;
  veredito_preco?: FreelaVeredictoPreco | null;
  recomenda: boolean;
  tarefas: FreelaTarefa[];
  perguntas_cliente: string[];
  skills_faltando: string[];
  estimativa?: FreelaEstimativa | null;
}

export interface FreelaPropostaEntrega {
  projeto_id: string;
  proposta_id: string;
  valor_cotado?: number | null;
  horas_estimadas?: number | null;
  prazo?: string | null;
  texto: string;
  variacoes_abertura: FreelaVariacaoAbertura[];
  checklist_score: number;
  checklist_selo?: string | null;
  checklist_sugestoes: string[];
}

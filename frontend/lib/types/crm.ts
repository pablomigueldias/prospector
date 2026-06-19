// CRM — empresas, contatos e pipeline lidos do Postgres (fora do Notion).

export interface ContatoOut {
  id: string;
  nome: string;
  cargo?: string | null;
  decisor: boolean;
  email?: string | null;
  telefone?: string | null;
  whatsapp?: string | null;
  linkedin?: string | null;
  origem_contato?: string | null;
}

export interface SocioOut {
  id: string;
  nome: string;
  qualificacao?: string | null;
}

export interface EmpresaListItem {
  id: string;
  nome: string;
  cnpj?: string | null;
  site?: string | null;
  cidade?: string | null;
  estado?: string | null;
  setor?: string | null;
  tamanho?: string | null;
  status?: string | null;
  como_conheceu?: string | null;
  score?: number | null;
  n_contatos: number;
}

export interface EmpresaDetalhe {
  id: string;
  nome: string;
  razao_social?: string | null;
  cnpj?: string | null;
  cidade?: string | null;
  estado?: string | null;
  local?: string | null;
  site?: string | null;
  instagram?: string | null;
  facebook?: string | null;
  capital_social?: number | null;
  setor?: string | null;
  tamanho?: string | null;
  score?: number | null;
  status?: string | null;
  como_conheceu?: string | null;
  notas?: string | null;
  analise_json?: Record<string, unknown> | null;
  notion_page_id?: string | null;
  contatos: ContatoOut[];
  socios: SocioOut[];
}

export interface EmpresaListResponse {
  items: EmpresaListItem[];
  total: number;
}

export interface KanbanColuna {
  status: string;
  total: number;
  empresas: EmpresaListItem[];
}

export interface KanbanResponse {
  colunas: KanbanColuna[];
}

export interface CrmMetricas {
  total_empresas: number;
  total_contatos: number;
  total_decisores: number;
  por_status: Record<string, number>;
}

export interface EmpresaRelacionados {
  negocios: NegocioListItem[];
  projetos: ProjetoListItem[];
  atividades: AtividadeListItem[];
}

export type RecordTipo =
  | 'empresa'
  | 'contato'
  | 'negocio'
  | 'projeto'
  | 'atividade';

export interface RecordCampo {
  label: string;
  valor: string;
  campo?: string | null;
  kind?: 'text' | 'num' | 'date' | 'select' | 'bool';
  opcoes_key?: string | null;
  raw?: string | null;
}

export interface RecordLink {
  tipo: RecordTipo;
  id: string;
  nome: string;
  sub?: string | null;
}

export interface RecordGrupo {
  titulo: string;
  itens: RecordLink[];
}

export interface RecordDetalhe {
  tipo: RecordTipo;
  id: string;
  titulo: string;
  campos: RecordCampo[];
  grupos: RecordGrupo[];
  notas?: string | null;
}

export interface EstagioResumo {
  estagio: string;
  total: number;
  valor: number;
}

export interface CrmDashboard {
  pipeline_valor: number;
  pipeline_ponderado: number;
  negocios_abertos: number;
  por_estagio: EstagioResumo[];
  atividades_total: number;
  atividades_pendentes: number;
  atividades_atrasadas: number;
  projetos_total: number;
  projetos_valor_total: number;
  projetos_recebido: number;
  projetos_a_receber: number;
  empresas_total: number;
  clientes_ativos: number;
  contatos_total: number;
}

export interface NotionSyncResultado {
  empresas_lidas: number;
  paginas_ignoradas: number;
  contatos_lidos: number;
  empresas_sem_link: number;
  negocios_lidos: number;
  projetos_lidos: number;
  atividades_lidas: number;
  erros: string[];
}

export interface EmpresaUpsert {
  nome: string;
  razao_social?: string | null;
  cnpj?: string | null;
  site?: string | null;
  cidade?: string | null;
  estado?: string | null;
  local?: string | null;
  instagram?: string | null;
  facebook?: string | null;
  capital_social?: number | null;
  setor?: string | null;
  tamanho?: string | null;
  score?: number | null;
  status?: string | null;
  como_conheceu?: string | null;
  notas?: string | null;
}

export type CrmFacetas = Record<string, string[]>;

export interface CrmOpcao {
  id: string;
  grupo: string;
  valor: string;
  cor?: string | null;
  ordem: number;
  ativo: boolean;
}

export interface MemoriaEvento {
  id: string;
  agente: string;
  alvo_tipo: string;
  alvo_id: string;
  tipo: string;
  resumo?: string | null;
  payload?: Record<string, unknown> | null;
  origem: string;
  created_at: string;
}

export interface MemoriaTimeline {
  alvo_tipo: string;
  alvo_id: string;
  eventos: MemoriaEvento[];
}

export interface OutcomeResumo {
  total: number;
  positivos: number;
  negativos: number;
  taxa_positiva?: number | null;
  por_resultado: Record<string, number>;
  por_alvo_tipo: Record<string, { positivos: number; negativos: number; total: number }>;
}

export interface EmpresasFiltro {
  status?: string;
  setor?: string;
  estado?: string;
  cidade?: string;
  tamanho?: string;
  como_conheceu?: string;
  score_min?: number;
  busca?: string;
  ordenar_por?: string;
  desc?: boolean;
  limit?: number;
}

export interface ContatoListItem {
  id: string;
  nome: string;
  cargo?: string | null;
  decisor: boolean;
  email?: string | null;
  telefone?: string | null;
  whatsapp?: string | null;
  linkedin?: string | null;
  origem_contato?: string | null;
  empresa_id: string;
  empresa_nome?: string | null;
}

export interface ContatoListResponse {
  items: ContatoListItem[];
  total: number;
}

export interface ContatoUpsert {
  empresa_id: string;
  nome: string;
  cargo?: string | null;
  decisor: boolean;
  email?: string | null;
  telefone?: string | null;
  whatsapp?: string | null;
  linkedin?: string | null;
  origem_contato?: string | null;
}

export interface ContatosFiltro {
  busca?: string;
  empresa_id?: string;
  decisor?: boolean;
  origem?: string;
  limit?: number;
}

export interface NegocioListItem {
  id: string;
  nome: string;
  estagio?: string | null;
  valor_estimado?: number | null;
  valor_ponderado?: number | null;
  probabilidade?: string | null;
  origem?: string | null;
  tipo_servico: string[];
  previsao_fechamento?: string | null;
  proxima_acao?: string | null;
  empresa_id?: string | null;
  empresa_nome?: string | null;
  contato_nome?: string | null;
  notas?: string | null;
}

export interface NegocioColuna {
  estagio: string;
  total: number;
  valor_total: number;
  valor_ponderado: number;
  negocios: NegocioListItem[];
}

export interface NegociosPipeline {
  colunas: NegocioColuna[];
  valor_total: number;
  valor_ponderado: number;
}

export interface AtividadeListItem {
  id: string;
  titulo: string;
  tipo?: string | null;
  status?: string | null;
  data?: string | null;
  resumo?: string | null;
  proximos_passos?: string | null;
  negocio_id?: string | null;
  negocio_nome?: string | null;
  contato_nome?: string | null;
}

export interface AtividadeListResponse {
  items: AtividadeListItem[];
  total: number;
}

export interface ProjetoListItem {
  id: string;
  nome: string;
  status?: string | null;
  tipo_servico?: string | null;
  valor_total?: number | null;
  valor_recebido?: number | null;
  a_receber?: number | null;
  prazo_entrega?: string | null;
  data_entrega_real?: string | null;
  link_producao?: string | null;
  repo_github?: string | null;
  empresa_nome?: string | null;
  negocio_nome?: string | null;
  briefing?: string | null;
}

export interface ProjetoListResponse {
  items: ProjetoListItem[];
  total: number;
}

export interface NegocioUpsert {
  nome: string;
  estagio?: string | null;
  valor_estimado?: number | null;
  probabilidade?: string | null;
  origem?: string | null;
  tipo_servico: string[];
  notas?: string | null;
  motivo_perda?: string | null;
  previsao_fechamento?: string | null;
  data_fechamento_real?: string | null;
  proxima_acao?: string | null;
  empresa_id?: string | null;
  contato_id?: string | null;
}

export interface AtividadeUpsert {
  titulo: string;
  tipo?: string | null;
  status?: string | null;
  data?: string | null;
  resumo?: string | null;
  proximos_passos?: string | null;
  negocio_id?: string | null;
  contato_id?: string | null;
}

export interface ProjetoUpsert {
  nome: string;
  status?: string | null;
  tipo_servico?: string | null;
  valor_total?: number | null;
  valor_recebido?: number | null;
  briefing?: string | null;
  link_producao?: string | null;
  repo_github?: string | null;
  forma_pagamento?: string | null;
  prazo_entrega?: string | null;
  data_inicio?: string | null;
  data_entrega_real?: string | null;
  empresa_id?: string | null;
  negocio_id?: string | null;
}

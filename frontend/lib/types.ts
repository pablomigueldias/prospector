export type AgentStatus = 'active' | 'soon' | 'experimental';

export interface Agent {
  slug: string;
  name: string;
  description: string;
  icon: string; // ex: "ti-radar", "ti-cash"
  status: AgentStatus;
  order: number;
  category: string;
  capabilities: Record<string, boolean>;
  roadmap_label: string | null;
}

export interface ProspectorManualRequest {
  cnpj: string;
  site?: string | null;
  instagram?: string | null;
  facebook?: string | null;
  linkedin?: string | null;
  email?: string | null;
  telefone?: string | null;
  whatsapp?: string | null;
}

export interface Contato {
  nome: string | null;
  cargo: string | null;
  email: string | null;
  telefone: string | null;
  whatsapp: string | null;
  linkedin: string | null;
  decisor: boolean;
}

export interface Empresa {
  nome: string | null;
  razao_social: string | null;
  cnpj: string | null;
  cidade: string | null;
  estado: string | null;
  setor: string | null;
  tamanho: string | null;
  capital_social: number | null;
  site: string | null;
  instagram: string | null;
  facebook: string | null;
  notas: string | null;
  notion_page_id: string | null;
}

export interface Lead {
  empresa: Empresa;
  contatos: Contato[];
}

export type FonteCnpj = 'brasilapi' | 'opencnpj' | null;

export interface ProspectorPreviewResponse {
  success: boolean;
  fonte_cnpj: FonteCnpj;
  lead: Lead;
}

export interface ProspectorRunResponse {
  success: boolean;
  fonte_cnpj: FonteCnpj;
  lead: Lead;
  notion_empresa_id: string | null;
  notion_contatos_ids: string[];
}

export interface LeadHistoryItem {
  empresa_nome: string;
  cnpj: string | null;
  cidade: string | null;
  estado: string | null;
  setor: string | null;
  qtd_contatos: number;
  notion_empresa_id: string | null;
  enviado_em: string | null; // ISO 8601
  arquivo: string;
}

export interface LeadHistoryResponse {
  items: LeadHistoryItem[];
  total: number;
}

// ── Auth (login / sessão / permissões) ─────────────────────────────
export interface Usuario {
  id: string;
  email: string;
  nome: string;
  ativo: boolean;
  twofa_ativado: boolean;
  ultimo_login: string | null;
  permissoes: string[];
}

export interface PapelItem {
  nome: string;
  descricao: string | null;
}

export interface UsuarioAdminItem {
  id: string;
  email: string;
  nome: string;
  ativo: boolean;
  twofa_ativado: boolean;
  papeis: string[];
  ultimo_login: string | null;
  created_at: string | null;
}

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly detail: string | null = null,
  ) {
    super(message);
    this.name = 'ApiError';
  }

  get isClientError(): boolean {
    return this.status >= 400 && this.status < 500;
  }

  get isServerError(): boolean {
    return this.status >= 500 || this.status === 0;
  }
}

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

// ══════════════════════════════════════════════════════════════════
// Área PESSOAL — Perfil Mestre, Vagas e Candidatura
// ══════════════════════════════════════════════════════════════════

export interface Habilidade {
  nome: string;
  nivel?: string | null;
  onde_usou?: string | null;
}

export interface ProjetoPerfil {
  nome: string;
  descricao?: string | null;
  prova?: string | null;
  stack: string[];
  link?: string | null;
}

export interface ExperienciaPerfil {
  empresa?: string | null;
  cargo?: string | null;
  periodo?: string | null;
  descricao?: string | null;
}

export interface FormacaoPerfil {
  instituicao?: string | null;
  curso?: string | null;
  periodo?: string | null;
}

export interface BlocoCurriculo {
  titulo: string;
  conteudo: string;
  tags: string[];
}

export interface OQueProcuro {
  stack: string[];
  modelo?: string | null;
  tipo_empresa?: string | null;
  pretensao?: string | null;
  observacoes?: string | null;
}

export interface ContatoPessoal {
  email?: string | null;
  telefone?: string | null;
  linkedin?: string | null;
  github?: string | null;
  portfolio?: string | null;
}

export interface PerfilMestre {
  id?: string;
  ativo?: boolean;
  nome: string;
  titulo?: string | null;
  resumo?: string | null;
  tom_escrita?: string | null;
  habilidades: Habilidade[];
  projetos: ProjetoPerfil[];
  experiencias: ExperienciaPerfil[];
  formacao: FormacaoPerfil[];
  o_que_procuro?: OQueProcuro | null;
  blocos_curriculo: BlocoCurriculo[];
  contato?: ContatoPessoal | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export type VagaStatus =
  | 'quero_candidatar'
  | 'candidatei'
  | 'respondeu'
  | 'entrevista'
  | 'fim';

export interface AnaliseVaga {
  requisitos_obrigatorios: string[];
  desejaveis: string[];
  stack: string[];
  senioridade?: string | null;
  palavras_chave: string[];
  resumo?: string | null;
}

export interface MatchVaga {
  aderencia: number;
  tenho: string[];
  gaps: string[];
  destaques: string[];
  veredito?: string | null;
}

export interface Vaga {
  id: string;
  titulo: string;
  empresa?: string | null;
  link?: string | null;
  fonte?: string | null;
  contato_nome?: string | null;
  contato_email?: string | null;
  localizacao?: string | null;
  modelo?: string | null;
  senioridade?: string | null;
  descricao: string;
  notas?: string | null;
  status: VagaStatus;
  analise_json?: AnaliseVaga | null;
  match_json?: MatchVaga | null;
  match_score?: number | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface VagaCreate {
  titulo: string;
  descricao: string;
  empresa?: string | null;
  link?: string | null;
  fonte?: string | null;
  contato_nome?: string | null;
  contato_email?: string | null;
  localizacao?: string | null;
  modelo?: string | null;
  senioridade?: string | null;
  notas?: string | null;
}

export interface VagaListItem {
  id: string;
  titulo: string;
  empresa?: string | null;
  status: VagaStatus;
  modelo?: string | null;
  senioridade?: string | null;
  match_score?: number | null;
  tem_analise: boolean;
  qtd_rascunhos: number;
  created_at?: string | null;
}

export interface VagaListResponse {
  items: VagaListItem[];
  total: number;
}

export interface AnalisarVagaResponse {
  success: boolean;
  analise: AnaliseVaga;
  match: MatchVaga;
  match_score: number;
}

export interface EmailCandidatura {
  assunto?: string | null;
  corpo: string;
  tom?: string | null;
}

export interface CartaCandidatura {
  corpo: string;
  tom?: string | null;
}

export interface GerarCandidaturaResponse {
  success: boolean;
  email: EmailCandidatura;
  variantes_email: EmailCandidatura[];
  carta?: CartaCandidatura | null;
  rascunho_id?: string | null;
}

export interface CandidaturaEmailItem {
  id: string;
  vaga_id: string;
  tipo: string;
  destinatario?: string | null;
  assunto?: string | null;
  corpo: string;
  tom?: string | null;
  status: string;
  created_at?: string | null;
}

// ── Finanças (Organizador Financeiro pessoal) ──────────────────────
export interface Conta {
  id: string;
  usuario_id: string;
  nome: string;
  tipo: string;
  saldo_atual: string;
  ativa: boolean;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface ContaListResponse {
  items: Conta[];
  total: number;
}

/** Tipos de conta aceitos pelo backend (TIPOS_CONTA). */
export type TipoConta =
  | 'corrente'
  | 'dinheiro'
  | 'vr'
  | 'va'
  | 'reserva'
  | 'cartao_credito';

export interface ContaCreateInput {
  nome: string;
  tipo: TipoConta;
  saldo_atual?: string;
}

export interface ContaUpdateInput {
  nome?: string;
  tipo?: TipoConta;
  ativa?: boolean;
}

export interface CategoriaResumoItem {
  categoria_id?: string | null;
  categoria_nome: string;
  total: string;
}

// ── Transações (lista filtrável + lançamento pela web) ──────────────
export interface TransacaoListItem {
  id: string;
  tipo: string;
  descricao: string;
  valor_total: string;
  data_competencia: string;
  data_pagamento?: string | null;
  data_vencimento?: string | null;
  status: string;
  categoria_id?: string | null;
  categoria_nome?: string | null;
  contas: string[];
}

export interface TransacaoListResponse {
  items: TransacaoListItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface TransacaoPagamento {
  id: string;
  conta_id: string;
  valor: string;
}

/** Resposta de detalhe/criação de transação. O detalhe (GET /{id}) traz os
 *  `pagamentos`, usados pra pré-preencher a conta na edição. */
export interface TransacaoResponse {
  id: string;
  usuario_id: string;
  tipo: string;
  descricao: string;
  valor_total: string;
  data_competencia: string;
  data_pagamento?: string | null;
  status: string;
  categoria_id?: string | null;
  pagamentos?: TransacaoPagamento[];
}

export interface TransacaoFiltro {
  ano?: number;
  mes?: number;
  conta_id?: string;
  categoria_id?: string;
  tipo?: 'despesa' | 'receita';
  /** prevista/paga/atrasada — pode passar várias (ex.: a pagar = previstas+atrasadas). */
  status?: string[];
  busca?: string;
  /** Ordena por vencimento (vencidas primeiro) — usado no painel "A pagar". */
  por_vencimento?: boolean;
  limit?: number;
  offset?: number;
}

/** Payload pra lançar despesa ou receita pela web. O `usuario_id` é injetado
 *  no api.ts (ignorado pelo backend, que usa a sessão). */
export interface LancamentoInput {
  descricao: string;
  valor_total: string;
  conta_id: string;
  categoria_id?: string | null;
  data_competencia?: string | null;
  status?: 'paga' | 'prevista';
}

/** Payload pra editar uma transação (PATCH). Inclui o `tipo` porque a edição
 *  pode trocar despesa↔receita. */
export interface TransacaoEditInput {
  tipo: 'despesa' | 'receita';
  descricao: string;
  valor_total: string;
  conta_id: string;
  categoria_id?: string | null;
  data_competencia?: string | null;
  status?: 'paga' | 'prevista';
}

// ── Recorrências (despesas/receitas fixas) ──────────────────────────
export interface Recorrencia {
  id: string;
  usuario_id: string;
  descricao: string;
  tipo: string;
  valor_estimado: string;
  dia_vencimento: number;
  frequencia: string;
  categoria_id?: string | null;
  conta_id?: string | null;
  ativa: boolean;
}

export interface RecorrenciaListResponse {
  items: Recorrencia[];
  total: number;
}

export interface RecorrenciaCreateInput {
  descricao: string;
  tipo: 'despesa' | 'receita';
  valor_estimado: string;
  dia_vencimento: number;
  categoria_id?: string | null;
  conta_id?: string | null;
}

export interface RecorrenciaUpdateInput {
  descricao?: string;
  tipo?: 'despesa' | 'receita';
  valor_estimado?: string;
  dia_vencimento?: number;
  categoria_id?: string | null;
  conta_id?: string | null;
  ativa?: boolean;
}

export interface CategoriaTreeItem {
  id: string;
  nome: string;
  ativa: boolean;
  filhos: CategoriaTreeItem[];
}

export interface CategoriaTreeResponse {
  items: CategoriaTreeItem[];
  total: number;
}

export interface CategoriaResponse {
  id: string;
  nome: string;
  categoria_pai_id?: string | null;
  ativa: boolean;
}

export interface CategoriaCreateInput {
  nome: string;
  categoria_pai_id?: string | null;
}

export interface CategoriaUpdateInput {
  nome?: string;
  categoria_pai_id?: string | null;
  ativa?: boolean;
}

export interface ResumoMes {
  ano: number;
  mes: number;
  total_receitas: string;
  total_despesas: string;
  saldo: string;
  por_categoria: CategoriaResumoItem[];
}

export interface RelatorioMesItem {
  ano: number;
  mes: number;
  total_receitas: string;
  total_despesas: string;
  saldo: string;
}

export interface RelatorioResponse {
  meses: RelatorioMesItem[];
  por_categoria: CategoriaResumoItem[];
  total_receitas: string;
  total_despesas: string;
  saldo: string;
  media_despesas: string;
}

export interface Cartao {
  id: string;
  usuario_id: string;
  nome: string;
  bandeira?: string | null;
  dia_fechamento: number;
  dia_vencimento: number;
  limite?: string | null;
  ativo: boolean;
}

export interface CartaoListResponse {
  items: Cartao[];
  total: number;
}

export interface CartaoCreateInput {
  nome: string;
  bandeira?: string | null;
  dia_fechamento: number;
  dia_vencimento: number;
  limite?: string | null;
}

export interface CartaoUpdateInput {
  nome?: string;
  bandeira?: string | null;
  dia_fechamento?: number;
  dia_vencimento?: number;
  limite?: string | null;
  ativo?: boolean;
}

export interface Fatura {
  id: string;
  cartao_id: string;
  mes_referencia: string;
  valor_total: string;
  vencimento: string;
  status: string;
}

export interface FaturasCartao {
  cartao_id: string;
  faturas: Fatura[];
  total_em_aberto: string;
  total_juros: string;
}

export interface LeituraConsumo {
  id: string;
  usuario_id: string;
  tipo: string;
  mes_referencia: string;
  leitura_atual: string;
  leitura_anterior?: string | null;
  consumo?: string | null;
  valor?: string | null;
  transacao_id?: string | null;
}

export interface LeituraConsumoListResponse {
  items: LeituraConsumo[];
  total: number;
}

export interface Comprovante {
  id: string;
  usuario_id: string;
  transacao_id?: string | null;
  tipo: string;
  bucket: string;
  arquivo_path: string;
  nome_original?: string | null;
  content_type?: string | null;
  tamanho?: number | null;
  hash: string;
  url?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface ComprovanteListResponse {
  items: Comprovante[];
  total: number;
}

// ── Importador de boleto (LLM multimodal) ─────────────────────────
export interface VerbaBoleto {
  descricao: string;
  valor: string | number;
}

export interface LeituraBoleto {
  tipo: string;
  leitura_atual?: string | number | null;
  leitura_anterior?: string | number | null;
  consumo?: string | number | null;
  valor?: string | number | null;
}

export interface BoletoExtraido {
  beneficiario?: string | null;
  vencimento?: string | null;
  valor_total: string | number;
  verbas: VerbaBoleto[];
  leituras: LeituraBoleto[];
}

export interface ImportarBoletoResponse {
  success: boolean;
  conferido: boolean;
  mensagem: string;
  comprovante_id?: string | null;
  transacao_id?: string | null;
  extraido?: BoletoExtraido | null;
}

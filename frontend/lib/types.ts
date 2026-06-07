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

export interface CategoriaResumoItem {
  categoria_id?: string | null;
  categoria_nome: string;
  total: string;
}

export interface ResumoMes {
  ano: number;
  mes: number;
  total_receitas: string;
  total_despesas: string;
  saldo: string;
  por_categoria: CategoriaResumoItem[];
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

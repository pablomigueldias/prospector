// Área PESSOAL — Perfil Mestre, Vagas e Candidatura.

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

export interface FaixaSalarial {
  pj_min?: number | null;
  pj_max?: number | null;
  clt_min?: number | null;
  clt_max?: number | null;
  pretensao_pj?: number | null;
  pretensao_clt?: number | null;
  base?: string | null;
  observacao?: string | null;
}

export interface AnaliseVaga {
  requisitos_obrigatorios: string[];
  desejaveis: string[];
  stack: string[];
  senioridade?: string | null;
  palavras_chave: string[];
  resumo?: string | null;
  salario?: FaixaSalarial | null;
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
  curriculo?: CurriculoVaga | null;
  curriculo_gerado_em?: string | null;
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
  tem_curriculo: boolean;
  qtd_rascunhos: number;
  created_at?: string | null;
}

export interface VagaListResponse {
  items: VagaListItem[];
  total: number;
}

export interface VagasFiltro {
  status?: VagaStatus | '';
  busca?: string;
  match_min?: number | null;
  modelo?: string;
  fonte?: string;
  tem_rascunho?: boolean | null;
  ordenar_por?: 'match' | 'recentes';
}

export interface VagasMetricas {
  total: number;
  por_status: Record<VagaStatus, number>;
  candidaturas: number;
  em_andamento: number;
  responderam: number;
  entrevistas: number;
  taxa_resposta: number | null;
  taxa_entrevista: number | null;
  match_medio: number | null;
  match_medio_candidaturas: number | null;
}

export interface SkillEstudo {
  skill: string;
  n_vagas: number;
  pct_vagas: number;
  obrigatoria_em: number;
  tenho: boolean;
}

export interface EstudoVagas {
  total_vagas: number;
  para_estudar: SkillEstudo[];
  pontos_fortes: SkillEstudo[];
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

// ── Currículo ATS sob medida pra vaga (PDF gerado no front) ───────

export interface CompetenciaGrupo {
  categoria: string;
  itens: string[];
}

export interface CurriculoExperiencia {
  cargo?: string | null;
  empresa?: string | null;
  periodo?: string | null;
  bullets: string[];
}

export interface CurriculoProjeto {
  nome: string;
  descricao?: string | null;
  stack: string[];
  link?: string | null;
}

export interface CurriculoVaga {
  nome: string;
  titulo?: string | null;
  contato?: ContatoPessoal | null;
  resumo?: string | null;
  competencias: CompetenciaGrupo[];
  experiencias: CurriculoExperiencia[];
  projetos: CurriculoProjeto[];
  formacao: FormacaoPerfil[];
}

export interface GerarCurriculoResponse {
  vaga_id: string;
  curriculo: CurriculoVaga;
  gerado_em?: string | null;
}

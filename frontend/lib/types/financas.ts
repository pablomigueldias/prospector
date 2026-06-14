// Finanças (Organizador Financeiro pessoal).
//
// Domínio grande — candidato a sub-divisão futura (conta / transacao / cartao /
// recorrencia / orcamento / resumo / boleto). Ver docs/ORGANIZACAO_REFATORACAO.md.

// ── Contas ──────────────────────────────────────────────────────────
export interface Conta {
  id: string;
  usuario_id: string;
  nome: string;
  tipo: string;
  saldo_atual: string;
  meta?: string | null;
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
  meta?: string | null;
}

export interface ContaUpdateInput {
  nome?: string;
  tipo?: TipoConta;
  ativa?: boolean;
  meta?: string | null;
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
  multa_percentual?: string | null;
  juros_mensal_percentual?: string | null;
  encargos_pagos?: string | null;
  linha_digitavel?: string | null;
  desconto_valor?: string | null;
  desconto_ate?: string | null;
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
  data_vencimento?: string | null;
  multa_percentual?: string | null;
  juros_mensal_percentual?: string | null;
  encargos_pagos?: string | null;
  linha_digitavel?: string | null;
  desconto_valor?: string | null;
  desconto_ate?: string | null;
  status: string;
  categoria_id?: string | null;
  recorrencia_id?: string | null;
  pagamentos?: TransacaoPagamento[];
  itens?: { id: string; descricao: string; valor: string; categoria_id?: string | null }[];
}

export interface VerbaInput {
  descricao: string;
  valor: string;
}

/** Edição de uma conta a pagar (prevista) — não mexe no saldo. */
export interface PrevistaUpdateInput {
  descricao: string;
  valor_total: string;
  categoria_id?: string | null;
  data_vencimento?: string | null;
  multa_percentual?: string | null;
  juros_mensal_percentual?: string | null;
  itens?: VerbaInput[] | null;
  recorrencia_id?: string | null;
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

// ── Orçamentos ──────────────────────────────────────────────────────
export interface Orcamento {
  id: string;
  usuario_id: string;
  categoria_id: string;
  categoria_nome?: string | null;
  valor_mensal: string;
  ativo: boolean;
}

export interface OrcamentoListResponse {
  items: Orcamento[];
  total: number;
}

export interface OrcamentoStatusItem {
  orcamento_id: string;
  categoria_id: string;
  categoria_nome?: string | null;
  valor_mensal: string;
  consumido: string;
  restante: string;
  percentual: number;
}

export interface OrcamentoStatusResponse {
  competencia: string;
  items: OrcamentoStatusItem[];
  total_orcado: string;
  total_consumido: string;
}

export interface OrcamentoCreateInput {
  categoria_id: string;
  valor_mensal: string;
}

export interface OrcamentoUpdateInput {
  valor_mensal?: string;
  ativo?: boolean;
}

// ── Pagar o mês (boletos + faturas juntos) ─────────────────────────
export interface PagamentoMesItem {
  tipo: 'boleto' | 'fatura';
  id: string;
  descricao: string;
  valor: string;
  vencimento?: string | null;
  conta_sugerida_id?: string | null;
  conta_sugerida_nome?: string | null;
}

export interface PagamentoMesPreview {
  competencia: string;
  itens: PagamentoMesItem[];
  total: string;
}

export interface PagamentoMesItemInput {
  tipo: 'boleto' | 'fatura';
  id: string;
  conta_id: string;
}

export interface PagamentoMesResultado {
  pagos: number;
  total_pago: string;
  falhas: string[];
}

export interface NluInterpretacao {
  tipo: string;
  valor: string;
  descricao: string;
  data: string;
  conta_id?: string | null;
  conta_nome?: string | null;
  categoria_id?: string | null;
  categoria_nome?: string | null;
  texto_original: string;
}

export interface PagamentoInput {
  conta_id: string;
  valor: string;
}

export interface DespesaDivididaInput {
  descricao: string;
  valor_total: string;
  pagamentos: PagamentoInput[];
  categoria_id?: string | null;
  data_competencia?: string | null;
  status?: 'paga' | 'prevista';
}

export interface PixParse {
  valor?: string | null;
  beneficiario?: string | null;
  cidade?: string | null;
  chave?: string | null;
}

export interface DespesaAutoSplitInput {
  descricao: string;
  valor_total: string;
  conta_vr_id: string;
  conta_fallback_id: string;
  categoria_id?: string | null;
  data_competencia?: string | null;
  notas?: string | null;
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
  forma_pagamento: string;
  cartao_id?: string | null;
  ativa: boolean;
}

export interface RecorrenciaStatusItem {
  recorrencia_id: string;
  descricao: string;
  forma_pagamento: string;
  valor_estimado: string;
  dia_vencimento: number;
  cartao_id?: string | null;
  situacao: 'paga' | 'prevista' | 'atrasada' | 'lancada_cartao' | 'nenhuma';
  transacao_id?: string | null;
  compra_id?: string | null;
}

export interface RecorrenciaStatusResponse {
  competencia: string;
  items: RecorrenciaStatusItem[];
}

export interface PagarMesInput {
  competencia?: string | null;
  conta_id?: string | null;
  data_pagamento?: string | null;
  valor_pago?: string | null;
}

export interface RecorrenciaListResponse {
  items: Recorrencia[];
  total: number;
}

export type FormaPagamento = 'conta' | 'cartao' | 'boleto';

export interface RecorrenciaCreateInput {
  descricao: string;
  tipo: 'despesa' | 'receita';
  valor_estimado: string;
  dia_vencimento: number;
  categoria_id?: string | null;
  conta_id?: string | null;
  forma_pagamento?: FormaPagamento;
  cartao_id?: string | null;
}

export interface RecorrenciaUpdateInput {
  descricao?: string;
  tipo?: 'despesa' | 'receita';
  valor_estimado?: string;
  dia_vencimento?: number;
  categoria_id?: string | null;
  conta_id?: string | null;
  forma_pagamento?: FormaPagamento;
  cartao_id?: string | null;
  ativa?: boolean;
}

// ── Categorias ──────────────────────────────────────────────────────
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

// ── Resumo / Relatório / Projeção ───────────────────────────────────
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

export interface ProjecaoMes {
  ano: number;
  mes: number;
  saldo_atual: string;
  a_pagar: string;
  a_receber: string;
  estimativa_sobra: string;
}

// ── Cartões / Faturas / Compras ─────────────────────────────────────
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

export interface FaturaExtratoItem {
  parcela_id: string;
  compra_id: string;
  descricao: string;
  numero: number;
  total_parcelas: number;
  valor: string;
  valor_juros: string;
  vencimento: string;
  categoria_id?: string | null;
  categoria_nome?: string | null;
}

export interface FaturaExtrato {
  fatura: Fatura;
  cartao_nome: string;
  itens: FaturaExtratoItem[];
  total_juros: string;
}

export interface Parcela {
  id: string;
  numero: number;
  total_parcelas: number;
  valor: string;
  tem_juros: boolean;
  valor_juros: string;
  vencimento: string;
  fatura_id?: string | null;
}

export interface Compra {
  id: string;
  usuario_id: string;
  cartao_id?: string | null;
  descricao: string;
  valor_total: string;
  total_parcelas: number;
  data_compra: string;
  origem: string;
  categoria_id?: string | null;
  parcelas: Parcela[];
}

export interface PagarFaturaInput {
  conta_id: string;
  data_pagamento?: string | null;
  valor_pago?: string | null;
  categoria_id?: string | null;
}

export interface ProjecaoMesItem {
  mes_referencia: string; // "YYYY-MM-01"
  total: string;
}

export interface ProjecaoFaturas {
  meses: ProjecaoMesItem[];
  total: string;
}

export interface CompraCategoriaSugestao {
  categoria_id?: string | null;
  categoria_nome?: string | null;
}

export interface CompraCreateInput {
  cartao_id: string;
  descricao: string;
  valor_total: string;
  total_parcelas: number;
  data_compra?: string | null;
  categoria_id?: string | null;
  valor_juros_total?: string;
}

// ── Leituras de consumo (água/gás/luz) ──────────────────────────────
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

export interface LeituraCreateInput {
  tipo: 'agua' | 'gas' | 'luz';
  mes_referencia: string;
  leitura_atual: string;
  leitura_anterior?: string | null;
  consumo?: string | null;
  valor?: string | null;
}

// ── Comprovantes ────────────────────────────────────────────────────
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
  linha_digitavel?: string | null;
  verbas: VerbaBoleto[];
  leituras: LeituraBoleto[];
}

export interface ImportarBoletoResponse {
  success: boolean;
  conferido: boolean;
  duplicado?: boolean;
  mensagem: string;
  comprovante_id?: string | null;
  transacao_id?: string | null;
  extraido?: BoletoExtraido | null;
}

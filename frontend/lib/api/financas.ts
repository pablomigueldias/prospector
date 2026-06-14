// Finanças — leitura (contas/resumo/relatório/cartões/leituras/comprovantes),
// escrita (CRUD pela web), recorrências, pagar-o-mês, orçamentos e importador
// de boleto. Domínio grande; candidato a sub-divisão futura.

import { request } from './client';
import { FINANCAS_USUARIO_ID } from '../financas';
import type {
  Cartao,
  CartaoCreateInput,
  CartaoUpdateInput,
  Conta,
  ContaCreateInput,
  ContaUpdateInput,
  CategoriaCreateInput,
  CategoriaResponse,
  CategoriaTreeResponse,
  CategoriaUpdateInput,
  LancamentoInput,
  DespesaAutoSplitInput,
  DespesaDivididaInput,
  NluInterpretacao,
  PagamentoMesPreview,
  PagamentoMesItemInput,
  PagamentoMesResultado,
  Orcamento,
  OrcamentoListResponse,
  OrcamentoStatusResponse,
  OrcamentoCreateInput,
  OrcamentoUpdateInput,
  Recorrencia,
  RecorrenciaCreateInput,
  RecorrenciaListResponse,
  RecorrenciaStatusItem,
  RecorrenciaStatusResponse,
  PagarMesInput,
  RecorrenciaUpdateInput,
  TransacaoEditInput,
  TransacaoFiltro,
  TransacaoListResponse,
  TransacaoResponse,
  ContaListResponse,
  ProjecaoMes,
  ResumoMes,
  RelatorioResponse,
  CartaoListResponse,
  FaturasCartao,
  FaturaExtrato,
  Compra,
  CompraCreateInput,
  Fatura,
  CompraCategoriaSugestao,
  PagarFaturaInput,
  PixParse,
  ProjecaoFaturas,
  LeituraConsumoListResponse,
  LeituraConsumo,
  LeituraCreateInput,
  Comprovante,
  ComprovanteListResponse,
  ImportarBoletoResponse,
  PrevistaUpdateInput,
} from '../types';

export const financasApi = {
  financasContas(usuarioId: string, apenasAtivas = false): Promise<ContaListResponse> {
    const q = new URLSearchParams({
      usuario_id: usuarioId,
      apenas_ativas: String(apenasAtivas),
    });
    return request<ContaListResponse>(`/api/financas/contas?${q}`, {
      timeoutMs: 10_000,
    });
  },

  financasResumo(usuarioId: string, ano: number, mes: number): Promise<ResumoMes> {
    const q = new URLSearchParams({
      usuario_id: usuarioId,
      ano: String(ano),
      mes: String(mes),
    });
    return request<ResumoMes>(`/api/financas/resumo?${q}`, { timeoutMs: 10_000 });
  },

  /** GET /api/financas/resumo/projecao — sobra estimada do fim do mês */
  financasProjecaoMes(ano: number, mes: number): Promise<ProjecaoMes> {
    const q = new URLSearchParams({
      usuario_id: FINANCAS_USUARIO_ID,
      ano: String(ano),
      mes: String(mes),
    });
    return request<ProjecaoMes>(`/api/financas/resumo/projecao?${q}`, {
      timeoutMs: 10_000,
    });
  },

  /** GET /api/financas/resumo/relatorio — série mês a mês + top categorias.
   *  Recorte opcional por conta e/ou categoria. */
  financasRelatorio(
    usuarioId: string,
    ano: number,
    mes: number,
    meses = 6,
    filtro?: { contaId?: string; categoriaId?: string },
  ): Promise<RelatorioResponse> {
    const q = new URLSearchParams({
      usuario_id: usuarioId,
      ano: String(ano),
      mes: String(mes),
      meses: String(meses),
    });
    if (filtro?.contaId) q.set('conta_id', filtro.contaId);
    if (filtro?.categoriaId) q.set('categoria_id', filtro.categoriaId);
    return request<RelatorioResponse>(`/api/financas/resumo/relatorio?${q}`, {
      timeoutMs: 10_000,
    });
  },

  financasCartoes(usuarioId: string): Promise<CartaoListResponse> {
    const q = new URLSearchParams({ usuario_id: usuarioId });
    return request<CartaoListResponse>(`/api/financas/cartoes?${q}`, {
      timeoutMs: 10_000,
    });
  },

  financasCartaoFaturas(cartaoId: string): Promise<FaturasCartao> {
    return request<FaturasCartao>(
      `/api/financas/cartoes/${encodeURIComponent(cartaoId)}/faturas`,
      { timeoutMs: 10_000 },
    );
  },

  financasFaturaExtrato(cartaoId: string, faturaId: string): Promise<FaturaExtrato> {
    return request<FaturaExtrato>(
      `/api/financas/cartoes/${encodeURIComponent(cartaoId)}/faturas/${encodeURIComponent(faturaId)}`,
      { timeoutMs: 10_000 },
    );
  },

  financasCriarCartao(body: CartaoCreateInput): Promise<Cartao> {
    return request<Cartao>('/api/financas/cartoes', {
      method: 'POST',
      body: { usuario_id: FINANCAS_USUARIO_ID, ...body },
      timeoutMs: 10_000,
    });
  },

  financasAtualizarCartao(id: string, body: CartaoUpdateInput): Promise<Cartao> {
    return request<Cartao>(`/api/financas/cartoes/${encodeURIComponent(id)}`, {
      method: 'PATCH',
      body,
      timeoutMs: 10_000,
    });
  },

  financasExcluirCartao(id: string): Promise<void> {
    return request<void>(`/api/financas/cartoes/${encodeURIComponent(id)}`, {
      method: 'DELETE',
      timeoutMs: 10_000,
    });
  },

  financasCriarCompra(body: CompraCreateInput): Promise<Compra> {
    return request<Compra>('/api/financas/compras', {
      method: 'POST',
      body: { usuario_id: FINANCAS_USUARIO_ID, ...body },
      timeoutMs: 10_000,
    });
  },

  financasCompra(id: string): Promise<Compra> {
    return request<Compra>(`/api/financas/compras/${encodeURIComponent(id)}`, {
      timeoutMs: 10_000,
    });
  },

  /** DELETE /api/financas/compras/{id} — estorna a compra (remove parcelas e
   *  abate das faturas). 400 se alguma parcela já entrou em fatura paga. */
  financasExcluirCompra(id: string): Promise<void> {
    return request<void>(`/api/financas/compras/${encodeURIComponent(id)}`, {
      method: 'DELETE',
      timeoutMs: 10_000,
    });
  },

  /** GET /api/financas/compras/sugestao-categoria — categoria da última compra
   *  com a mesma descrição (auto-categoria do cartão). */
  financasSugestaoCategoriaCompra(
    descricao: string,
  ): Promise<CompraCategoriaSugestao> {
    const q = new URLSearchParams({
      usuario_id: FINANCAS_USUARIO_ID,
      descricao,
    });
    return request<CompraCategoriaSugestao>(
      `/api/financas/compras/sugestao-categoria?${q}`,
      { timeoutMs: 8_000 },
    );
  },

  /** GET /api/financas/cartoes/projecao — comprometido por mês (todos os cartões) */
  financasProjecaoCartoes(meses = 6): Promise<ProjecaoFaturas> {
    const q = new URLSearchParams({
      usuario_id: FINANCAS_USUARIO_ID,
      meses: String(meses),
    });
    return request<ProjecaoFaturas>(`/api/financas/cartoes/projecao?${q}`, {
      timeoutMs: 10_000,
    });
  },

  financasPagarFatura(
    cartaoId: string,
    faturaId: string,
    body: PagarFaturaInput,
  ): Promise<Fatura> {
    return request<Fatura>(
      `/api/financas/cartoes/${encodeURIComponent(cartaoId)}/faturas/${encodeURIComponent(faturaId)}/pagar`,
      { method: 'POST', body, timeoutMs: 10_000 },
    );
  },

  financasLeituras(usuarioId: string, tipo?: string): Promise<LeituraConsumoListResponse> {
    const q = new URLSearchParams({ usuario_id: usuarioId });
    if (tipo) q.set('tipo', tipo);
    return request<LeituraConsumoListResponse>(`/api/financas/leituras?${q}`, {
      timeoutMs: 10_000,
    });
  },

  financasCriarLeitura(body: LeituraCreateInput): Promise<LeituraConsumo> {
    return request<LeituraConsumo>('/api/financas/leituras', {
      method: 'POST',
      body: { usuario_id: FINANCAS_USUARIO_ID, ...body },
      timeoutMs: 10_000,
    });
  },

  /** GET /api/financas/comprovantes?transacao_id=… — anexos de uma transação */
  financasComprovantesDaTransacao(
    transacaoId: string,
  ): Promise<ComprovanteListResponse> {
    return request<ComprovanteListResponse>(
      `/api/financas/comprovantes?transacao_id=${encodeURIComponent(transacaoId)}`,
      { timeoutMs: 10_000 },
    );
  },

  /** POST /api/financas/comprovantes — anexa um arquivo a uma transação */
  financasAnexarComprovante(
    transacaoId: string,
    file: File,
    tipo = 'comprovante',
  ): Promise<Comprovante> {
    const form = new FormData();
    form.append('tipo', tipo);
    form.append('file', file);
    form.append('transacao_id', transacaoId);
    return request<Comprovante>('/api/financas/comprovantes', {
      method: 'POST',
      body: form,
      timeoutMs: 60_000,
    });
  },

  financasComprovantes(usuarioId: string, tipo?: string): Promise<ComprovanteListResponse> {
    const q = new URLSearchParams({ usuario_id: usuarioId });
    if (tipo) q.set('tipo', tipo);
    return request<ComprovanteListResponse>(`/api/financas/comprovantes?${q}`, {
      timeoutMs: 10_000,
    });
  },

  // ── Escrita (CRUD pela web) ─────────────────────────────────────
  /** POST /api/financas/contas — cria conta. O `usuario_id` do corpo é
   *  ignorado pelo backend (dono = sessão), mas precisa estar presente. */
  financasCriarConta(body: ContaCreateInput): Promise<Conta> {
    return request<Conta>('/api/financas/contas', {
      method: 'POST',
      body: { usuario_id: FINANCAS_USUARIO_ID, ...body },
      timeoutMs: 10_000,
    });
  },

  /** PATCH /api/financas/contas/{id} — renomeia / muda tipo / ativa-inativa */
  financasAtualizarConta(id: string, body: ContaUpdateInput): Promise<Conta> {
    return request<Conta>(`/api/financas/contas/${encodeURIComponent(id)}`, {
      method: 'PATCH',
      body,
      timeoutMs: 10_000,
    });
  },

  /** DELETE /api/financas/contas/{id} — remove a conta (204) */
  financasExcluirConta(id: string): Promise<void> {
    return request<void>(`/api/financas/contas/${encodeURIComponent(id)}`, {
      method: 'DELETE',
      timeoutMs: 10_000,
    });
  },

  /** GET /api/financas/transacoes — lista filtrável (mês/conta/categoria/tipo/busca) */
  financasTransacoes(filtro: TransacaoFiltro = {}): Promise<TransacaoListResponse> {
    const q = new URLSearchParams();
    if (filtro.ano) q.set('ano', String(filtro.ano));
    if (filtro.mes) q.set('mes', String(filtro.mes));
    if (filtro.conta_id) q.set('conta_id', filtro.conta_id);
    if (filtro.categoria_id) q.set('categoria_id', filtro.categoria_id);
    if (filtro.tipo) q.set('tipo', filtro.tipo);
    if (filtro.status) filtro.status.forEach((s) => q.append('status', s));
    if (filtro.busca) q.set('busca', filtro.busca);
    if (filtro.por_vencimento) q.set('por_vencimento', 'true');
    if (filtro.limit != null) q.set('limit', String(filtro.limit));
    if (filtro.offset != null) q.set('offset', String(filtro.offset));
    const qs = q.toString();
    return request<TransacaoListResponse>(
      `/api/financas/transacoes${qs ? `?${qs}` : ''}`,
      { timeoutMs: 10_000 },
    );
  },

  /** POST /api/financas/transacoes/despesa — lança despesa simples */
  financasLancarDespesa(body: LancamentoInput): Promise<TransacaoResponse> {
    return request<TransacaoResponse>('/api/financas/transacoes/despesa', {
      method: 'POST',
      body: { usuario_id: FINANCAS_USUARIO_ID, ...body },
      timeoutMs: 10_000,
    });
  },

  /** POST /api/financas/nlu/interpretar — texto livre → rascunho (não grava) */
  financasNluInterpretar(texto: string): Promise<NluInterpretacao> {
    return request<NluInterpretacao>('/api/financas/nlu/interpretar', {
      method: 'POST',
      body: { usuario_id: FINANCAS_USUARIO_ID, texto },
      timeoutMs: 30_000,
    });
  },

  /** POST /api/financas/transacoes/despesa/dividida — despesa paga por N contas */
  financasLancarDespesaDividida(
    body: DespesaDivididaInput,
  ): Promise<TransacaoResponse> {
    return request<TransacaoResponse>('/api/financas/transacoes/despesa/dividida', {
      method: 'POST',
      body: { usuario_id: FINANCAS_USUARIO_ID, ...body },
      timeoutMs: 10_000,
    });
  },

  /** POST /api/financas/transacoes/despesa/auto-split — esgota o VR/VA e joga o
   *  resto no dinheiro. Sempre paga. */
  financasLancarDespesaAutoSplit(
    body: DespesaAutoSplitInput,
  ): Promise<TransacaoResponse> {
    return request<TransacaoResponse>('/api/financas/transacoes/despesa/auto-split', {
      method: 'POST',
      body: { usuario_id: FINANCAS_USUARIO_ID, ...body },
      timeoutMs: 10_000,
    });
  },

  /** POST /api/financas/pix/parse — lê um PIX copia-e-cola (valor/beneficiário) */
  financasParsePix(codigo: string): Promise<PixParse> {
    return request<PixParse>('/api/financas/pix/parse', {
      method: 'POST',
      body: { codigo },
      timeoutMs: 8_000,
    });
  },

  /** POST /api/financas/transacoes/transferencia — move entre contas (reserva) */
  financasTransferir(body: {
    origem_conta_id: string;
    destino_conta_id: string;
    valor: string;
    descricao?: string | null;
    data?: string | null;
  }): Promise<{ origem_conta_id: string; destino_conta_id: string; valor: string }> {
    return request('/api/financas/transacoes/transferencia', {
      method: 'POST',
      body: { usuario_id: FINANCAS_USUARIO_ID, ...body },
      timeoutMs: 10_000,
    });
  },

  /** POST /api/financas/transacoes/receita — lança receita simples */
  financasLancarReceita(body: LancamentoInput): Promise<TransacaoResponse> {
    return request<TransacaoResponse>('/api/financas/transacoes/receita', {
      method: 'POST',
      body: { usuario_id: FINANCAS_USUARIO_ID, ...body },
      timeoutMs: 10_000,
    });
  },

  /** GET /api/financas/transacoes/{id} — detalhe (traz os pagamentos/conta) */
  financasTransacao(id: string): Promise<TransacaoResponse> {
    return request<TransacaoResponse>(
      `/api/financas/transacoes/${encodeURIComponent(id)}`,
      { timeoutMs: 10_000 },
    );
  },

  /** PATCH /api/financas/transacoes/{id} — edita e reajusta o saldo */
  financasEditarTransacao(
    id: string,
    body: TransacaoEditInput,
  ): Promise<TransacaoResponse> {
    return request<TransacaoResponse>(
      `/api/financas/transacoes/${encodeURIComponent(id)}`,
      { method: 'PATCH', body, timeoutMs: 10_000 },
    );
  },

  /** POST /api/financas/transacoes/{id}/tornar-recorrente — cria uma conta
   *  fixa (recorrência) a partir do boleto e liga a transação a ela. */
  financasTornarRecorrente(id: string): Promise<Recorrencia> {
    return request<Recorrencia>(
      `/api/financas/transacoes/${encodeURIComponent(id)}/tornar-recorrente`,
      { method: 'POST', timeoutMs: 10_000 },
    );
  },

  /** GET /api/financas/transacoes/{id}/sugestao-conta — conta sugerida pra
   *  pagar (a última usada com o mesmo beneficiário). */
  financasSugestaoConta(
    id: string,
  ): Promise<{ conta_id: string | null; conta_nome: string | null }> {
    return request(
      `/api/financas/transacoes/${encodeURIComponent(id)}/sugestao-conta`,
      { timeoutMs: 10_000 },
    );
  },

  /** PATCH /api/financas/transacoes/{id}/conta-a-pagar — edita uma conta a
   *  pagar (prevista): detalha verbas, ajusta valor/categoria/vencimento/encargos.
   *  Não mexe no saldo (ainda não foi paga). */
  financasEditarPrevista(
    id: string,
    body: PrevistaUpdateInput,
  ): Promise<TransacaoResponse> {
    return request<TransacaoResponse>(
      `/api/financas/transacoes/${encodeURIComponent(id)}/conta-a-pagar`,
      { method: 'PATCH', body, timeoutMs: 10_000 },
    );
  },

  /** POST /api/financas/transacoes/{id}/pagar — marca a prevista como paga e
   *  move o saldo. `contaId` só é exigido quando a transação ainda não tem
   *  conta (boleto importado / recorrência). */
  financasPagarTransacao(
    id: string,
    opts: {
      contaId?: string;
      dataPagamento?: string;
      multaPercentual?: string | null;
      jurosMensalPercentual?: string | null;
      valorPago?: string | null;
    } = {},
  ): Promise<TransacaoResponse> {
    return request<TransacaoResponse>(
      `/api/financas/transacoes/${encodeURIComponent(id)}/pagar`,
      {
        method: 'POST',
        body: {
          conta_id: opts.contaId || null,
          data_pagamento: opts.dataPagamento || null,
          multa_percentual: opts.multaPercentual ?? null,
          juros_mensal_percentual: opts.jurosMensalPercentual ?? null,
          valor_pago: opts.valorPago ?? null,
        },
        timeoutMs: 10_000,
      },
    );
  },

  /** DELETE /api/financas/transacoes/{id} — exclui e reverte saldo (204) */
  financasExcluirTransacao(id: string): Promise<void> {
    return request<void>(`/api/financas/transacoes/${encodeURIComponent(id)}`, {
      method: 'DELETE',
      timeoutMs: 10_000,
    });
  },

  /** GET /api/financas/categorias — árvore de categorias */
  financasCategorias(): Promise<CategoriaTreeResponse> {
    return request<CategoriaTreeResponse>('/api/financas/categorias', {
      timeoutMs: 10_000,
    });
  },

  /** POST /api/financas/categorias — cria categoria (raiz ou subverba) */
  financasCriarCategoria(body: CategoriaCreateInput): Promise<CategoriaResponse> {
    return request<CategoriaResponse>('/api/financas/categorias', {
      method: 'POST',
      body,
      timeoutMs: 10_000,
    });
  },

  /** PATCH /api/financas/categorias/{id} — renomeia / move / ativa-inativa */
  financasAtualizarCategoria(
    id: string,
    body: CategoriaUpdateInput,
  ): Promise<CategoriaResponse> {
    return request<CategoriaResponse>(
      `/api/financas/categorias/${encodeURIComponent(id)}`,
      { method: 'PATCH', body, timeoutMs: 10_000 },
    );
  },

  /** DELETE /api/financas/categorias/{id} — remove a categoria (204) */
  financasExcluirCategoria(id: string): Promise<void> {
    return request<void>(
      `/api/financas/categorias/${encodeURIComponent(id)}`,
      { method: 'DELETE', timeoutMs: 10_000 },
    );
  },

  // ── Recorrências (despesas/receitas fixas) ──────────────────────
  financasRecorrencias(): Promise<RecorrenciaListResponse> {
    return request<RecorrenciaListResponse>('/api/financas/recorrencias', {
      timeoutMs: 10_000,
    });
  },

  financasCriarRecorrencia(body: RecorrenciaCreateInput): Promise<Recorrencia> {
    return request<Recorrencia>('/api/financas/recorrencias', {
      method: 'POST',
      body: { usuario_id: FINANCAS_USUARIO_ID, ...body },
      timeoutMs: 10_000,
    });
  },

  financasAtualizarRecorrencia(
    id: string,
    body: RecorrenciaUpdateInput,
  ): Promise<Recorrencia> {
    return request<Recorrencia>(
      `/api/financas/recorrencias/${encodeURIComponent(id)}`,
      { method: 'PATCH', body, timeoutMs: 10_000 },
    );
  },

  financasExcluirRecorrencia(id: string): Promise<void> {
    return request<void>(
      `/api/financas/recorrencias/${encodeURIComponent(id)}`,
      { method: 'DELETE', timeoutMs: 10_000 },
    );
  },

  // ── Pagar o mês (boletos + faturas juntos) ──────────────────────
  financasPagarMesPreview(competencia?: string): Promise<PagamentoMesPreview> {
    const q = competencia ? `?competencia=${encodeURIComponent(competencia)}` : '';
    return request<PagamentoMesPreview>(`/api/financas/pagar-mes/preview${q}`, {
      timeoutMs: 15_000,
    });
  },

  financasPagarMes(
    itens: PagamentoMesItemInput[],
    dataPagamento?: string,
  ): Promise<PagamentoMesResultado> {
    return request<PagamentoMesResultado>('/api/financas/pagar-mes', {
      method: 'POST',
      body: { data_pagamento: dataPagamento ?? null, itens },
      timeoutMs: 30_000,
    });
  },

  // ── Orçamentos (teto mensal por categoria) ──────────────────────
  financasOrcamentos(): Promise<OrcamentoListResponse> {
    return request<OrcamentoListResponse>('/api/financas/orcamentos', {
      timeoutMs: 10_000,
    });
  },

  financasOrcamentosStatus(competencia?: string): Promise<OrcamentoStatusResponse> {
    const q = competencia ? `?competencia=${encodeURIComponent(competencia)}` : '';
    return request<OrcamentoStatusResponse>(`/api/financas/orcamentos/status${q}`, {
      timeoutMs: 10_000,
    });
  },

  financasCriarOrcamento(body: OrcamentoCreateInput): Promise<Orcamento> {
    return request<Orcamento>('/api/financas/orcamentos', {
      method: 'POST',
      body: { usuario_id: FINANCAS_USUARIO_ID, ...body },
      timeoutMs: 10_000,
    });
  },

  financasAtualizarOrcamento(
    id: string,
    body: OrcamentoUpdateInput,
  ): Promise<Orcamento> {
    return request<Orcamento>(`/api/financas/orcamentos/${encodeURIComponent(id)}`, {
      method: 'PATCH',
      body,
      timeoutMs: 10_000,
    });
  },

  financasExcluirOrcamento(id: string): Promise<void> {
    return request<void>(`/api/financas/orcamentos/${encodeURIComponent(id)}`, {
      method: 'DELETE',
      timeoutMs: 10_000,
    });
  },

  financasProcessarRecorrencias(): Promise<{
    previstas_criadas: number;
    marcadas_atrasadas: number;
  }> {
    return request('/api/financas/recorrencias/processar', {
      method: 'POST',
      timeoutMs: 15_000,
    });
  },

  financasRecorrenciasStatus(
    competencia?: string,
  ): Promise<RecorrenciaStatusResponse> {
    const q = competencia ? `?competencia=${encodeURIComponent(competencia)}` : '';
    return request<RecorrenciaStatusResponse>(
      `/api/financas/recorrencias/status${q}`,
      { timeoutMs: 10_000 },
    );
  },

  financasPagarMesRecorrencia(
    id: string,
    body: PagarMesInput,
  ): Promise<RecorrenciaStatusItem> {
    return request<RecorrenciaStatusItem>(
      `/api/financas/recorrencias/${encodeURIComponent(id)}/pagar-mes`,
      { method: 'POST', body, timeoutMs: 10_000 },
    );
  },

  // ── Importador de boleto (LLM multimodal) ───────────────────────
  /** POST /api/financas/importar/boleto — sobe um boleto (PDF/foto), a IA lê
   *  e, se as verbas batem com o total, já cria a despesa prevista. */
  financasImportarBoleto(
    file: File,
    categoriaId?: string,
    opts?: { signal?: AbortSignal },
  ): Promise<ImportarBoletoResponse> {
    // O dono dos dados vem da sessão no backend; aqui só o arquivo e a
    // categoria opcional (pra etiquetar a despesa que será criada).
    const form = new FormData();
    form.append('file', file);
    if (categoriaId) form.append('categoria_id', categoriaId);
    return request<ImportarBoletoResponse>('/api/financas/importar/boleto', {
      method: 'POST',
      body: form,
      timeoutMs: 120_000,
      signal: opts?.signal,
    });
  },
};

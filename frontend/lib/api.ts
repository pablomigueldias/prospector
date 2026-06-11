import { ApiError } from './types';
import { FINANCAS_USUARIO_ID } from './financas';
import type {
  Agent,
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
  Recorrencia,
  RecorrenciaCreateInput,
  RecorrenciaListResponse,
  RecorrenciaUpdateInput,
  TransacaoFiltro,
  TransacaoListResponse,
  TransacaoResponse,
  CopywriterResponse,
  LeadHistoryResponse,
  ProspectorManualRequest,
  ProspectorPreviewResponse,
  ProspectorRunResponse,
  CopywriterRequest,
  EmailHistoryResponse,
  GerarRascunhosResponse,
  GerarFollowupsRequest,
  GerarFollowupsResponse,
  SyncResponse,
  PerfilMestre,
  Vaga,
  VagaCreate,
  VagaListResponse,
  AnalisarVagaResponse,
  GerarCandidaturaResponse,
  CandidaturaEmailItem,
  ContaListResponse,
  ResumoMes,
  CartaoListResponse,
  FaturasCartao,
  LeituraConsumoListResponse,
  ComprovanteListResponse,
  Usuario,
  UsuarioAdminItem,
  PapelItem,
} from './types';

const API_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, '') ||
  'http://localhost:8000';


const DEFAULT_TIMEOUT_MS = 180_000; // 3 min

/** Lê o cookie CSRF (legível pelo JS) — nomes dev/prod. */
function lerCookieCsrf(): string | null {
  if (typeof document === 'undefined') return null;
  for (const nome of ['__Host-csrf', 'csrf_token']) {
    const m = document.cookie.match(
      new RegExp('(?:^|; )' + nome.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '=([^;]*)'),
    );
    if (m) return decodeURIComponent(m[1]);
  }
  return null;
}

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  body?: unknown;
  timeoutMs?: number;
  signal?: AbortSignal;
}

async function request<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, timeoutMs = DEFAULT_TIMEOUT_MS, signal } = opts;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
  if (signal) {
    if (signal.aborted) controller.abort();
    else signal.addEventListener('abort', () => controller.abort());
  }

  const headers: Record<string, string> = {};
  if (body) headers['Content-Type'] = 'application/json';
  // CSRF (double-submit): em mutações, reenvia o cookie CSRF como header. O
  // backend só exige isso quando há cookie de sessão.
  if (method !== 'GET') {
    const csrf = lerCookieCsrf();
    if (csrf) headers['X-CSRF-Token'] = csrf;
  }

  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
      // Sempre manda o cookie de sessão (auth). Em prod é first-party (mesmo
      // domínio via Caddy); em dev é cross-port mas same-site, então o cookie
      // viaja com credentials:'include' + CORS allow_credentials no backend.
      credentials: 'include',
      signal: controller.signal,
    });
  } catch (err) {
    clearTimeout(timeoutId);
    if (err instanceof DOMException && err.name === 'AbortError') {
      throw new ApiError(
        'Tempo esgotado. A API demorou mais que o esperado.',
        0,
        `Timeout de ${Math.round(timeoutMs / 1000)}s atingido.`,
      );
    }
    throw new ApiError(
      'Não consegui falar com a API. Está rodando em ' + API_URL + '?',
      0,
      err instanceof Error ? err.message : String(err),
    );
  } finally {
    clearTimeout(timeoutId);
  }

  if (!response.ok) {
    let detail: string | null = null;
    try {
      const errBody = await response.json();
      detail = errBody?.detail ?? errBody?.error ?? null;
    } catch {
    }
    throw new ApiError(
      detail || `Erro HTTP ${response.status}`,
      response.status,
      detail,
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}



export const api = {
  /** GET /api/health */
  healthcheck(): Promise<{ status: string; service: string }> {
    return request('/api/health', { timeoutMs: 5000 });
  },

  /** GET /api/agents — lista todos os agentes da plataforma */
  listAgents(): Promise<Agent[]> {
    return request<Agent[]>('/api/agents', { timeoutMs: 10000 });
  },

  /** GET /api/agents/{slug} — detalhe de um agente */
  getAgent(slug: string): Promise<Agent> {
    return request<Agent>(`/api/agents/${encodeURIComponent(slug)}`, {
      timeoutMs: 10000,
    });
  },

  prospectorPreview(
    body: ProspectorManualRequest,
    opts?: { signal?: AbortSignal },
  ): Promise<ProspectorPreviewResponse> {
    return request<ProspectorPreviewResponse>(
      '/api/agents/prospector/preview',
      {
        method: 'POST',
        body,
        timeoutMs: 60_000,
        signal: opts?.signal,
      },
    );
  },

  copywriterGerar(
  body: CopywriterRequest,
  opts?: { signal?: AbortSignal },
  ): Promise<CopywriterResponse> {
  return request<CopywriterResponse>('/api/agents/copywriter/gerar', {
    method: 'POST',
    body,
    timeoutMs: 120_000,
    signal: opts?.signal,
  });
  },

  prospectorRun(
    body: ProspectorManualRequest,
    opts?: { signal?: AbortSignal },
  ): Promise<ProspectorRunResponse> {
    return request<ProspectorRunResponse>('/api/agents/prospector/manual', {
      method: 'POST',
      body,
      signal: opts?.signal,
    });
  },

  prospectorHistory(limit: number = 20): Promise<LeadHistoryResponse> {
    return request<LeadHistoryResponse>(
      `/api/agents/prospector/leads?limit=${limit}`,
      { timeoutMs: 10000 },
    );
  },

  outreachGerar(
    body: { limit?: number | null; pausa?: number },
    opts?: { signal?: AbortSignal },
  ): Promise<GerarRascunhosResponse> {
    return request<GerarRascunhosResponse>('/api/agents/outreach/gerar', {
      method: 'POST',
      body,
      timeoutMs: 600_000,
      signal: opts?.signal,
    });
  },

  outreachFollowups(
    body: GerarFollowupsRequest,
    opts?: { signal?: AbortSignal },
  ): Promise<GerarFollowupsResponse> {
    return request<GerarFollowupsResponse>('/api/agents/outreach/followups', {
      method: 'POST',
      body,
      timeoutMs: 600_000,
      signal: opts?.signal,
    });
  },

  outreachSync(opts?: { signal?: AbortSignal }): Promise<SyncResponse> {
    return request<SyncResponse>('/api/agents/outreach/sync', {
      method: 'POST',
      timeoutMs: 120_000,
      signal: opts?.signal,
    });
  },

  outreachEmails(limit: number = 50): Promise<EmailHistoryResponse> {
    return request<EmailHistoryResponse>(
      `/api/agents/outreach/emails?limit=${limit}`,
      { timeoutMs: 15_000 },
    );
  },

  // ── Área pessoal: Perfil Mestre ─────────────────────────────────
  /** GET /api/pessoal/perfil — perfil ativo, ou null se não houver */
  perfilGet(): Promise<PerfilMestre | null> {
    return request<PerfilMestre | null>('/api/pessoal/perfil', {
      timeoutMs: 10_000,
    });
  },

  /** PUT /api/pessoal/perfil — cria/atualiza o perfil */
  perfilSalvar(body: PerfilMestre): Promise<PerfilMestre> {
    return request<PerfilMestre>('/api/pessoal/perfil', {
      method: 'PUT',
      body,
      timeoutMs: 15_000,
    });
  },

  // ── Área pessoal: Vagas ─────────────────────────────────────────
  vagasListar(status?: string): Promise<VagaListResponse> {
    const q = status ? `?status=${encodeURIComponent(status)}` : '';
    return request<VagaListResponse>(`/api/pessoal/vagas${q}`, {
      timeoutMs: 10_000,
    });
  },

  vagaCriar(body: VagaCreate): Promise<Vaga> {
    return request<Vaga>('/api/pessoal/vagas', {
      method: 'POST',
      body,
      timeoutMs: 15_000,
    });
  },

  vagaDetalhe(id: string): Promise<Vaga> {
    return request<Vaga>(`/api/pessoal/vagas/${encodeURIComponent(id)}`, {
      timeoutMs: 10_000,
    });
  },

  vagaAtualizar(id: string, body: Partial<Vaga>): Promise<Vaga> {
    return request<Vaga>(`/api/pessoal/vagas/${encodeURIComponent(id)}`, {
      method: 'PATCH',
      body,
      timeoutMs: 10_000,
    });
  },

  vagaRemover(id: string): Promise<void> {
    return request<void>(`/api/pessoal/vagas/${encodeURIComponent(id)}`, {
      method: 'DELETE',
      timeoutMs: 10_000,
    });
  },

  vagaAnalisar(id: string): Promise<AnalisarVagaResponse> {
    return request<AnalisarVagaResponse>(
      `/api/pessoal/vagas/${encodeURIComponent(id)}/analisar`,
      { method: 'POST', timeoutMs: 120_000 },
    );
  },

  vagaGerarCandidatura(
    id: string,
    body: { gerar_carta?: boolean; instrucoes_extra?: string | null },
  ): Promise<GerarCandidaturaResponse> {
    return request<GerarCandidaturaResponse>(
      `/api/pessoal/vagas/${encodeURIComponent(id)}/candidatura`,
      { method: 'POST', body, timeoutMs: 120_000 },
    );
  },

  vagaRascunhos(id: string): Promise<CandidaturaEmailItem[]> {
    return request<CandidaturaEmailItem[]>(
      `/api/pessoal/vagas/${encodeURIComponent(id)}/rascunhos`,
      { timeoutMs: 10_000 },
    );
  },

  // ── Finanças ────────────────────────────────────────────────────
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

  financasLeituras(usuarioId: string, tipo?: string): Promise<LeituraConsumoListResponse> {
    const q = new URLSearchParams({ usuario_id: usuarioId });
    if (tipo) q.set('tipo', tipo);
    return request<LeituraConsumoListResponse>(`/api/financas/leituras?${q}`, {
      timeoutMs: 10_000,
    });
  },

  financasComprovantes(usuarioId: string, tipo?: string): Promise<ComprovanteListResponse> {
    const q = new URLSearchParams({ usuario_id: usuarioId });
    if (tipo) q.set('tipo', tipo);
    return request<ComprovanteListResponse>(`/api/financas/comprovantes?${q}`, {
      timeoutMs: 10_000,
    });
  },

  // ── Finanças · escrita (CRUD pela web) ──────────────────────────
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
    if (filtro.busca) q.set('busca', filtro.busca);
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

  /** POST /api/financas/transacoes/receita — lança receita simples */
  financasLancarReceita(body: LancamentoInput): Promise<TransacaoResponse> {
    return request<TransacaoResponse>('/api/financas/transacoes/receita', {
      method: 'POST',
      body: { usuario_id: FINANCAS_USUARIO_ID, ...body },
      timeoutMs: 10_000,
    });
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

  // ── Finanças · recorrências (despesas/receitas fixas) ───────────
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

  // ── Dev tools (só habilitado fora de produção) ──────────────────
  /** POST /api/dev/sync-prod-to-dev — copia os dados da produção pro dev.
   *  DESTRUTIVO: substitui o banco de dev inteiro. 404 em produção. */
  devSyncProdToDev(): Promise<{ ok: boolean; mensagem: string; log: string }> {
    return request('/api/dev/sync-prod-to-dev', {
      method: 'POST',
      timeoutMs: 320_000,
    });
  },

  // ── Auth ────────────────────────────────────────────────────────
  /** POST /api/auth/login — seta o cookie de sessão e devolve o usuário.
   *  Se o usuário tiver 2FA, a 1ª chamada (sem codigo2fa) responde 401 com
   *  detail "2fa_requerido"; reenvie com o código. */
  authLogin(email: string, senha: string, codigo2fa?: string): Promise<Usuario> {
    return request<Usuario>('/api/auth/login', {
      method: 'POST',
      body: { email, senha, codigo_2fa: codigo2fa || null },
      timeoutMs: 15_000,
    });
  },

  /** GET /api/auth/me — usuário logado + permissões (401 se sem sessão) */
  authMe(): Promise<Usuario> {
    return request<Usuario>('/api/auth/me', { timeoutMs: 10_000 });
  },

  /** POST /api/auth/logout — encerra a sessão atual */
  authLogout(): Promise<{ ok: boolean; mensagem: string }> {
    return request('/api/auth/logout', { method: 'POST', timeoutMs: 10_000 });
  },

  /** POST /api/auth/logout-all — sai de todos os dispositivos */
  authLogoutAll(): Promise<{ ok: boolean; mensagem: string }> {
    return request('/api/auth/logout-all', { method: 'POST', timeoutMs: 10_000 });
  },

  /** POST /api/auth/senha — troca a senha (revoga as outras sessões) */
  authTrocarSenha(
    senhaAtual: string,
    senhaNova: string,
  ): Promise<{ ok: boolean; mensagem: string }> {
    return request('/api/auth/senha', {
      method: 'POST',
      body: { senha_atual: senhaAtual, senha_nova: senhaNova },
      timeoutMs: 15_000,
    });
  },

  // ── 2FA (TOTP) ──────────────────────────────────────────────────
  /** POST /api/auth/2fa/setup — gera secret + QR (ainda não ativa) */
  authTwofaSetup(): Promise<{
    secret: string;
    otpauth_uri: string;
    qr_data_uri: string;
  }> {
    return request('/api/auth/2fa/setup', { method: 'POST', timeoutMs: 15_000 });
  },

  /** POST /api/auth/2fa/ativar — confirma o código e devolve os backup codes */
  authTwofaAtivar(codigo: string): Promise<{ ok: boolean; backup_codes: string[] }> {
    return request('/api/auth/2fa/ativar', {
      method: 'POST',
      body: { codigo },
      timeoutMs: 15_000,
    });
  },

  /** POST /api/auth/2fa/desativar — exige senha + código */
  authTwofaDesativar(
    senha: string,
    codigo: string,
  ): Promise<{ ok: boolean; mensagem: string }> {
    return request('/api/auth/2fa/desativar', {
      method: 'POST',
      body: { senha, codigo },
      timeoutMs: 15_000,
    });
  },

  // ── Admin de usuários (exige usuarios.gerenciar) ─────────────────
  adminListarPapeis(): Promise<PapelItem[]> {
    return request('/api/admin/papeis', { timeoutMs: 10_000 });
  },

  adminListarUsuarios(): Promise<{ items: UsuarioAdminItem[]; total: number }> {
    return request('/api/admin/usuarios', { timeoutMs: 10_000 });
  },

  adminCriarUsuario(body: {
    email: string;
    nome: string;
    senha: string;
    papeis: string[];
  }): Promise<UsuarioAdminItem> {
    return request('/api/admin/usuarios', { method: 'POST', body, timeoutMs: 15_000 });
  },

  adminAtualizarUsuario(
    id: string,
    body: { nome?: string; ativo?: boolean; papeis?: string[] },
  ): Promise<UsuarioAdminItem> {
    return request(`/api/admin/usuarios/${id}`, {
      method: 'PATCH',
      body,
      timeoutMs: 15_000,
    });
  },
};

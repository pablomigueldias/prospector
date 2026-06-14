// Cliente HTTP compartilhado: monta a URL, anexa o cookie de sessão + header
// CSRF, trata timeout/erros e devolve JSON tipado. Cada módulo de domínio
// (financas.ts, auth.ts, …) usa o `request` daqui. Ver lib/api/index.ts.

import { ApiError } from '../types';

export const API_URL =
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

export interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  body?: unknown;
  timeoutMs?: number;
  signal?: AbortSignal;
}

export async function request<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, timeoutMs = DEFAULT_TIMEOUT_MS, signal } = opts;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
  if (signal) {
    if (signal.aborted) controller.abort();
    else signal.addEventListener('abort', () => controller.abort());
  }

  // FormData (upload) vai como multipart — deixa o browser pôr o boundary;
  // não serializa em JSON nem força Content-Type.
  const isFormData =
    typeof FormData !== 'undefined' && body instanceof FormData;

  const headers: Record<string, string> = {};
  if (body && !isFormData) headers['Content-Type'] = 'application/json';
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
      body: body ? (isFormData ? (body as FormData) : JSON.stringify(body)) : undefined,
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

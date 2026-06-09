import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

/**
 * Guarda de rota no edge — camada extra antes de carregar a página.
 *
 * Em PRODUÇÃO o front e a API ficam no mesmo domínio (Caddy), então o cookie
 * de sessão é first-party e o middleware consegue lê-lo (httpOnly não bloqueia
 * leitura no servidor, só no JS do browser). Sem cookie → manda pro /login.
 *
 * Em DEV o front (3000) e a API (8000) ficam em portas diferentes, então o
 * cookie não está no domínio do front e o middleware não o vê — por isso aqui
 * só atua em produção. Em dev quem protege é o AuthProvider (client-side).
 */
const PUBLIC_PREFIXES = ['/login'];

export function middleware(req: NextRequest) {
  if (process.env.NODE_ENV !== 'production') {
    return NextResponse.next();
  }

  const { pathname } = req.nextUrl;
  if (PUBLIC_PREFIXES.some((p) => pathname.startsWith(p))) {
    return NextResponse.next();
  }

  const temSessao =
    req.cookies.has('__Host-sessao') || req.cookies.has('sessao');
  if (!temSessao) {
    const url = req.nextUrl.clone();
    url.pathname = '/login';
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

// Aplica a tudo, menos assets internos do Next, a API e arquivos estáticos.
export const config = {
  matcher: ['/((?!_next/|api/|favicon.ico|.*\\.).*)'],
};

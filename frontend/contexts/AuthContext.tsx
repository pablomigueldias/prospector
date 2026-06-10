import { useRouter } from 'next/router';
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from 'react';

import { api } from '@/lib/api';
import type { Usuario } from '@/lib/types';

/**
 * Estado de autenticação do app. Guarda o usuário (e suas permissões) em
 * memória — NUNCA em localStorage. O token de sessão fica num cookie httpOnly
 * que o JS não enxerga; aqui só sabemos "quem é" via /api/auth/me.
 */
interface AuthState {
  usuario: Usuario | null;
  loading: boolean;
  login: (email: string, senha: string, codigo2fa?: string) => Promise<void>;
  logout: () => Promise<void>;
  /** UX only — a trava de verdade é no backend (require_permission). */
  hasPermission: (codigo: string) => boolean;
  refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthState | undefined>(undefined);

// Rotas que não exigem login.
const PUBLIC_ROUTES = ['/login'];

function FullScreenLoader() {
  return (
    <div className="min-h-screen grid place-items-center text-ink-mute text-sm">
      Carregando…
    </div>
  );
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [usuario, setUsuario] = useState<Usuario | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      setUsuario(await api.authMe());
    } catch {
      setUsuario(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const isPublic = PUBLIC_ROUTES.includes(router.pathname);

  // Guarda de rota (client-side): funciona em dev e prod. Em prod o
  // middleware.ts é uma camada extra antes mesmo de carregar a página.
  useEffect(() => {
    if (loading) return;
    if (!usuario && !isPublic) {
      void router.replace('/login');
    } else if (usuario && isPublic) {
      void router.replace('/');
    }
  }, [loading, usuario, isPublic, router]);

  const login = useCallback(
    async (email: string, senha: string, codigo2fa?: string) => {
      const u = await api.authLogin(email, senha, codigo2fa);
      setUsuario(u);
    },
    [],
  );

  const logout = useCallback(async () => {
    try {
      await api.authLogout();
    } finally {
      setUsuario(null);
      void router.replace('/login');
    }
  }, [router]);

  const hasPermission = useCallback(
    (codigo: string) => !!usuario?.permissoes.includes(codigo),
    [usuario],
  );

  // Evita flash de conteúdo protegido: enquanto carrega, ou logado-fora numa
  // rota protegida (o efeito acima já está redirecionando), mostra o loader.
  const blocking = loading || (!usuario && !isPublic);

  return (
    <AuthContext.Provider
      value={{ usuario, loading, login, logout, hasPermission, refresh }}
    >
      {blocking && !isPublic ? <FullScreenLoader /> : children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth precisa estar dentro de <AuthProvider>');
  return ctx;
}

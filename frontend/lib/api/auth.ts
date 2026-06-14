// Auth — login/sessão/senha, 2FA (TOTP) e admin de usuários.

import { request } from './client';
import type { Usuario, UsuarioAdminItem, PapelItem } from '../types';

export const authApi = {
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

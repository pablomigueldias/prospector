import Head from 'next/head';
import { useState, type FormEvent } from 'react';

import { useAuth } from '@/contexts/AuthContext';
import { ApiError } from '@/lib/types';

export default function LoginPage() {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [senha, setSenha] = useState('');
  const [codigo, setCodigo] = useState('');
  const [precisa2fa, setPrecisa2fa] = useState(false);
  const [erro, setErro] = useState('');
  const [enviando, setEnviando] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setErro('');
    setEnviando(true);
    try {
      await login(email.trim(), senha, precisa2fa ? codigo.trim() : undefined);
      // O AuthProvider redireciona pra "/" assim que o usuário entra.
    } catch (err) {
      if (err instanceof ApiError && err.detail === '2fa_requerido') {
        // Senha OK; agora pede o 2º fator (não revela isso antes da senha certa).
        setPrecisa2fa(true);
        setErro('');
      } else if (precisa2fa) {
        setErro('Código de verificação inválido.');
      } else {
        // Genérica (anti-enumeração) — não dizemos se foi email ou senha.
        setErro('Email ou senha inválidos.');
      }
      setEnviando(false);
    }
  }

  return (
    <>
      <Head>
        <title>Entrar · Reative Systems</title>
      </Head>
      <main className="min-h-screen grid place-items-center px-4 bg-bg">
        <div className="w-full max-w-sm">
          <div className="card p-8">
            <span className="eyebrow mb-6">Reative Systems</span>
            <h1 className="font-display text-2xl font-semibold tracking-tight text-ink mt-3">
              Entrar
            </h1>
            <p className="text-ink-mute text-sm mt-1 mb-6">
              Acesso restrito. Use sua conta.
            </p>

            <form onSubmit={onSubmit} className="flex flex-col gap-4">
              <label className="flex flex-col gap-1.5">
                <span className="text-xs font-medium text-ink-mute">Email</span>
                <input
                  type="email"
                  className="input"
                  autoComplete="username"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  autoFocus
                />
              </label>

              <label className="flex flex-col gap-1.5">
                <span className="text-xs font-medium text-ink-mute">Senha</span>
                <input
                  type="password"
                  className="input"
                  autoComplete="current-password"
                  value={senha}
                  onChange={(e) => setSenha(e.target.value)}
                  required
                  disabled={precisa2fa}
                />
              </label>

              {precisa2fa && (
                <label className="flex flex-col gap-1.5">
                  <span className="text-xs font-medium text-ink-mute">
                    Código de verificação (2FA)
                  </span>
                  <input
                    type="text"
                    inputMode="numeric"
                    autoComplete="one-time-code"
                    className="input tracking-widest"
                    placeholder="123456 ou backup code"
                    value={codigo}
                    onChange={(e) => setCodigo(e.target.value)}
                    required
                    autoFocus
                  />
                  <span className="text-xs text-ink-mute">
                    Abra seu app autenticador, ou use um código de backup.
                  </span>
                </label>
              )}

              {erro && (
                <p className="text-sm text-red-600" role="alert">
                  {erro}
                </p>
              )}

              <button
                type="submit"
                className="btn-primary justify-center mt-2"
                disabled={enviando}
              >
                {enviando
                  ? 'Entrando…'
                  : precisa2fa
                    ? 'Verificar código'
                    : 'Entrar'}
              </button>
            </form>
          </div>
        </div>
      </main>
    </>
  );
}

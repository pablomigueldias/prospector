import Head from 'next/head';
import { useState, type FormEvent } from 'react';

import { useAuth } from '@/contexts/AuthContext';

export default function LoginPage() {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [senha, setSenha] = useState('');
  const [erro, setErro] = useState('');
  const [enviando, setEnviando] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setErro('');
    setEnviando(true);
    try {
      await login(email.trim(), senha);
      // O AuthProvider redireciona pra "/" assim que o usuário entra.
    } catch {
      // Mensagem sempre genérica (anti-enumeração) — não dizemos se o email
      // existe ou se foi só a senha.
      setErro('Email ou senha inválidos.');
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
                />
              </label>

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
                {enviando ? 'Entrando…' : 'Entrar'}
              </button>
            </form>
          </div>
        </div>
      </main>
    </>
  );
}

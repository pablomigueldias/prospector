import Head from 'next/head';
import { useState, type FormEvent } from 'react';

import { DashboardLayout } from '@/components/DashboardLayout';
import { useAuth } from '@/contexts/AuthContext';
import { api } from '@/lib/api';
import { ApiError } from '@/lib/types';

export default function ContaPage() {
  const { usuario, logout } = useAuth();

  const [atual, setAtual] = useState('');
  const [nova, setNova] = useState('');
  const [nova2, setNova2] = useState('');
  const [msg, setMsg] = useState<{ tipo: 'ok' | 'erro'; texto: string } | null>(null);
  const [enviando, setEnviando] = useState(false);

  async function trocarSenha(e: FormEvent) {
    e.preventDefault();
    setMsg(null);
    if (nova !== nova2) {
      setMsg({ tipo: 'erro', texto: 'A confirmação não bate com a nova senha.' });
      return;
    }
    setEnviando(true);
    try {
      const r = await api.authTrocarSenha(atual, nova);
      setMsg({ tipo: 'ok', texto: r.mensagem });
      setAtual('');
      setNova('');
      setNova2('');
    } catch (err) {
      const texto =
        err instanceof ApiError ? err.message : 'Não consegui trocar a senha.';
      setMsg({ tipo: 'erro', texto });
    } finally {
      setEnviando(false);
    }
  }

  async function sairDeTodos() {
    try {
      await api.authLogoutAll();
    } finally {
      await logout();
    }
  }

  return (
    <>
      <Head>
        <title>Conta · Reative Systems</title>
      </Head>
      <DashboardLayout currentAgentName="Conta">
        <div className="max-w-lg mx-auto">
          <header className="mb-7">
            <div className="eyebrow mb-3">Conta</div>
            <h1 className="font-display font-semibold text-3xl tracking-tight text-ink mb-1">
              {usuario?.nome ?? 'Minha conta'}
            </h1>
            <p className="text-ink-mute text-sm">{usuario?.email}</p>
          </header>

          <section className="card p-6 mb-5">
            <h2 className="font-display font-semibold text-lg text-ink mb-4">
              Trocar senha
            </h2>
            <form onSubmit={trocarSenha} className="flex flex-col gap-4">
              <label className="flex flex-col gap-1.5">
                <span className="text-xs font-medium text-ink-mute">Senha atual</span>
                <input
                  type="password"
                  className="input"
                  autoComplete="current-password"
                  value={atual}
                  onChange={(e) => setAtual(e.target.value)}
                  required
                />
              </label>
              <label className="flex flex-col gap-1.5">
                <span className="text-xs font-medium text-ink-mute">
                  Nova senha (mín. 12 caracteres)
                </span>
                <input
                  type="password"
                  className="input"
                  autoComplete="new-password"
                  value={nova}
                  onChange={(e) => setNova(e.target.value)}
                  required
                />
              </label>
              <label className="flex flex-col gap-1.5">
                <span className="text-xs font-medium text-ink-mute">
                  Confirme a nova senha
                </span>
                <input
                  type="password"
                  className="input"
                  autoComplete="new-password"
                  value={nova2}
                  onChange={(e) => setNova2(e.target.value)}
                  required
                />
              </label>

              {msg && (
                <p
                  className={`text-sm ${msg.tipo === 'ok' ? 'text-success-ink' : 'text-red-600'}`}
                  role="alert"
                >
                  {msg.texto}
                </p>
              )}

              <button type="submit" className="btn-primary justify-center" disabled={enviando}>
                {enviando ? 'Trocando…' : 'Trocar senha'}
              </button>
            </form>
          </section>

          <section className="card p-6">
            <h2 className="font-display font-semibold text-lg text-ink mb-1">
              Sessões
            </h2>
            <p className="text-ink-mute text-sm mb-4">
              Encerra a sessão em todos os dispositivos (você precisará entrar de novo).
            </p>
            <button type="button" className="btn-ghost" onClick={() => void sairDeTodos()}>
              Sair de todos os dispositivos
            </button>
          </section>
        </div>
      </DashboardLayout>
    </>
  );
}

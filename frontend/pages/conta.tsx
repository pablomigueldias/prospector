import Head from 'next/head';
import { useState, type FormEvent } from 'react';

import { DashboardLayout } from '@/components/shared/DashboardLayout';
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

          <SecaoDoisFatores />

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

/** Verificação em duas etapas (TOTP): ativar (QR + backup codes) ou desativar. */
function SecaoDoisFatores() {
  const { usuario, refresh } = useAuth();
  const ativo = usuario?.twofa_ativado ?? false;

  const [setup, setSetup] = useState<
    { secret: string; otpauth_uri: string; qr_data_uri: string } | null
  >(null);
  const [codigo, setCodigo] = useState('');
  const [backupCodes, setBackupCodes] = useState<string[] | null>(null);
  const [senhaDes, setSenhaDes] = useState('');
  const [codigoDes, setCodigoDes] = useState('');
  const [msg, setMsg] = useState<{ tipo: 'ok' | 'erro'; texto: string } | null>(null);
  const [busy, setBusy] = useState(false);

  async function iniciarSetup() {
    setMsg(null);
    setBusy(true);
    try {
      setSetup(await api.authTwofaSetup());
    } catch (err) {
      setMsg({ tipo: 'erro', texto: err instanceof ApiError ? err.message : 'Falha no setup.' });
    } finally {
      setBusy(false);
    }
  }

  async function ativar(e: FormEvent) {
    e.preventDefault();
    setMsg(null);
    setBusy(true);
    try {
      const r = await api.authTwofaAtivar(codigo.trim());
      setBackupCodes(r.backup_codes);
      setSetup(null);
      setCodigo('');
      await refresh();
    } catch (err) {
      setMsg({ tipo: 'erro', texto: err instanceof ApiError ? err.message : 'Código inválido.' });
    } finally {
      setBusy(false);
    }
  }

  async function desativar(e: FormEvent) {
    e.preventDefault();
    setMsg(null);
    setBusy(true);
    try {
      const r = await api.authTwofaDesativar(senhaDes, codigoDes.trim());
      setMsg({ tipo: 'ok', texto: r.mensagem });
      setSenhaDes('');
      setCodigoDes('');
      await refresh();
    } catch (err) {
      setMsg({ tipo: 'erro', texto: err instanceof ApiError ? err.message : 'Não consegui desativar.' });
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="card p-6 mb-5">
      <h2 className="font-display font-semibold text-lg text-ink mb-1">
        Verificação em duas etapas (2FA)
      </h2>
      <p className="text-ink-mute text-sm mb-4">
        {ativo
          ? 'Ativa — o login pede um código do seu app autenticador.'
          : 'Protege o login com um código do app autenticador (Google Authenticator, Authy…).'}
      </p>

      {/* Backup codes recém-gerados (mostrados UMA vez) */}
      {backupCodes && (
        <div className="rounded-lg border border-amber-300 bg-amber-50 p-4 mb-4">
          <p className="text-sm font-medium text-amber-900 mb-2">
            Guarde estes códigos de backup agora — eles não aparecem de novo.
            Cada um serve uma única vez se você perder o app.
          </p>
          <div className="grid grid-cols-2 gap-1 font-mono text-sm text-amber-900">
            {backupCodes.map((c) => (
              <span key={c}>{c}</span>
            ))}
          </div>
          <button
            type="button"
            className="btn-ghost mt-3"
            onClick={() => setBackupCodes(null)}
          >
            Já guardei
          </button>
        </div>
      )}

      {msg && (
        <p
          className={`text-sm mb-3 ${msg.tipo === 'ok' ? 'text-success-ink' : 'text-red-600'}`}
          role="alert"
        >
          {msg.texto}
        </p>
      )}

      {/* ── Estado: ATIVO → permite desativar ──────────────────────── */}
      {ativo && !backupCodes && (
        <form onSubmit={desativar} className="flex flex-col gap-3">
          <p className="text-sm text-ink-mute">
            Para desativar, confirme sua senha e um código (TOTP ou backup).
          </p>
          <input
            type="password"
            className="input"
            placeholder="Senha atual"
            autoComplete="current-password"
            value={senhaDes}
            onChange={(e) => setSenhaDes(e.target.value)}
            required
          />
          <input
            type="text"
            inputMode="numeric"
            className="input tracking-widest"
            placeholder="Código (123456 ou backup)"
            value={codigoDes}
            onChange={(e) => setCodigoDes(e.target.value)}
            required
          />
          <button type="submit" className="btn-ghost self-start" disabled={busy}>
            {busy ? 'Desativando…' : 'Desativar 2FA'}
          </button>
        </form>
      )}

      {/* ── Estado: INATIVO, sem setup → botão pra começar ─────────── */}
      {!ativo && !setup && (
        <button type="button" className="btn-primary" onClick={() => void iniciarSetup()} disabled={busy}>
          {busy ? 'Gerando…' : 'Ativar 2FA'}
        </button>
      )}

      {/* ── Estado: INATIVO, com setup → QR + confirmar código ─────── */}
      {!ativo && setup && (
        <form onSubmit={ativar} className="flex flex-col gap-3">
          <p className="text-sm text-ink-mute">
            1. Escaneie o QR no seu app autenticador (ou use o código manual abaixo).
          </p>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={setup.qr_data_uri}
            alt="QR code do 2FA"
            width={180}
            height={180}
            className="rounded-lg border border-line self-start"
          />
          <p className="text-xs text-ink-mute">
            Código manual:{' '}
            <span className="font-mono text-ink break-all">{setup.secret}</span>
          </p>
          <label className="flex flex-col gap-1.5">
            <span className="text-xs font-medium text-ink-mute">
              2. Digite o código de 6 dígitos pra confirmar
            </span>
            <input
              type="text"
              inputMode="numeric"
              autoComplete="one-time-code"
              className="input tracking-widest"
              placeholder="123456"
              value={codigo}
              onChange={(e) => setCodigo(e.target.value)}
              required
            />
          </label>
          <div className="flex gap-2">
            <button type="submit" className="btn-primary" disabled={busy}>
              {busy ? 'Confirmando…' : 'Confirmar e ativar'}
            </button>
            <button type="button" className="btn-ghost" onClick={() => setSetup(null)}>
              Cancelar
            </button>
          </div>
        </form>
      )}
    </section>
  );
}

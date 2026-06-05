import { useState } from 'react';

import { StatCard } from './StatCard';
import {
  useOutreachEmails,
  useOutreachFollowups,
  useOutreachGerar,
  useOutreachSync,
} from '@/hooks/useOutreach';
import type { EmailItem, EmailStatus } from '@/lib/types';

export default function OutreachScreen() {
  const emails = useOutreachEmails(50);
  const sync = useOutreachSync();
  // Por segurança: a tela gera em lotes pequenos (5) por clique.
  const gerar = useOutreachGerar(5, 8);
  const followups = useOutreachFollowups(3);
  

  const [aviso, setAviso] = useState<string | null>(null);

  async function handleGerar() {
    setAviso(null);
    const r = await gerar.run();
    if (r) {
      setAviso(
        `Gerados ${r.gerados} rascunho(s), ${r.falhas} falha(s), ${r.pulados} pulado(s). ` +
          `Revise no webmail antes de enviar.`,
      );
      emails.refetch();
    }
  }

  async function handleFollowups() {
    setAviso(null);
    const r = await followups.run();
    if (r) {
      setAviso(
        `Gerados ${r.gerados} follow-up(s), ${r.falhas} falha(s). ` +
          `Revise no webmail antes de enviar.`,
      );
      emails.refetch();
    }
  }

  async function handleSync() {
    setAviso(null);
    const r = await sync.run();
    if (r) {
      setAviso(
        `${r.enviados_confirmados} envio(s) confirmado(s), ` +
          `${r.respostas_detectadas} resposta(s) detectada(s).`,
      );
      emails.refetch();
    }
  }

  const stats = computeStats(emails.items);
  const busy = gerar.loading || sync.loading || followups.loading;

  return (
    <div className="max-w-[1200px] mx-auto">
      <header className="mb-7">
        <div className="eyebrow mb-3">Agente 03 · Outreach por e-mail</div>
        <h1 className="font-display font-semibold text-[38px] leading-[1.05] tracking-tighter text-ink m-0 mb-2.5">
          Outreach
        </h1>
        <p className="text-[15px] text-ink-soft max-w-[60ch] leading-relaxed m-0">
          Gera rascunhos de e-mail pros contatos com a IA, deixa na sua caixa
          pra revisão, e acompanha quais foram enviados e respondidos.
        </p>
      </header>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-7">
        <StatCard label="Rascunhos" value={stats.rascunho} loading={emails.loading} />
        <StatCard label="Enviados" value={stats.enviado} loading={emails.loading} />
        <StatCard
          label="Respondidos"
          value={stats.respondido}
          trend={stats.taxaResposta}
          trendDirection="up"
          loading={emails.loading}
        />
        <StatCard label="Total" value={emails.total} loading={emails.loading} />
      </div>

      <section className="card p-6 mb-6">
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div className="max-w-[55ch]">
            <h3 className="font-display font-semibold text-sm tracking-tight text-ink mb-1">
              Ações
            </h3>
            <p className="text-xs text-ink-mute">
              "Gerar rascunhos" processa até 5 contatos pendentes por vez (cada
              um vira um rascunho na sua caixa). "Sincronizar" confere o que
              você enviou e detecta respostas.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              type="button"
              className="btn-ghost disabled:opacity-40 disabled:cursor-not-allowed"
              onClick={handleSync}
              disabled={busy}
            >
              {sync.loading ? 'Sincronizando…' : 'Sincronizar status'}
            </button>
            <button
              type="button"
              className="btn-ghost disabled:opacity-40 disabled:cursor-not-allowed"
              onClick={handleFollowups}
              disabled={busy}
            >
              {followups.loading ? 'Gerando follow-ups…' : 'Gerar follow-ups'}
            </button>
            <button
              type="button"
              className="btn-primary disabled:opacity-40 disabled:cursor-not-allowed"
              onClick={handleGerar}
              disabled={busy}
            >
              {gerar.loading ? 'Gerando… (pode demorar)' : 'Gerar rascunhos (até 5)'}
            </button>
          </div>
        </div>

        {aviso && (
          <div className="mt-4 text-[13px] text-ink-soft bg-bg-alt border border-line rounded p-3">
            {aviso}
          </div>
        )}
        {(gerar.error || sync.error || followups.error) && (
          <div className="mt-4 text-[13px] text-brand-ink bg-brand-soft/60 border border-brand/30 rounded p-3">
            {gerar.error?.message ?? sync.error?.message ?? followups.error?.message}
          </div>
        )}
      </section>

      <section className="mb-8">
        <h2 className="font-display font-semibold text-lg tracking-tight text-ink mb-4">
          E-mails
        </h2>
        <EmailList items={emails.items} loading={emails.loading} />
      </section>
    </div>
  );
}

function EmailList({
  items,
  loading,
}: {
  items: EmailItem[];
  loading: boolean;
}) {
  if (loading) {
    return (
      <div className="flex flex-col gap-2">
        {[0, 1, 2].map((i) => (
          <div key={i} className="card p-3.5 h-[60px] animate-pulse" />
        ))}
      </div>
    );
  }
  if (items.length === 0) {
    return (
      <div className="card p-8 text-center">
        <p className="text-sm text-ink-mute">
          Nenhum e-mail ainda. Clique em "Gerar rascunhos" pra começar.
        </p>
      </div>
    );
  }
  return (
    <div className="flex flex-col gap-2">
      {items.map((e) => (
        <div
          key={e.id}
          className="card p-3.5 px-[18px] grid grid-cols-[1fr_auto] gap-4 items-center"
        >
          <div className="flex flex-col gap-0.5 min-w-0">
            <span className="text-sm font-medium text-ink truncate">
              {e.assunto}
            </span>
            <span className="font-mono text-[11.5px] text-ink-mute truncate">
              {e.destinatario}
              {e.follow_up_num > 0 && ` · follow-up ${e.follow_up_num}`}
            </span>
          </div>
          <StatusBadge status={e.status} />
        </div>
      ))}
    </div>
  );
}

function StatusBadge({ status }: { status: EmailStatus }) {
  const mapa: Record<EmailStatus, { label: string; cls: string }> = {
    rascunho: { label: 'Rascunho', cls: 'bg-bg-alt text-ink-soft' },
    enviado: { label: 'Enviado', cls: 'bg-brand-soft text-brand-ink' },
    respondido: { label: 'Respondido', cls: 'bg-success-soft text-success-ink' },
    sem_resposta: { label: 'Sem resposta', cls: 'bg-bg-alt text-ink-mute' },
    erro: { label: 'Erro', cls: 'bg-brand-soft text-brand-ink' },
  };
  const { label, cls } = mapa[status] ?? mapa.rascunho;
  return (
    <span
      className={`font-mono text-[10px] uppercase tracking-[0.08em] px-2 py-1 rounded-sm whitespace-nowrap ${cls}`}
    >
      {label}
    </span>
  );
}

function computeStats(items: EmailItem[]) {
  const c = { rascunho: 0, enviado: 0, respondido: 0 };
  for (const e of items) {
    if (e.status === 'rascunho') c.rascunho++;
    else if (e.status === 'enviado') c.enviado++;
    else if (e.status === 'respondido') c.respondido++;
  }
  const base = c.enviado + c.respondido;
  const taxa = base > 0 ? `${Math.round((c.respondido / base) * 100)}% resposta` : '—';
  return { ...c, taxaResposta: taxa };
}
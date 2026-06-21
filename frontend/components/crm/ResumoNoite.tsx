import { useState } from 'react';

import { useFetch } from '@/hooks/useFetch';
import { api } from '@/lib/api';
import type { Briefing } from '@/lib/types';

/**
 * "Resumo da Noite" (MAS-4) — o coordenador em modo proativo. Mostra o que
 * precisa de você (vagas a triar, follow-ups, atividades) + 1 micro-ação.
 * Gera sob demanda; o cron manda a mesma coisa no Telegram às 18h.
 */
export function ResumoNoite() {
  const [versao, setVersao] = useState(0);
  const { data: b, loading } = useFetch<Briefing>(
    () => api.briefingGerar(),
    [versao],
  );

  return (
    <div className="card p-5 border-brand/30 bg-brand-soft/15">
      <div className="flex items-center justify-between gap-3 mb-3">
        <h2 className="font-display font-semibold text-[15px] tracking-tight text-ink m-0">
          🌙 Resumo da Noite
          <span className="text-[12px] text-ink-mute font-normal ml-2">
            (coordenador · MAS-4)
          </span>
        </h2>
        <button
          type="button"
          className="btn-ghost !px-3 !py-1 !text-[12px]"
          onClick={() => setVersao((v) => v + 1)}
          disabled={loading}
        >
          {loading ? 'Gerando…' : 'Atualizar'}
        </button>
      </div>

      {!b ? (
        <div className="animate-pulse h-20" />
      ) : (
        <div className="grid md:grid-cols-3 gap-3">
          <Bloco titulo="🎯 Vagas pra triar" total={b.vagas_triar.total} exemplos={b.vagas_triar.exemplos} />
          <Bloco titulo="📨 Follow-ups freela" total={b.freela_followups.total} exemplos={b.freela_followups.exemplos} />
          <div className="rounded-lg border border-line bg-surface p-3">
            <div className="text-[12px] text-ink-mute mb-1">📋 CRM</div>
            <div className="text-[13px] text-ink">
              {b.atividades_pendentes} pendente(s)
              <br />
              {b.atividades_atrasadas} atrasada(s)
            </div>
          </div>
        </div>
      )}

      {b?.micro_acao && (
        <div className="mt-3 text-[13px] text-ink">
          <span className="font-semibold">👉 Micro-ação: </span>
          {b.micro_acao}
        </div>
      )}
    </div>
  );
}

function Bloco({
  titulo,
  total,
  exemplos,
}: {
  titulo: string;
  total: number;
  exemplos: string[];
}) {
  return (
    <div className="rounded-lg border border-line bg-surface p-3">
      <div className="text-[12px] text-ink-mute mb-1">{titulo}</div>
      <div className="font-display font-semibold text-xl text-ink leading-none mb-1.5">
        {total}
      </div>
      <ul className="flex flex-col gap-0.5 m-0 p-0 list-none">
        {exemplos.slice(0, 3).map((e) => (
          <li key={e} className="text-[12px] text-ink-soft truncate">
            • {e}
          </li>
        ))}
      </ul>
    </div>
  );
}

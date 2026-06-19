import { useState } from 'react';

import { useFetch } from '@/hooks/useFetch';
import { api } from '@/lib/api';
import type { RecordTipo } from '@/lib/types';

function quando(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

// Pontinho: outcome pinta por sinal (+/-); senão por origem do evento.
function corPonto(ev: { tipo: string; origem: string; payload?: Record<string, unknown> | null }): string {
  if (ev.tipo === 'outcome') {
    const sinal = Number(ev.payload?.sinal ?? 0);
    if (sinal > 0) return 'bg-green-500';
    if (sinal < 0) return 'bg-red-500';
    return 'bg-ink-mute';
  }
  if (ev.origem === 'coordenador') return 'bg-brand';
  if (ev.origem === 'cron') return 'bg-purple-400';
  return 'bg-ink-mute';
}

// Resultados mais comuns por tipo de alvo (rótulo amigável → chave do backend).
const OUTCOMES: { chave: string; label: string }[] = [
  { chave: 'respondido', label: '✅ Respondeu' },
  { chave: 'reuniao', label: '📅 Reunião' },
  { chave: 'entrevista', label: '🎯 Entrevista' },
  { chave: 'fechou', label: '🤝 Fechou' },
  { chave: 'ganho', label: '🟢 Ganho' },
  { chave: 'sem_resposta', label: '🔇 Sem resposta' },
  { chave: 'recusado', label: '🔴 Recusado' },
  { chave: 'perdido', label: '⚪ Perdido' },
];

/**
 * Linha do tempo da memória compartilhada (MAS-1) de um alvo. Mostra o que os
 * agentes (e você) já fizeram com ele e deixa adicionar uma nota.
 */
export function Timeline({
  tipo,
  id,
}: {
  tipo: RecordTipo;
  id: string;
}) {
  const [versao, setVersao] = useState(0);
  const [nota, setNota] = useState('');
  const [salvando, setSalvando] = useState(false);
  const { data } = useFetch(
    () => api.memoriaTimeline(tipo, id),
    [tipo, id, versao],
  );
  const eventos = data?.eventos ?? [];

  async function adicionar() {
    const v = nota.trim();
    if (!v) return;
    setNota('');
    setSalvando(true);
    try {
      await api.memoriaCriarNota(tipo, id, v);
      setVersao((x) => x + 1);
    } finally {
      setSalvando(false);
    }
  }

  async function marcarResultado(resultado: string) {
    if (!resultado) return;
    setSalvando(true);
    try {
      await api.memoriaRegistrarOutcome(tipo, id, resultado);
      setVersao((x) => x + 1);
    } finally {
      setSalvando(false);
    }
  }

  return (
    <div>
      <h3 className="font-display font-semibold text-[13px] tracking-tight text-ink m-0 mb-2">
        Linha do tempo ({eventos.length})
      </h3>

      <div className="flex items-center gap-2 mb-3">
        <input
          className="input !py-1 !text-[12.5px]"
          placeholder="Adicionar uma nota…"
          value={nota}
          onChange={(e) => setNota(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') adicionar();
          }}
        />
        <button
          type="button"
          className="btn-ghost !px-3 !py-1 !text-[12px] disabled:opacity-40"
          onClick={adicionar}
          disabled={salvando || !nota.trim()}
        >
          Anotar
        </button>
        <select
          className="input !py-1 !text-[12px] max-w-[150px]"
          value=""
          disabled={salvando}
          onChange={(e) => marcarResultado(e.target.value)}
          title="Registrar resultado (alimenta o aprendizado)"
        >
          <option value="">Resultado…</option>
          {OUTCOMES.map((o) => (
            <option key={o.chave} value={o.chave}>
              {o.label}
            </option>
          ))}
        </select>
      </div>

      {eventos.length === 0 ? (
        <p className="text-[12.5px] text-ink-mute m-0">
          Nada registrado ainda. As ações dos agentes aparecem aqui.
        </p>
      ) : (
        <ul className="flex flex-col gap-2 m-0 p-0 list-none">
          {eventos.map((ev) => (
            <li key={ev.id} className="flex gap-2.5 text-[12.5px]">
              <span
                className={`mt-1.5 w-1.5 h-1.5 rounded-full shrink-0 ${corPonto(
                  ev,
                )}`}
              />
              <div className="min-w-0">
                <div className="text-ink">{ev.resumo ?? ev.tipo}</div>
                <div className="text-ink-mute text-[11px]">
                  {ev.agente} · {quando(ev.created_at)}
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

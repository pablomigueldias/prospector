import { useEffect, useState } from 'react';

import { useFetch } from '@/hooks/useFetch';
import { api } from '@/lib/api';
import { ApiError } from '@/lib/types';
import type { Job, JobRunResult } from '@/lib/types';

/**
 * S4 — Agendamentos na UI. Lista os jobs do scheduler, deixa ligar/desligar e
 * mudar a hora (gravado via /api/config, S3) e **rodar agora** (on-demand). As
 * mudanças de hora/liga-desliga só valem no próximo restart da API — o que a
 * tela avisa; o "Rodar agora" funciona na hora.
 */
export function AgendamentosScreen() {
  const { data, loading, error } = useFetch<Job[]>(
    () => api.getAgendamentos(),
    [],
  );
  const [jobs, setJobs] = useState<Job[]>([]);

  useEffect(() => {
    if (data) setJobs(data);
  }, [data]);

  return (
    <div className="flex flex-col gap-6 max-w-3xl">
      <header>
        <div className="eyebrow mb-2">Self-service</div>
        <h1 className="font-display font-semibold text-2xl tracking-tight text-ink m-0">
          Agendamentos
        </h1>
        <p className="text-[15px] text-ink-soft mt-1 mb-0 max-w-[60ch]">
          Controle os jobs automáticos — ligue/desligue, mude o horário e
          dispare na hora. Mudar horário ou ligar/desligar só vale após
          reiniciar a API; o &quot;Rodar agora&quot; funciona já.
        </p>
      </header>

      {loading && jobs.length === 0 ? (
        <div className="card p-6 animate-pulse h-32" />
      ) : error ? (
        <div className="card p-5 border-red-300">
          <p className="text-[14px] text-red-600 m-0">
            Não consegui carregar (
            {error.status === 403 ? 'sem permissão' : error.message}).
          </p>
        </div>
      ) : (
        jobs.map((job) => (
          <JobCard
            key={job.id}
            job={job}
            onPatch={(patch) =>
              setJobs((prev) =>
                prev.map((j) => (j.id === job.id ? { ...j, ...patch } : j)),
              )
            }
          />
        ))
      )}
    </div>
  );
}

function JobCard({
  job,
  onPatch,
}: {
  job: Job;
  onPatch: (patch: Partial<Job>) => void;
}) {
  const [rodando, setRodando] = useState(false);
  const [salvando, setSalvando] = useState(false);
  const [resultado, setResultado] = useState<JobRunResult | null>(null);
  const [msg, setMsg] = useState<{ tipo: 'ok' | 'erro'; texto: string } | null>(
    null,
  );

  async function salvarConfig(mudancas: Record<string, boolean | number>) {
    setSalvando(true);
    setMsg(null);
    try {
      await api.updateConfig(mudancas);
      setMsg({ tipo: 'ok', texto: 'Salvo — vale no próximo restart da API.' });
    } catch (e) {
      setMsg({
        tipo: 'erro',
        texto: e instanceof ApiError ? e.message : 'Falha ao salvar.',
      });
    } finally {
      setSalvando(false);
    }
  }

  function toggle() {
    const novo = !job.ligado;
    onPatch({ ligado: novo });
    void salvarConfig({ [job.enabled_key]: novo });
  }

  function mudarHora(hora: number) {
    if (Number.isNaN(hora) || hora < 0 || hora > 23) return;
    onPatch({ hora });
    void salvarConfig({ [job.hora_key]: hora });
  }

  async function rodarAgora() {
    setRodando(true);
    setMsg(null);
    setResultado(null);
    try {
      const r = await api.rodarJob(job.id);
      setResultado(r);
    } catch (e) {
      setMsg({
        tipo: 'erro',
        texto: e instanceof ApiError ? e.message : 'Falha ao rodar.',
      });
    } finally {
      setRodando(false);
    }
  }

  return (
    <section className="card p-5">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <h2 className="font-display font-semibold text-[15px] tracking-tight text-ink m-0">
              {job.nome}
            </h2>
            <span
              className={`text-[11px] font-mono uppercase tracking-wide ${
                job.ligado ? 'text-emerald-600' : 'text-ink-faint'
              }`}
            >
              {job.ligado ? 'ligado' : 'desligado'}
            </span>
          </div>
          <p className="text-[13px] text-ink-mute mt-1 mb-0">{job.descricao}</p>
        </div>
        <button
          type="button"
          role="switch"
          aria-checked={job.ligado}
          disabled={salvando}
          onClick={toggle}
          className={`relative inline-flex h-6 w-11 shrink-0 items-center rounded-full transition-colors ${
            job.ligado ? 'bg-brand' : 'bg-line'
          }`}
        >
          <span
            className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
              job.ligado ? 'translate-x-6' : 'translate-x-1'
            }`}
          />
        </button>
      </div>

      <div className="flex flex-wrap items-center gap-4 mt-4 pt-4 border-t border-line">
        <label className="flex items-center gap-2 text-[13px] text-ink-soft">
          Todo dia às
          <input
            type="number"
            min={0}
            max={23}
            value={job.hora}
            disabled={salvando}
            onChange={(e) => mudarHora(Number(e.target.value))}
            className="input !py-1.5 !px-2 text-[14px] w-16 text-right"
          />
          h
        </label>
        <button
          type="button"
          className="btn-ghost !py-1.5"
          disabled={rodando}
          onClick={() => void rodarAgora()}
        >
          {rodando ? 'Rodando…' : 'Rodar agora'}
        </button>
        {msg && (
          <span
            className={`text-[12px] ${
              msg.tipo === 'ok' ? 'text-emerald-600' : 'text-red-600'
            }`}
          >
            {msg.texto}
          </span>
        )}
      </div>

      {resultado && (
        <div className="mt-3 rounded-lg border border-line bg-bg-alt p-3">
          <div className="text-[12px] text-ink-mute mb-1">
            Rodou em{' '}
            {new Date(resultado.executado_em).toLocaleString('pt-BR')}
          </div>
          <pre className="text-[12px] text-ink-soft m-0 whitespace-pre-wrap break-words">
            {JSON.stringify(resultado.resultado, null, 2)}
          </pre>
        </div>
      )}
    </section>
  );
}

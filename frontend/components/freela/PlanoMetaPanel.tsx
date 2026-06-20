import { useEffect, useState } from 'react';

import { formatBRL } from '@/lib/format';
import { useFreelaActions } from '@/hooks/useFreela';
import { type FreelaPlanoMeta } from '@/lib/types';

// ── Plano da meta (motor: matemática reversa + rampa) ─────────────

const META_LIQ_KEY = 'freela_meta_liquida';
const HORAS_DIA_KEY = 'freela_horas_dia';
const DIAS_MES_KEY = 'freela_dias_mes';

const GARGALO_META: Record<string, { label: string; cls: string }> = {
  ticket: { label: '⬆ Gargalo: subir ticket', cls: 'bg-red-50 text-red-700 border-red-200' },
  conversao: { label: '🎯 Gargalo: conversão', cls: 'bg-amber-50 text-amber-800 border-amber-200' },
  volume: { label: '📨 Gargalo: volume de propostas', cls: 'bg-sky-50 text-sky-700 border-sky-200' },
  no_caminho: { label: '✅ No caminho', cls: 'bg-emerald-50 text-emerald-700 border-emerald-200' },
  sem_dados: { label: '🌱 Sem dados ainda', cls: 'bg-bg-alt text-ink-soft border-line' },
};

// Progresso do mês corrente vs ritmo necessário.
const STATUS_MES: Record<string, { label: string; barra: string; texto: string }> = {
  na_frente: { label: '🚀 Na frente', barra: 'bg-emerald-500', texto: 'text-emerald-700' },
  no_caminho: { label: '✅ No caminho', barra: 'bg-emerald-500', texto: 'text-emerald-700' },
  atras: { label: '⚠️ Atrás do ritmo', barra: 'bg-red-500', texto: 'text-red-700' },
  sem_dados: { label: '🌱 Sem fechadas no mês', barra: 'bg-line', texto: 'text-ink-soft' },
};

function numFromLS(key: string, def: number): number {
  if (typeof window === 'undefined') return def;
  const v = Number(localStorage.getItem(key));
  return Number.isFinite(v) && v > 0 ? v : def;
}

export function PlanoMetaPanel({ refreshKey }: { refreshKey: number }) {
  const { planoMeta } = useFreelaActions();
  const [metaLiq, setMetaLiq] = useState(10000);
  const [horasDia, setHorasDia] = useState(5);
  const [diasMes, setDiasMes] = useState(26);
  const [plano, setPlano] = useState<FreelaPlanoMeta | null>(null);

  // carrega inputs salvos (uma vez)
  useEffect(() => {
    setMetaLiq(numFromLS(META_LIQ_KEY, 10000));
    setHorasDia(numFromLS(HORAS_DIA_KEY, 5));
    setDiasMes(numFromLS(DIAS_MES_KEY, 26));
  }, []);

  // recalcula (com leve debounce) quando inputs ou métricas mudam
  useEffect(() => {
    if (!(metaLiq > 0 && horasDia > 0 && diasMes > 0)) return;
    const t = setTimeout(async () => {
      const r = await planoMeta({
        meta_liquida: metaLiq,
        horas_dia: horasDia,
        dias_mes: diasMes,
        pct_faturavel: 0.7,
      });
      if (r) setPlano(r);
    }, 350);
    return () => clearTimeout(t);
  }, [metaLiq, horasDia, diasMes, refreshKey, planoMeta]);

  function save(key: string, v: number, setter: (n: number) => void) {
    setter(v);
    if (typeof window !== 'undefined' && v > 0) localStorage.setItem(key, String(v));
  }

  const abaixoAlvo =
    plano?.valor_hora_real != null && plano.valor_hora_real < plano.valor_hora_alvo;
  const gargalo = plano ? GARGALO_META[plano.gargalo] : null;

  return (
    <div className="card p-5 mb-3">
      <div className="flex items-center justify-between flex-wrap gap-2 mb-3">
        <h3 className="font-display font-semibold text-base text-ink m-0">🎯 Plano da meta</h3>
        {plano && (
          <span
            className="text-[12px] font-medium px-2 py-0.5 rounded border bg-brand-soft text-brand-ink border-brand/20"
            title={plano.fase.foco}
          >
            {plano.fase.nome} · meta {formatBRL(plano.fase.meta_min)}
            {plano.fase.meta_max !== plano.fase.meta_min && `–${formatBRL(plano.fase.meta_max)}`}
          </span>
        )}
      </div>

      {/* inputs de capacidade */}
      <div className="flex flex-wrap gap-3 mb-3">
        <label className="text-[12px] text-ink-soft flex items-center gap-1">
          Meta líq/mês R$
          <input
            type="number"
            className="input py-1 w-28 text-[13px]"
            value={metaLiq || ''}
            onChange={(e) => save(META_LIQ_KEY, Number(e.target.value), setMetaLiq)}
          />
        </label>
        <label className="text-[12px] text-ink-soft flex items-center gap-1">
          Horas/dia
          <input
            type="number"
            className="input py-1 w-16 text-[13px]"
            value={horasDia || ''}
            onChange={(e) => save(HORAS_DIA_KEY, Number(e.target.value), setHorasDia)}
          />
        </label>
        <label className="text-[12px] text-ink-soft flex items-center gap-1">
          Dias/mês
          <input
            type="number"
            className="input py-1 w-16 text-[13px]"
            value={diasMes || ''}
            onChange={(e) => save(DIAS_MES_KEY, Number(e.target.value), setDiasMes)}
          />
        </label>
      </div>

      {plano?.progresso_mes && (() => {
        const pm = plano.progresso_mes;
        const st = STATUS_MES[pm.status] ?? STATUS_MES.sem_dados;
        const pctReal = Math.min(100, pm.pct_meta * 100);
        const pctRitmo = Math.min(100, (pm.meta_ate_hoje / plano.meta_liquida) * 100);
        return (
          <div className="rounded-lg border border-line bg-surface p-3 mb-3">
            <div className="flex items-center justify-between gap-2 mb-1.5">
              <span className="text-[12px] font-medium text-ink-soft">
                Progresso do mês (dia {pm.dia}/{pm.dias_no_mes})
              </span>
              <span className={`text-[12px] font-semibold ${st.texto}`}>{st.label}</span>
            </div>
            {/* barra: realizado preenchido + marcador do ritmo esperado até hoje */}
            <div className="relative h-2.5 rounded-full bg-bg-alt overflow-hidden">
              <div className={`h-full ${st.barra}`} style={{ width: `${pctReal}%` }} />
              <div
                className="absolute top-0 bottom-0 w-0.5 bg-ink/60"
                style={{ left: `${pctRitmo}%` }}
                title={`Ritmo esperado até hoje: ${formatBRL(pm.meta_ate_hoje)}`}
              />
            </div>
            <div className="flex items-center justify-between text-[11px] text-ink-faint mt-1">
              <span className="tabular-nums">
                {formatBRL(pm.realizado)} de {formatBRL(plano.meta_liquida)} ({Math.round(pctReal)}%)
              </span>
              <span className="tabular-nums">ritmo: {formatBRL(pm.meta_ate_hoje)}</span>
            </div>
            <p className="text-[12px] text-ink-soft m-0 mt-1.5">{pm.resumo}</p>
          </div>
        );
      })()}

      {plano && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-3">
            <div>
              <div className="text-[11px] uppercase tracking-wide text-ink-mute">Valor-hora alvo</div>
              <div className="font-display font-semibold text-lg text-ink mt-0.5">
                {formatBRL(plano.valor_hora_alvo)}/h
              </div>
              <div className="text-[11px] text-ink-faint">
                {plano.horas_faturaveis_mes}h faturáveis/mês
              </div>
            </div>
            <div>
              <div className="text-[11px] uppercase tracking-wide text-ink-mute">Valor-hora real</div>
              <div
                className={`font-display font-semibold text-lg mt-0.5 ${
                  abaixoAlvo ? 'text-red-600' : 'text-ink'
                }`}
              >
                {plano.valor_hora_real != null ? `${formatBRL(plano.valor_hora_real)}/h` : '—'}
              </div>
              <div className="text-[11px] text-ink-faint">
                {plano.projecao_liquida_mes != null
                  ? `≈ ${formatBRL(plano.projecao_liquida_mes)}/mês no ritmo`
                  : 'feche 1 projeto p/ calibrar'}
              </div>
            </div>
            <div>
              <div className="text-[11px] uppercase tracking-wide text-ink-mute">Projetos/mês</div>
              <div className="font-display font-semibold text-lg text-ink mt-0.5">
                {plano.projetos_necessarios_mes != null
                  ? Math.ceil(plano.projetos_necessarios_mes)
                  : '—'}
              </div>
              <div className="text-[11px] text-ink-faint">
                {plano.ticket_medio != null ? `ticket ${formatBRL(plano.ticket_medio)}` : 'sem ticket ainda'}
              </div>
            </div>
            <div>
              <div className="text-[11px] uppercase tracking-wide text-ink-mute">Propostas/semana</div>
              <div className="font-display font-semibold text-lg text-brand-ink mt-0.5">
                {plano.propostas_por_semana != null ? Math.ceil(plano.propostas_por_semana) : '—'}
              </div>
              <div className="text-[11px] text-ink-faint">ritmo p/ bater a meta</div>
            </div>
          </div>

          <div className="flex items-start gap-2 flex-wrap">
            {gargalo && (
              <span
                className={`text-[12px] font-medium px-2 py-0.5 rounded border shrink-0 ${gargalo.cls}`}
              >
                {gargalo.label}
              </span>
            )}
            <p className="text-[12px] text-ink-soft m-0 flex-1 min-w-[200px]">{plano.diagnostico}</p>
          </div>
        </>
      )}
    </div>
  );
}


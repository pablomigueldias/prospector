import { useEffect, useState } from 'react';

import { formatBRL } from '@/lib/format';
import { type FreelaMetricas } from '@/lib/types';

// ── Forecast de pipeline + meta mensal ────────────────────────────

const META_KEY = 'freela_meta_mensal';

export function MetaForecast({ m, loading }: { m: FreelaMetricas | null; loading: boolean }) {
  const [meta, setMeta] = useState<number>(0);

  useEffect(() => {
    const v = Number(localStorage.getItem(META_KEY) || '0');
    if (!Number.isNaN(v)) setMeta(v);
  }, []);

  function salvarMeta(v: number) {
    setMeta(v);
    localStorage.setItem(META_KEY, String(v || 0));
  }

  const fechado = m?.liquido_total_fechado ?? 0;
  const forecast = m?.forecast_liquido ?? 0;
  const projetado = fechado + forecast; // o que já entrou + o provável
  const pctFechado = meta > 0 ? Math.min(100, (fechado / meta) * 100) : 0;
  const pctProjetado = meta > 0 ? Math.min(100, (projetado / meta) * 100) : 0;
  const falta = Math.max(0, meta - projetado);

  return (
    <div className="card p-5 mb-3">
      <div className="grid md:grid-cols-[1fr_1fr_1.4fr] gap-5 items-center">
        <div>
          <div className="text-[11px] uppercase tracking-wide text-ink-mute">Pipeline em aberto</div>
          <div className="font-display font-semibold text-lg text-ink mt-0.5">
            {loading ? '…' : formatBRL(m?.pipeline_aberto_liquido ?? 0)}
          </div>
          <div className="text-[12px] text-ink-faint">{m?.em_aberto ?? 0} proposta(s) aguardando</div>
        </div>
        <div>
          <div className="text-[11px] uppercase tracking-wide text-ink-mute">Previsão (ponderada)</div>
          <div className="font-display font-semibold text-lg text-brand-ink mt-0.5">
            {loading ? '…' : formatBRL(forecast)}
          </div>
          <div className="text-[12px] text-ink-faint">
            pipeline × {Math.round((m?.taxa_fechamento ?? 0) * 100)}% de fechamento
          </div>
        </div>
        <div>
          <div className="flex items-center justify-between mb-1">
            <span className="text-[11px] uppercase tracking-wide text-ink-mute">Meta</span>
            <label className="text-[12px] text-ink-soft flex items-center gap-1">
              R$
              <input
                type="number"
                className="input py-1 w-28 text-[13px]"
                value={meta || ''}
                placeholder="0"
                onChange={(e) => salvarMeta(Number(e.target.value))}
              />
            </label>
          </div>
          {meta > 0 ? (
            <>
              <div className="h-2.5 rounded-full bg-bg-alt overflow-hidden relative">
                {/* projetado (mais claro) + fechado (forte) */}
                <div className="absolute inset-y-0 left-0 bg-brand/30" style={{ width: `${pctProjetado}%` }} />
                <div className="absolute inset-y-0 left-0 bg-brand" style={{ width: `${pctFechado}%` }} />
              </div>
              <div className="text-[12px] text-ink-soft mt-1">
                {falta > 0 ? (
                  <>Faltam <strong>{formatBRL(falta)}</strong> (fechado + previsto = {formatBRL(projetado)}).</>
                ) : (
                  <>🎉 Meta coberta pelo fechado + previsto ({formatBRL(projetado)}).</>
                )}
              </div>
            </>
          ) : (
            <div className="text-[12px] text-ink-faint">Defina uma meta pra ver quanto falta.</div>
          )}
        </div>
      </div>

      {(m?.tempo_medio_resposta_horas != null || m?.valor_hora_real != null) && (
        <div className="mt-3 pt-3 border-t border-line flex flex-wrap gap-x-6 gap-y-1 text-[12px] text-ink-soft">
          {m?.tempo_medio_resposta_horas != null && (
            <span>⏱ Resposta média do cliente: <strong>{m.tempo_medio_resposta_horas}h</strong></span>
          )}
          {m?.valor_hora_real != null && (
            <span>💵 Seu valor-hora real (fechadas): <strong>{formatBRL(m.valor_hora_real)}/h</strong></span>
          )}
        </div>
      )}
    </div>
  );
}


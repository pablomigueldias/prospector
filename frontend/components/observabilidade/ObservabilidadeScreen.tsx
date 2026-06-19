import { useState } from 'react';
import {
  Bar,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import { useFetch } from '@/hooks/useFetch';
import { api } from '@/lib/api';
import type { ObsResumo } from '@/lib/types';

// Cores do design system (oklch) — mesmo padrão do RelatorioSection.
const COR_CUSTO = 'oklch(0.68 0.19 38)'; // brand
const COR_CHAMADAS = 'oklch(0.16 0.015 50)'; // ink
const COR_GRID = 'oklch(0.9 0.008 60)'; // line
const COR_EIXO = 'oklch(0.5 0.012 50)'; // ink-mute

const usd = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  maximumFractionDigits: 4,
});
const num = new Intl.NumberFormat('pt-BR');

const PERIODOS = [7, 30, 90];

/**
 * S2 — Observabilidade & Custos de IA. Custo/tokens por agente e por dia,
 * latência, taxa de erro e últimas chamadas, sobre a tabela `ai_calls`.
 */
export function ObservabilidadeScreen() {
  const [dias, setDias] = useState(30);
  const { data, loading, error } = useFetch<ObsResumo>(
    () => api.getObservabilidade(dias),
    [dias],
  );

  return (
    <div className="flex flex-col gap-6">
      <header className="flex items-end justify-between gap-4 flex-wrap">
        <div>
          <div className="eyebrow mb-2">Plataforma</div>
          <h1 className="font-display font-semibold text-2xl tracking-tight text-ink m-0">
            Observabilidade de IA
          </h1>
          <p className="text-[15px] text-ink-soft mt-1 mb-0 max-w-[60ch]">
            Quanto seu sistema gastou de IA, onde, e o que falhou.
          </p>
        </div>
        <div className="flex gap-1">
          {PERIODOS.map((p) => (
            <button
              key={p}
              type="button"
              onClick={() => setDias(p)}
              className={`px-3 py-1.5 rounded-pill text-[13px] font-medium transition-colors ${
                dias === p
                  ? 'bg-ink text-white'
                  : 'border border-line text-ink-soft hover:border-ink-mute'
              }`}
            >
              {p}d
            </button>
          ))}
        </div>
      </header>

      {loading && !data ? (
        <div className="card p-6 animate-pulse h-40" />
      ) : error ? (
        <div className="card p-5 border-red-300">
          <p className="text-[14px] text-red-600 m-0">
            Não consegui carregar (
            {error.status === 403 ? 'sem permissão' : error.message}).
          </p>
        </div>
      ) : data ? (
        <>
          {/* KPIs */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            <Kpi titulo="Custo" valor={usd.format(data.totais.custo_usd)} />
            <Kpi titulo="Chamadas" valor={num.format(data.totais.chamadas)} />
            <Kpi titulo="Tokens" valor={num.format(data.totais.tokens)} />
            <Kpi
              titulo="Taxa de erro"
              valor={`${(data.totais.taxa_erro * 100).toFixed(1)}%`}
              alerta={data.totais.taxa_erro > 0.1}
            />
            <Kpi
              titulo="Latência média"
              valor={
                data.totais.latencia_media_ms != null
                  ? `${num.format(data.totais.latencia_media_ms)} ms`
                  : '—'
              }
            />
          </div>

          {/* Série diária */}
          <section className="card p-5">
            <h2 className="font-display font-semibold text-[15px] tracking-tight text-ink mt-0 mb-4">
              Custo e chamadas por dia
            </h2>
            {data.por_dia.length === 0 ? (
              <p className="text-[13px] text-ink-mute m-0">
                Sem chamadas no período.
              </p>
            ) : (
              <div style={{ width: '100%', height: 280 }}>
                <ResponsiveContainer>
                  <ComposedChart
                    data={data.por_dia}
                    margin={{ top: 8, right: 8, bottom: 0, left: 8 }}
                  >
                    <CartesianGrid
                      vertical={false}
                      stroke={COR_GRID}
                      strokeDasharray="3 3"
                    />
                    <XAxis
                      dataKey="dia"
                      tick={{ fontSize: 11, fill: COR_EIXO }}
                      tickLine={false}
                      axisLine={{ stroke: COR_GRID }}
                      tickFormatter={(v) => String(v).slice(5)}
                    />
                    <YAxis
                      yAxisId="custo"
                      width={64}
                      tick={{ fontSize: 11, fill: COR_EIXO }}
                      tickLine={false}
                      axisLine={false}
                      tickFormatter={(v) => usd.format(Number(v))}
                    />
                    <YAxis
                      yAxisId="chamadas"
                      orientation="right"
                      width={36}
                      tick={{ fontSize: 11, fill: COR_EIXO }}
                      tickLine={false}
                      axisLine={false}
                    />
                    <Tooltip
                      cursor={{ fill: COR_GRID, opacity: 0.3 }}
                      formatter={(value, name) =>
                        name === 'Custo'
                          ? usd.format(Number(value))
                          : num.format(Number(value))
                      }
                    />
                    <Legend
                      iconType="circle"
                      wrapperStyle={{ fontSize: 12, paddingTop: 8 }}
                    />
                    <Bar
                      yAxisId="custo"
                      dataKey="custo_usd"
                      name="Custo"
                      fill={COR_CUSTO}
                      radius={[4, 4, 0, 0]}
                      maxBarSize={34}
                    />
                    <Line
                      yAxisId="chamadas"
                      type="monotone"
                      dataKey="chamadas"
                      name="Chamadas"
                      stroke={COR_CHAMADAS}
                      strokeWidth={2}
                      dot={{ r: 3, fill: COR_CHAMADAS }}
                      activeDot={{ r: 5 }}
                    />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
            )}
          </section>

          {/* Por agente */}
          <section className="card p-5">
            <h2 className="font-display font-semibold text-[15px] tracking-tight text-ink mt-0 mb-3">
              Por agente
            </h2>
            <div className="overflow-x-auto">
              <table className="w-full text-[13px]">
                <thead>
                  <tr className="text-ink-mute text-left border-b border-line">
                    <th className="font-medium py-2 pr-3">Agente</th>
                    <th className="font-medium py-2 px-3 text-right">Chamadas</th>
                    <th className="font-medium py-2 px-3 text-right">Tokens</th>
                    <th className="font-medium py-2 px-3 text-right">Custo</th>
                    <th className="font-medium py-2 px-3 text-right">Erro</th>
                    <th className="font-medium py-2 pl-3 text-right">Latência</th>
                  </tr>
                </thead>
                <tbody>
                  {data.por_agente.map((a) => (
                    <tr key={a.agente} className="border-b border-line/60">
                      <td className="py-2 pr-3 text-ink font-medium">{a.agente}</td>
                      <td className="py-2 px-3 text-right text-ink-soft">
                        {num.format(a.chamadas)}
                      </td>
                      <td className="py-2 px-3 text-right text-ink-soft">
                        {num.format(a.tokens)}
                      </td>
                      <td className="py-2 px-3 text-right text-ink">
                        {usd.format(a.custo_usd)}
                      </td>
                      <td
                        className={`py-2 px-3 text-right ${
                          a.taxa_erro > 0.1 ? 'text-red-600' : 'text-ink-soft'
                        }`}
                      >
                        {(a.taxa_erro * 100).toFixed(0)}%
                      </td>
                      <td className="py-2 pl-3 text-right text-ink-soft">
                        {a.latencia_media_ms != null
                          ? `${num.format(a.latencia_media_ms)} ms`
                          : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          {/* Últimas chamadas */}
          <section className="card p-5">
            <h2 className="font-display font-semibold text-[15px] tracking-tight text-ink mt-0 mb-3">
              Últimas chamadas
            </h2>
            <div className="flex flex-col divide-y divide-line/60">
              {data.ultimas.map((c, i) => (
                <div
                  key={`${c.created_at}-${i}`}
                  className="flex items-center justify-between gap-3 py-2 text-[13px]"
                >
                  <div className="min-w-0 flex items-center gap-2">
                    <span
                      className={`inline-block w-1.5 h-1.5 rounded-full shrink-0 ${
                        c.sucesso ? 'bg-emerald-500' : 'bg-red-500'
                      }`}
                      title={c.sucesso ? 'sucesso' : c.error_message || 'falha'}
                    />
                    <span className="text-ink font-medium">{c.agente}</span>
                    {c.operacao && (
                      <span className="text-ink-mute truncate">· {c.operacao}</span>
                    )}
                    <span className="text-ink-faint text-[11px] font-mono">
                      {c.provider}/{c.modelo}
                    </span>
                  </div>
                  <div className="flex items-center gap-4 shrink-0 text-ink-soft">
                    <span>{c.tokens_total != null ? num.format(c.tokens_total) : '—'} tok</span>
                    <span className="text-ink">{usd.format(c.custo_usd)}</span>
                    <span className="text-ink-faint">
                      {c.latencia_ms != null ? `${num.format(c.latencia_ms)}ms` : '—'}
                    </span>
                  </div>
                </div>
              ))}
              {data.ultimas.length === 0 && (
                <p className="text-[13px] text-ink-mute m-0 py-2">
                  Nenhuma chamada registrada.
                </p>
              )}
            </div>
          </section>
        </>
      ) : null}
    </div>
  );
}

function Kpi({
  titulo,
  valor,
  alerta,
}: {
  titulo: string;
  valor: string;
  alerta?: boolean;
}) {
  return (
    <div className="card p-4">
      <div className="text-[12px] text-ink-mute mb-1">{titulo}</div>
      <div
        className={`font-display font-semibold text-xl leading-none ${
          alerta ? 'text-red-600' : 'text-ink'
        }`}
      >
        {valor}
      </div>
    </div>
  );
}

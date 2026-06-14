import { useMemo, useState } from 'react';
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
  type TooltipProps,
} from 'recharts';

import { CategoriaDonut } from '@/components/CategoriaDonut';
import { useCategorias, useContas, useRelatorio } from '@/hooks/useFinancas';
import { achatarCategorias } from '@/lib/categorias';
import { formatBRL, formatMesAno } from '@/lib/format';
import type { RelatorioMesItem } from '@/lib/types';

interface Props {
  /** Mês âncora (o selecionado no topo do dashboard). A série termina nele. */
  ano: number;
  mes: number;
}

// Cores do design system (oklch) reaproveitadas no gráfico.
const COR_RECEITA = 'oklch(0.55 0.12 145)'; // success
const COR_DESPESA = 'oklch(0.68 0.19 38)'; // brand
const COR_SALDO = 'oklch(0.16 0.015 50)'; // ink
const COR_GRID = 'oklch(0.9 0.008 60)'; // line
const COR_EIXO = 'oklch(0.5 0.012 50)'; // ink-mute

const brlCompacto = new Intl.NumberFormat('pt-BR', {
  notation: 'compact',
  style: 'currency',
  currency: 'BRL',
  maximumFractionDigits: 1,
});

/** Monta o CSV (pt-BR: separador ';' e decimal com vírgula) e dispara o
 *  download no navegador, sem dependência externa. */
function baixarCsv(meses: RelatorioMesItem[]) {
  const br = (v: string) => String(v).replace('.', ',');
  const linhas = [
    ['Mês', 'Receitas', 'Despesas', 'Saldo'],
    ...meses.map((m) => [
      formatMesAno(m.ano, m.mes),
      br(m.total_receitas),
      br(m.total_despesas),
      br(m.saldo),
    ]),
  ];
  const csv = linhas.map((l) => l.join(';')).join('\n');
  const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `relatorio-financas-${meses[0]?.ano ?? ''}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

const PERIODOS = [3, 6, 12] as const;

export function RelatorioSection({ ano, mes }: Props) {
  const [meses, setMeses] = useState<number>(6);
  const [contaId, setContaId] = useState('');
  const [categoriaId, setCategoriaId] = useState('');
  const { relatorio, loading } = useRelatorio(ano, mes, meses, {
    contaId: contaId || undefined,
    categoriaId: categoriaId || undefined,
  });

  const { contas } = useContas(true);
  const { arvore } = useCategorias();
  const categoriasPlanas = useMemo(() => achatarCategorias(arvore), [arvore]);
  const recortado = !!contaId || !!categoriaId;

  const dados = useMemo(
    () =>
      (relatorio?.meses ?? []).map((m) => ({
        rotulo: formatMesAno(m.ano, m.mes),
        receitas: Number(m.total_receitas),
        despesas: Number(m.total_despesas),
        saldo: Number(m.saldo),
      })),
    [relatorio],
  );

  const temDados = dados.some((d) => d.receitas > 0 || d.despesas > 0);

  // Insight: despesa do último mês vs. média do período.
  const insight = useMemo(() => {
    if (!relatorio || dados.length < 2) return null;
    const ultimo = dados[dados.length - 1];
    const media = Number(relatorio.media_despesas);
    if (media <= 0) return null;
    const diffPct = ((ultimo.despesas - media) / media) * 100;
    return {
      rotulo: ultimo.rotulo,
      despesa: ultimo.despesas,
      diffPct,
      acima: diffPct > 0,
    };
  }, [relatorio, dados]);

  return (
    <section id="sec-relatorio" className="scroll-mt-16 mb-8">
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <h2 className="font-display font-semibold text-lg tracking-tight text-ink m-0">
          Relatório
        </h2>
        <div className="flex items-center gap-2">
          {/* Período */}
          <div className="inline-flex rounded-pill border border-line overflow-hidden">
            {PERIODOS.map((p) => (
              <button
                key={p}
                type="button"
                onClick={() => setMeses(p)}
                className={`px-3 py-1 text-[12.5px] transition-colors ${
                  meses === p
                    ? 'bg-brand text-white'
                    : 'text-ink-soft hover:bg-line-soft'
                }`}
              >
                {p}m
              </button>
            ))}
          </div>
          {/* Recorte por conta / categoria */}
          <select
            className="input w-auto py-1 text-[12.5px]"
            value={contaId}
            onChange={(e) => setContaId(e.target.value)}
            title="Recortar o relatório por conta"
          >
            <option value="">Conta: todas</option>
            {contas.map((c) => (
              <option key={c.id} value={c.id}>
                {c.nome}
              </option>
            ))}
          </select>
          <select
            className="input w-auto py-1 text-[12.5px]"
            value={categoriaId}
            onChange={(e) => setCategoriaId(e.target.value)}
            title="Recortar o relatório por categoria"
          >
            <option value="">Categoria: todas</option>
            {categoriasPlanas.map((c) => (
              <option key={c.id} value={c.id}>
                {`${'  '.repeat(c.depth)}${c.nome}`}
              </option>
            ))}
          </select>
          {recortado && (
            <button
              type="button"
              onClick={() => {
                setContaId('');
                setCategoriaId('');
              }}
              className="text-[12.5px] text-ink-mute hover:text-ink px-1"
            >
              limpar
            </button>
          )}
          <button
            type="button"
            onClick={() => relatorio && baixarCsv(relatorio.meses)}
            disabled={!relatorio || !temDados}
            className="btn-ghost px-3 py-1 text-[12.5px] disabled:opacity-40"
            title="Exportar a série em CSV"
          >
            Exportar CSV
          </button>
        </div>
      </div>

      {loading ? (
        <div className="card p-6 h-[320px] animate-pulse" />
      ) : !temDados ? (
        <div className="card p-6 text-center text-ink-soft text-sm">
          Sem lançamentos nos últimos {meses} meses
          {recortado ? ' com esse recorte' : ''}.
        </div>
      ) : (
        <>
          {/* Totais do período */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
            <MiniStat label="Receitas" value={formatBRL(relatorio!.total_receitas)} />
            <MiniStat label="Despesas" value={formatBRL(relatorio!.total_despesas)} />
            <MiniStat
              label="Saldo do período"
              value={formatBRL(relatorio!.saldo)}
              positivo={Number(relatorio!.saldo) >= 0}
            />
            <MiniStat
              label="Despesa média/mês"
              value={formatBRL(relatorio!.media_despesas)}
            />
          </div>

          {/* Insight: último mês vs. média */}
          {insight && (
            <div className="flex items-center gap-2 text-[13px] text-ink-soft mb-4">
              <span
                className={`inline-flex items-center justify-center w-5 h-5 rounded-full text-[11px] shrink-0 ${
                  insight.acima
                    ? 'bg-red-50 text-red-600'
                    : 'bg-success-soft text-success-ink'
                }`}
                aria-hidden
              >
                {insight.acima ? '↑' : '↓'}
              </span>
              <span>
                <strong className="text-ink">{insight.rotulo}</strong> fechou em{' '}
                {formatBRL(insight.despesa)} de despesa —{' '}
                <strong
                  className={insight.acima ? 'text-red-600' : 'text-success-ink'}
                >
                  {Math.abs(insight.diffPct).toFixed(0)}%{' '}
                  {insight.acima ? 'acima' : 'abaixo'}
                </strong>{' '}
                da média do período.
              </span>
            </div>
          )}

          {/* Gráfico: receitas x despesas (barras) + saldo (linha) */}
          <div className="card p-5 mb-4">
            <div style={{ width: '100%', height: 300 }}>
              <ResponsiveContainer>
                <ComposedChart
                  data={dados}
                  margin={{ top: 8, right: 8, bottom: 0, left: 8 }}
                  barGap={4}
                  barCategoryGap="22%"
                >
                  <CartesianGrid
                    vertical={false}
                    stroke={COR_GRID}
                    strokeDasharray="3 3"
                  />
                  <XAxis
                    dataKey="rotulo"
                    tick={{ fontSize: 11, fill: COR_EIXO }}
                    tickLine={false}
                    axisLine={{ stroke: COR_GRID }}
                  />
                  <YAxis
                    width={64}
                    tick={{ fontSize: 11, fill: COR_EIXO }}
                    tickLine={false}
                    axisLine={false}
                    tickFormatter={(v) => brlCompacto.format(Number(v))}
                  />
                  <Tooltip content={<TooltipBox />} cursor={{ fill: COR_GRID, opacity: 0.3 }} />
                  <Legend
                    iconType="circle"
                    wrapperStyle={{ fontSize: 12, paddingTop: 8 }}
                  />
                  <Bar
                    dataKey="receitas"
                    name="Receitas"
                    fill={COR_RECEITA}
                    radius={[4, 4, 0, 0]}
                    maxBarSize={34}
                  />
                  <Bar
                    dataKey="despesas"
                    name="Despesas"
                    fill={COR_DESPESA}
                    radius={[4, 4, 0, 0]}
                    maxBarSize={34}
                  />
                  <Line
                    type="monotone"
                    dataKey="saldo"
                    name="Saldo"
                    stroke={COR_SALDO}
                    strokeWidth={2}
                    dot={{ r: 3, fill: COR_SALDO }}
                    activeDot={{ r: 5 }}
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Top categorias do período */}
          <h3 className="font-display font-semibold text-sm tracking-tight text-ink-soft m-0 mb-2">
            Top categorias no período
          </h3>
          <CategoriaDonut items={relatorio!.por_categoria} />
        </>
      )}
    </section>
  );
}

function TooltipBox({ active, payload, label }: TooltipProps<number, string>) {
  if (!active || !payload?.length) return null;
  return (
    <div className="card px-3 py-2 shadow-brand-sm text-xs min-w-[150px]">
      <div className="font-medium text-ink mb-1.5">{label}</div>
      <ul className="m-0 p-0 list-none flex flex-col gap-1">
        {payload.map((p) => (
          <li key={p.dataKey} className="flex items-center gap-2">
            <span
              className="w-2 h-2 rounded-full shrink-0"
              style={{ background: p.color }}
            />
            <span className="text-ink-soft">{p.name}</span>
            <span className="ml-auto tabular-nums text-ink">
              {formatBRL(p.value ?? 0)}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function MiniStat({
  label,
  value,
  positivo,
}: {
  label: string;
  value: string;
  positivo?: boolean;
}) {
  return (
    <div className="card p-3">
      <div className="text-[11px] uppercase tracking-wide text-ink-mute mb-1">
        {label}
      </div>
      <div
        className={`font-display font-semibold tracking-tight text-base ${
          positivo === undefined
            ? 'text-ink'
            : positivo
              ? 'text-success-ink'
              : 'text-red-600'
        }`}
      >
        {value}
      </div>
    </div>
  );
}

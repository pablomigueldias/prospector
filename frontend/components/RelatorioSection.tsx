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
import type { RelatorioMesItem, RelatorioResponse } from '@/lib/types';

interface Props {
  /** Mês âncora (o selecionado no topo do dashboard). A série termina nele. */
  ano: number;
  mes: number;
  /** Clique num mês do gráfico → abre a lista de transações daquele mês. */
  onVerMes?: (ano: number, mes: number) => void;
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

/** Imprime só a seção Relatório (vira PDF pelo "Salvar como PDF" do navegador).
 *  Marca o body, dispara a impressão e limpa a marca quando o diálogo fecha. */
function exportarPdf() {
  const limpar = () => {
    document.body.classList.remove('print-relatorio');
    window.removeEventListener('afterprint', limpar);
  };
  window.addEventListener('afterprint', limpar);
  document.body.classList.add('print-relatorio');
  window.print();
}

export function RelatorioSection({ ano, mes, onVerMes }: Props) {
  const [meses, setMeses] = useState<number>(6);
  const [contaId, setContaId] = useState('');
  const [categoriaId, setCategoriaId] = useState('');
  const [comparar, setComparar] = useState(false);
  const filtro = { contaId: contaId || undefined, categoriaId: categoriaId || undefined };
  const { relatorio, loading } = useRelatorio(ano, mes, meses, filtro);
  // Período anterior: mesma janela um ano antes (ex.: jun/26 vs jun/25).
  const { relatorio: relAnterior } = useRelatorio(ano - 1, mes, meses, filtro, comparar);

  const { contas } = useContas(true);
  const { arvore } = useCategorias();
  const categoriasPlanas = useMemo(() => achatarCategorias(arvore), [arvore]);
  const recortado = !!contaId || !!categoriaId;

  const dados = useMemo(
    () =>
      (relatorio?.meses ?? []).map((m) => ({
        ano: m.ano,
        mes: m.mes,
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
            onClick={() => setComparar((v) => !v)}
            className={`px-3 py-1 text-[12.5px] rounded-pill border transition-colors ${
              comparar
                ? 'bg-brand text-white border-brand'
                : 'border-line text-ink-soft hover:bg-line-soft'
            }`}
            title={`Comparar com o mesmo período de ${ano - 1}`}
          >
            vs {ano - 1}
          </button>
          <button
            type="button"
            onClick={() => relatorio && baixarCsv(relatorio.meses)}
            disabled={!relatorio || !temDados}
            className="btn-ghost px-3 py-1 text-[12.5px] disabled:opacity-40"
            title="Exportar a série em CSV"
          >
            Exportar CSV
          </button>
          <button
            type="button"
            onClick={exportarPdf}
            disabled={!relatorio || !temDados}
            className="btn-ghost px-3 py-1 text-[12.5px] disabled:opacity-40"
            title="Imprimir / salvar como PDF"
          >
            Exportar PDF
          </button>
        </div>
      </div>

      {/* Cabeçalho só na impressão (dá contexto ao PDF) */}
      <div className="hidden print:block mb-4">
        <div className="font-display font-semibold text-lg text-ink">
          Relatório de finanças — {formatMesAno(ano, mes)} · últimos {meses} meses
        </div>
        {recortado && (
          <div className="text-sm text-ink-soft mt-0.5">
            Recorte:{' '}
            {[
              contaId && contas.find((c) => c.id === contaId)?.nome,
              categoriaId &&
                categoriasPlanas.find((c) => c.id === categoriaId)?.nome,
            ]
              .filter(Boolean)
              .join(' · ')}
          </div>
        )}
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
            {onVerMes && (
              <p className="text-[11.5px] text-ink-mute m-0 mb-2 print:hidden">
                Dica: clique num mês pra ver os lançamentos dele.
              </p>
            )}
            <div style={{ width: '100%', height: 300 }}>
              <ResponsiveContainer>
                <ComposedChart
                  data={dados}
                  margin={{ top: 8, right: 8, bottom: 0, left: 8 }}
                  barGap={4}
                  barCategoryGap="22%"
                  onClick={(state) => {
                    if (!onVerMes) return;
                    const ponto = (
                      state as { activePayload?: { payload?: { ano: number; mes: number } }[] }
                    )?.activePayload?.[0]?.payload;
                    if (ponto) onVerMes(ponto.ano, ponto.mes);
                  }}
                  className={onVerMes ? 'cursor-pointer' : undefined}
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

          {/* Comparativo com o mesmo período do ano anterior */}
          {comparar && (
            <ComparativoBlock
              atual={relatorio!}
              anterior={relAnterior}
              meses={meses}
              anoAtual={ano}
            />
          )}

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

function ComparativoBlock({
  atual,
  anterior,
  meses,
  anoAtual,
}: {
  atual: RelatorioResponse;
  anterior: RelatorioResponse | null;
  meses: number;
  anoAtual: number;
}) {
  if (!anterior) {
    return (
      <div className="card p-5 mb-4 h-[120px] animate-pulse" />
    );
  }
  const linhas: { rotulo: string; a: number; b: number; despesa?: boolean }[] = [
    { rotulo: 'Receitas', a: Number(atual.total_receitas), b: Number(anterior.total_receitas) },
    { rotulo: 'Despesas', a: Number(atual.total_despesas), b: Number(anterior.total_despesas), despesa: true },
    { rotulo: 'Saldo', a: Number(atual.saldo), b: Number(anterior.saldo) },
    { rotulo: 'Despesa média/mês', a: Number(atual.media_despesas), b: Number(anterior.media_despesas), despesa: true },
  ];
  return (
    <div className="card p-5 mb-4">
      <div className="flex items-baseline justify-between mb-3">
        <h3 className="font-display font-semibold text-sm tracking-tight text-ink m-0">
          Comparativo
        </h3>
        <span className="text-[11.5px] text-ink-mute">
          últimos {meses}m · {anoAtual} vs {anoAtual - 1}
        </span>
      </div>
      <table className="w-full text-sm border-collapse">
        <thead>
          <tr className="text-[11px] uppercase tracking-wide text-ink-mute">
            <th className="text-left font-medium pb-2"> </th>
            <th className="text-right font-medium pb-2">{anoAtual}</th>
            <th className="text-right font-medium pb-2">{anoAtual - 1}</th>
            <th className="text-right font-medium pb-2">variação</th>
          </tr>
        </thead>
        <tbody>
          {linhas.map((l) => {
            const diff = l.a - l.b;
            const pct = l.b !== 0 ? (diff / Math.abs(l.b)) * 100 : null;
            const subiu = diff > 0;
            // Pra despesa, subir é ruim (vermelho); pra receita/saldo, subir é bom.
            const ruim = l.despesa ? subiu : !subiu && diff !== 0;
            const cor =
              diff === 0
                ? 'text-ink-mute'
                : ruim
                  ? 'text-red-600'
                  : 'text-success-ink';
            return (
              <tr key={l.rotulo} className="border-t border-line-soft">
                <td className="py-2 text-ink-soft">{l.rotulo}</td>
                <td className="py-2 text-right tabular-nums text-ink">
                  {formatBRL(l.a)}
                </td>
                <td className="py-2 text-right tabular-nums text-ink-mute">
                  {formatBRL(l.b)}
                </td>
                <td className={`py-2 text-right tabular-nums ${cor}`}>
                  {diff === 0
                    ? '—'
                    : `${subiu ? '↑' : '↓'} ${pct != null ? `${Math.abs(pct).toFixed(0)}%` : formatBRL(Math.abs(diff))}`}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
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

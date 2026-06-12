import { useMemo, useState } from 'react';

import { CategoriaDonut } from '@/components/CategoriaDonut';
import { useRelatorio } from '@/hooks/useFinancas';
import { formatBRL, formatMesAno } from '@/lib/format';
import type { RelatorioMesItem } from '@/lib/types';

interface Props {
  /** Mês âncora (o selecionado no topo do dashboard). A série termina nele. */
  ano: number;
  mes: number;
}

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
  const { relatorio, loading } = useRelatorio(ano, mes, meses);

  // Escala das barras: maior valor (receita ou despesa) de qualquer mês.
  const maxValor = useMemo(() => {
    const todos = (relatorio?.meses ?? []).flatMap((m) => [
      Number(m.total_receitas),
      Number(m.total_despesas),
    ]);
    return Math.max(1, ...todos);
  }, [relatorio]);

  const temDados = (relatorio?.meses ?? []).some(
    (m) => Number(m.total_receitas) > 0 || Number(m.total_despesas) > 0,
  );

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
        <div className="card p-6 h-[260px] animate-pulse" />
      ) : !temDados ? (
        <div className="card p-6 text-center text-ink-soft text-sm">
          Sem lançamentos nos últimos {meses} meses.
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

          {/* Gráfico de barras: receitas x despesas por mês */}
          <div className="card p-5 mb-4">
            <div className="flex items-end gap-3 sm:gap-5 h-44">
              {relatorio!.meses.map((m) => {
                const rec = Number(m.total_receitas);
                const desp = Number(m.total_despesas);
                return (
                  <div
                    key={`${m.ano}-${m.mes}`}
                    className="flex-1 min-w-0 flex flex-col items-center justify-end gap-1 h-full"
                  >
                    <div className="flex items-end justify-center gap-1 w-full h-full">
                      <span
                        className="w-1/2 max-w-[26px] rounded-t bg-success/80"
                        style={{ height: `${(rec / maxValor) * 100}%` }}
                        title={`Receitas ${formatMesAno(m.ano, m.mes)}: ${formatBRL(rec)}`}
                      />
                      <span
                        className="w-1/2 max-w-[26px] rounded-t bg-brand/80"
                        style={{ height: `${(desp / maxValor) * 100}%` }}
                        title={`Despesas ${formatMesAno(m.ano, m.mes)}: ${formatBRL(desp)}`}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
            {/* Rótulos de mês + saldo */}
            <div className="flex gap-3 sm:gap-5 mt-2">
              {relatorio!.meses.map((m) => {
                const saldo = Number(m.saldo);
                return (
                  <div
                    key={`lbl-${m.ano}-${m.mes}`}
                    className="flex-1 min-w-0 text-center"
                  >
                    <div className="text-[11px] text-ink-mute truncate">
                      {formatMesAno(m.ano, m.mes)}
                    </div>
                    <div
                      className={`text-[11px] font-medium tabular-nums truncate ${
                        saldo >= 0 ? 'text-success-ink' : 'text-red-600'
                      }`}
                    >
                      {saldo >= 0 ? '+' : '−'}
                      {formatBRL(Math.abs(saldo))}
                    </div>
                  </div>
                );
              })}
            </div>
            {/* Legenda */}
            <div className="flex items-center gap-4 mt-4 text-[11.5px] text-ink-soft">
              <span className="inline-flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-sm bg-success/80" /> Receitas
              </span>
              <span className="inline-flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-sm bg-brand/80" /> Despesas
              </span>
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

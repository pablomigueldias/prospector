import { useMemo } from 'react';
import {
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  type TooltipProps,
} from 'recharts';

import { formatBRL } from '@/lib/format';
import type { CategoriaResumoItem } from '@/lib/types';

// Paleta OKLCH (mesma família do design system).
const CORES = [
  'oklch(0.62 0.17 25)',
  'oklch(0.68 0.15 70)',
  'oklch(0.70 0.13 145)',
  'oklch(0.62 0.13 230)',
  'oklch(0.60 0.16 300)',
  'oklch(0.66 0.14 340)',
  'oklch(0.72 0.12 110)',
  'oklch(0.55 0.06 50)',
];

function cor(i: number): string {
  return CORES[i % CORES.length];
}

interface Props {
  items: CategoriaResumoItem[];
  loading?: boolean;
}

export function CategoriaDonut({ items, loading }: Props) {
  const { total, segmentos } = useMemo(() => {
    const soma = items.reduce((acc, it) => acc + Number(it.total), 0);
    const segs = items.map((it, i) => ({
      ...it,
      valor: Number(it.total),
      cor: cor(i),
      pct: soma > 0 ? (Number(it.total) / soma) * 100 : 0,
    }));
    return { total: soma, segmentos: segs };
  }, [items]);

  if (loading) {
    return <div className="card p-6 h-[220px] animate-pulse" />;
  }
  if (items.length === 0) {
    return (
      <div className="card p-6 text-center text-ink-soft text-sm">
        Sem despesas neste período.
      </div>
    );
  }

  return (
    <div className="card p-5 flex flex-col sm:flex-row items-center gap-6">
      {/* Donut (Recharts) com total no centro */}
      <div className="relative shrink-0" style={{ width: 160, height: 160 }}>
        <ResponsiveContainer>
          <PieChart>
            <Pie
              data={segmentos}
              dataKey="valor"
              nameKey="categoria_nome"
              innerRadius={52}
              outerRadius={78}
              paddingAngle={1}
              stroke="none"
              startAngle={90}
              endAngle={-270}
            >
              {segmentos.map((s) => (
                <Cell key={s.categoria_id ?? s.categoria_nome} fill={s.cor} />
              ))}
            </Pie>
            <Tooltip content={<DonutTooltip total={total} />} />
          </PieChart>
        </ResponsiveContainer>
        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
          <div className="font-mono uppercase tracking-[0.1em] text-[9px] text-ink-mute">
            Despesas
          </div>
          <div className="font-display font-semibold tracking-tight text-base text-ink leading-tight text-center px-1">
            {formatBRL(total)}
          </div>
        </div>
      </div>

      {/* Legenda */}
      <ul className="flex-1 w-full m-0 p-0 list-none flex flex-col gap-2">
        {segmentos.map((s) => (
          <li
            key={s.categoria_id ?? s.categoria_nome}
            className="flex items-center gap-2.5 text-sm"
          >
            <span
              className="w-2.5 h-2.5 rounded-sm shrink-0"
              style={{ background: s.cor }}
            />
            <span className="text-ink flex-1 truncate">{s.categoria_nome}</span>
            <span className="text-ink-soft tabular-nums">{formatBRL(s.total)}</span>
            <span className="text-ink-mute text-[11px] tabular-nums w-10 text-right">
              {s.pct.toFixed(0)}%
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function DonutTooltip({
  active,
  payload,
  total,
}: TooltipProps<number, string> & { total: number }) {
  if (!active || !payload?.length) return null;
  const item = payload[0];
  const valor = Number(item.value ?? 0);
  const pct = total > 0 ? (valor / total) * 100 : 0;
  return (
    <div className="card px-3 py-2 shadow-brand-sm text-xs">
      <div className="flex items-center gap-2">
        <span
          className="w-2 h-2 rounded-full shrink-0"
          style={{ background: item.payload?.cor }}
        />
        <span className="text-ink-soft">{item.name}</span>
        <span className="ml-auto tabular-nums text-ink">{formatBRL(valor)}</span>
      </div>
      <div className="text-ink-mute text-[10.5px] mt-0.5 text-right">
        {pct.toFixed(0)}% das despesas
      </div>
    </div>
  );
}

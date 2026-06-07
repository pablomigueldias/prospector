import { useMemo } from 'react';

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
    let cursor = 0;
    const segs = items.map((it, i) => {
      const frac = soma > 0 ? Number(it.total) / soma : 0;
      const ini = cursor * 360;
      cursor += frac;
      return {
        ...it,
        cor: cor(i),
        pct: frac * 100,
        css: `${cor(i)} ${ini}deg ${cursor * 360}deg`,
      };
    });
    return { total: soma, segmentos: segs };
  }, [items]);

  if (loading) {
    return <div className="card p-6 h-[220px] animate-pulse" />;
  }
  if (items.length === 0) {
    return (
      <div className="card p-6 text-center text-ink-soft text-sm">
        Sem despesas neste mês.
      </div>
    );
  }

  const gradient = `conic-gradient(${segmentos.map((s) => s.css).join(', ')})`;

  return (
    <div className="card p-5 flex flex-col sm:flex-row items-center gap-6">
      {/* Donut */}
      <div className="relative shrink-0" style={{ width: 160, height: 160 }}>
        <div
          className="w-full h-full rounded-full"
          style={{ background: gradient }}
        />
        <div className="absolute inset-[22px] rounded-full bg-surface flex flex-col items-center justify-center">
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

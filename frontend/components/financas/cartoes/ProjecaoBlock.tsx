import { formatBRL, formatMesAno } from '@/lib/format';
import type { ProjecaoFaturas } from '@/lib/types';

/** Barras do comprometido por mês (todos os cartões), no topo da seção. */
export function ProjecaoBlock({ projecao }: { projecao: ProjecaoFaturas }) {
  const maximo = Math.max(...projecao.meses.map((m) => Number(m.total)), 1);
  return (
    <div className="card p-4 mb-3">
      <div className="flex items-baseline justify-between mb-3">
        <h3 className="font-mono uppercase tracking-[0.1em] text-[10px] text-ink-mute m-0">
          comprometido nos próximos meses
        </h3>
        <span className="text-[12px] text-ink-soft">
          total{' '}
          <span className="font-display font-semibold text-ink">
            {formatBRL(projecao.total)}
          </span>
        </span>
      </div>
      <ul className="m-0 p-0 list-none flex items-end gap-3 min-h-[88px]">
        {projecao.meses.map((m) => {
          const [a, mes] = m.mes_referencia.split('-').map(Number);
          const altura = Math.max(6, Math.round((Number(m.total) / maximo) * 56));
          return (
            <li key={m.mes_referencia} className="flex-1 flex flex-col items-center justify-end gap-1.5">
              <span className="text-[11px] tabular-nums text-ink-soft">
                {formatBRL(m.total)}
              </span>
              <div
                className="w-full max-w-[40px] rounded-t bg-brand"
                style={{ height: `${altura}px` }}
                title={`${formatMesAno(a, mes)}: ${formatBRL(m.total)}`}
              />
              <span className="font-mono uppercase tracking-[0.08em] text-[9px] text-ink-mute">
                {a && mes ? formatMesAno(a, mes) : m.mes_referencia}
              </span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

import { type FreelaTaxaPorStackItem } from '@/lib/types';

/**
 * "Onde insistir" — taxa de resposta por stack/categoria (§2.F). Mostra em quais
 * tecnologias as propostas mais voltam, pra concentrar esforço onde rende. Só
 * aparece quando há dados (stacks com volume mínimo, calculado no backend).
 */
export function OndeInsistir({
  itens,
  loading,
}: {
  itens: FreelaTaxaPorStackItem[];
  loading: boolean;
}) {
  if (loading || itens.length === 0) return null;

  const max = Math.max(...itens.map((i) => i.taxa_resposta), 0.01);

  return (
    <section className="card p-5 mt-7">
      <h2 className="font-display font-semibold text-base tracking-tight text-ink m-0 mb-1">
        Onde insistir
      </h2>
      <p className="text-[13px] text-ink-soft mt-0 mb-4">
        Taxa de resposta e de fechamento por stack — concentre a proposta onde o
        cliente mais volta e onde mais fecha.
      </p>
      <div className="flex flex-col gap-2.5">
        {itens.map((i) => (
          <div key={i.stack} className="flex items-center gap-3 text-[13px]">
            <span className="w-32 shrink-0 truncate text-ink" title={i.stack}>
              {i.stack}
            </span>
            <div className="flex-1 h-2 rounded-full bg-bg-alt overflow-hidden">
              <div
                className="h-full rounded-full bg-brand"
                style={{ width: `${(i.taxa_resposta / max) * 100}%` }}
              />
            </div>
            <span className="w-24 shrink-0 text-right tabular-nums text-ink-soft">
              {Math.round(i.taxa_resposta * 100)}%
              <span className="text-ink-faint">
                {' '}
                resp.
              </span>
            </span>
            <span
              className="w-24 shrink-0 text-right tabular-nums text-ink-soft"
              title={`${i.fechadas} de ${i.enviadas} propostas fecharam`}
            >
              <span
                className={i.win_rate > 0 ? 'text-emerald-700 font-medium' : 'text-ink-faint'}
              >
                {Math.round(i.win_rate * 100)}%
              </span>
              <span className="text-ink-faint"> win</span>
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}

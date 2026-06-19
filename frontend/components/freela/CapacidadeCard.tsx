import { type FreelaCapacidade } from '@/lib/types';

/**
 * Capacidade da semana (anti-furada, §2.C). Mostra horas livres vs comprometidas
 * pra não pegar projeto que você não entrega. O número da semana se ajusta em
 * Configurações (freela_capacidade_horas_semana); aqui é só leitura.
 */
export function CapacidadeCard({
  cap,
  loading,
}: {
  cap: FreelaCapacidade | undefined;
  loading: boolean;
}) {
  if (loading || !cap) return null;

  const usado = cap.horas_semana > 0 ? cap.horas_comprometidas / cap.horas_semana : 0;
  const pct = Math.min(100, Math.round(usado * 100));
  const lotado = cap.horas_livres <= 0;

  return (
    <section className="card p-4 mt-7">
      <div className="flex items-baseline justify-between gap-3 mb-2">
        <h2 className="font-display font-semibold text-base tracking-tight text-ink m-0">
          Capacidade da semana
        </h2>
        <span className={`text-[13px] font-medium ${lotado ? 'text-red-600' : 'text-ink-soft'}`}>
          {lotado ? 'sem mão livre' : `${cap.horas_livres}h livres`}
        </span>
      </div>
      <div className="h-2 rounded-full bg-bg-alt overflow-hidden">
        <div
          className={`h-full rounded-full ${lotado ? 'bg-red-500' : 'bg-brand'}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <p className="text-[12px] text-ink-mute mt-2 mb-0">
        {cap.horas_comprometidas}h comprometidas de {cap.horas_semana}h/semana ·
        ajuste em <span className="text-ink-soft">Configurações</span>.
      </p>
    </section>
  );
}

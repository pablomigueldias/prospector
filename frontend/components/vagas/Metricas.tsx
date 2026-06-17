import { StatCard } from '../StatCard';
import { type VagasMetricas } from '@/lib/types';

// ── Métricas (funil + taxas) ──────────────────────────────────────

export function Metricas({
  metricas,
  loading,
}: {
  metricas: VagasMetricas | null | undefined;
  loading: boolean;
}) {
  const m = metricas;
  const pct = (v: number | null | undefined) =>
    v == null ? '—' : `${v}%`;
  const matchCand = m?.match_medio_candidaturas ?? m?.match_medio ?? null;

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-7">
      <StatCard
        label="Vagas"
        value={m?.total ?? 0}
        trend={m ? `${m.em_andamento} em andamento` : undefined}
        loading={loading}
      />
      <StatCard
        label="Candidaturas"
        value={m?.candidaturas ?? 0}
        trend={m ? `${m.responderam} responderam` : undefined}
        trendDirection={m && m.responderam > 0 ? 'up' : 'neutral'}
        loading={loading}
      />
      <StatCard
        label="Taxa de resposta"
        value={pct(m?.taxa_resposta)}
        trend={m ? `${m.entrevistas} em entrevista` : undefined}
        trendDirection={m && (m.taxa_resposta ?? 0) >= 30 ? 'up' : 'neutral'}
        loading={loading}
      />
      <StatCard
        label="Match médio (candidaturas)"
        value={pct(matchCand)}
        trend="você está mirando vaga boa?"
        loading={loading}
      />
    </div>
  );
}


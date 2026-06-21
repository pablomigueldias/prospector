import { ResumoNoite } from '@/components/crm/ResumoNoite';
import { StatCard } from '@/components/shared/StatCard';
import { useFetch } from '@/hooks/useFetch';
import { api } from '@/lib/api';
import type { CrmDashboard, OutcomeResumo } from '@/lib/types';

function brl(v?: number | null): string {
  if (v == null) return '—';
  return v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}

export function DashboardSection() {
  const { data: d, loading } = useFetch<CrmDashboard>(() => api.crmDashboard(), []);
  const { data: out } = useFetch<OutcomeResumo>(
    () => api.memoriaOutcomesResumo(),
    [],
  );

  if (loading || !d) return <div className="card p-8 animate-pulse h-48" />;

  const maxValor = Math.max(1, ...d.por_estagio.map((e) => e.valor));

  return (
    <div className="flex flex-col gap-6">
      <ResumoNoite />

      <div>
        <h2 className="font-display font-semibold text-[15px] tracking-tight text-ink mb-3">
          Pipeline de vendas
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          <StatCard label="Valor no pipeline" value={brl(d.pipeline_valor)} />
          <StatCard
            label="Forecast ponderado"
            value={brl(d.pipeline_ponderado)}
            trend="valor × probabilidade"
            trendDirection="up"
          />
          <StatCard label="Negócios abertos" value={d.negocios_abertos} />
        </div>
      </div>

      {d.por_estagio.length > 0 && (
        <div className="card p-5">
          <h3 className="font-display font-semibold text-[13px] tracking-tight text-ink m-0 mb-3">
            Por estágio
          </h3>
          <div className="flex flex-col gap-2.5">
            {d.por_estagio.map((e) => (
              <div key={e.estagio} className="flex items-center gap-3">
                <div className="w-[150px] text-[13px] text-ink-soft truncate shrink-0">
                  {e.estagio}
                </div>
                <div className="flex-1 bg-bg-alt rounded h-5 overflow-hidden">
                  <div
                    className="h-full bg-brand/70 rounded"
                    style={{ width: `${(e.valor / maxValor) * 100}%` }}
                  />
                </div>
                <div className="w-[120px] text-right text-[12.5px] text-ink shrink-0">
                  {brl(e.valor)}{' '}
                  <span className="text-ink-mute">({e.total})</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div>
        <h2 className="font-display font-semibold text-[15px] tracking-tight text-ink mb-3">
          Atividades & entregas
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <StatCard label="Atividades pendentes" value={d.atividades_pendentes} />
          <StatCard
            label="Atrasadas"
            value={d.atividades_atrasadas}
            trendDirection={d.atividades_atrasadas > 0 ? 'down' : 'neutral'}
            trend={d.atividades_atrasadas > 0 ? 'precisam de ação' : 'em dia'}
          />
          <StatCard label="Projetos ativos" value={d.projetos_total} />
          <StatCard label="A receber" value={brl(d.projetos_a_receber)} />
        </div>
      </div>

      <div>
        <h2 className="font-display font-semibold text-[15px] tracking-tight text-ink mb-3">
          Carteira
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <StatCard label="Empresas" value={d.empresas_total} />
          <StatCard label="Clientes ativos" value={d.clientes_ativos} />
          <StatCard label="Contatos" value={d.contatos_total} />
          <StatCard
            label="Faturamento projetos"
            value={brl(d.projetos_valor_total)}
          />
        </div>
      </div>

      {out && out.total > 0 && (
        <div>
          <h2 className="font-display font-semibold text-[15px] tracking-tight text-ink mb-3">
            O que tem dado retorno
            <span className="text-[12px] text-ink-mute font-normal ml-2">
              (aprendizado — MAS-3)
            </span>
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <StatCard
              label="Taxa de retorno"
              value={
                out.taxa_positiva != null
                  ? `${Math.round(out.taxa_positiva * 100)}%`
                  : '—'
              }
              trend={`${out.positivos} de ${out.positivos + out.negativos} com sinal`}
              trendDirection={
                (out.taxa_positiva ?? 0) >= 0.5 ? 'up' : 'neutral'
              }
            />
            <StatCard label="Retornos +" value={out.positivos} />
            <StatCard label="Sem retorno" value={out.negativos} />
            <StatCard label="Resultados registrados" value={out.total} />
          </div>
          {Object.keys(out.por_resultado).length > 0 && (
            <div className="card p-4 mt-3 flex flex-wrap gap-2">
              {Object.entries(out.por_resultado)
                .sort((a, b) => b[1] - a[1])
                .map(([res, n]) => (
                  <span
                    key={res}
                    className="text-[12px] bg-bg-alt text-ink-soft px-2 py-0.5 rounded-full"
                  >
                    {res}: <span className="text-ink font-medium">{n}</span>
                  </span>
                ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

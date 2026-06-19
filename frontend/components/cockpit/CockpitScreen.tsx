import Link from 'next/link';

import { IconFromName, IconArrowRight } from '@/components/shared/Icon';
import { MoreAgentsSection } from '@/components/shared/MoreAgentsSection';
import { ResumoNoite } from '@/components/crm/ResumoNoite';
import { useAgents } from '@/hooks/useAgents';
import { useAuth } from '@/contexts/AuthContext';
import { permissaoDoAgente } from '@/lib/permissions';
import type { Agent } from '@/lib/types';

/**
 * S1 — Central de Agentes (cockpit). A home do sistema: uma tela só com
 *   1) o "Resumo da Noite" (MAS-4) no topo = o que precisa de você hoje;
 *   2) os agentes ativos como cards clicáveis (dirigidos pelo registry);
 *   3) os próximos agentes da plataforma.
 * Tudo já existe no backend (registry + /orchestrator/briefing) — isto é
 * montagem de front pra "abrir o sistema e ver tudo num lugar".
 */
export function CockpitScreen() {
  const { agents, loading } = useAgents();
  const { usuario, hasPermission } = useAuth();

  // Só os ativos que o usuário pode usar (mesma regra de UX do menu lateral).
  const ativos = agents.filter((a) => {
    if (a.status !== 'active') return false;
    const need = permissaoDoAgente(a.slug);
    return !need || hasPermission(need);
  });

  const primeiroNome = usuario?.nome?.split(' ')[0];

  return (
    <div className="flex flex-col gap-8">
      <header>
        <div className="eyebrow mb-2">Central de Agentes</div>
        <h1 className="font-display font-semibold text-2xl tracking-tight text-ink m-0">
          {primeiroNome ? `Bom te ver, ${primeiroNome}.` : 'Seu cockpit'}
        </h1>
        <p className="text-[15px] text-ink-soft mt-1 mb-0 max-w-[60ch]">
          Tudo que importa numa tela só — o que precisa de você hoje e seus
          agentes a um clique.
        </p>
      </header>

      {/* O que precisa de você hoje (MAS-4) */}
      <ResumoNoite />

      {/* Agentes ativos */}
      <section>
        <h2 className="font-display font-semibold text-base tracking-tight text-ink mb-3">
          Seus agentes
        </h2>
        {loading && ativos.length === 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {[0, 1, 2].map((i) => (
              <div key={i} className="card p-[18px] animate-pulse h-28" />
            ))}
          </div>
        ) : ativos.length === 0 ? (
          <p className="text-[13px] text-ink-mute m-0">
            Nenhum agente disponível pra você ainda.
          </p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {ativos.map((agent) => (
              <AgentCard key={agent.slug} agent={agent} />
            ))}
          </div>
        )}
      </section>

      {/* Próximos agentes (reusa o card existente) */}
      <MoreAgentsSection agents={agents} />
    </div>
  );
}

function AgentCard({ agent }: { agent: Agent }) {
  return (
    <Link
      href={`/agents/${agent.slug}`}
      className="group card p-[18px] flex flex-col gap-2 transition-colors hover:border-brand/40"
    >
      <div className="flex items-center justify-between">
        <div className="w-9 h-9 rounded bg-brand-soft/40 flex items-center justify-center text-brand-ink">
          <IconFromName name={agent.icon} className="text-base" />
        </div>
        <IconArrowRight className="text-ink-faint group-hover:text-brand transition-colors" />
      </div>
      <h3 className="font-display font-semibold text-[15px] text-ink mt-1 mb-0">
        {agent.name}
      </h3>
      <p className="text-[13px] text-ink-mute leading-snug m-0 line-clamp-2">
        {agent.description}
      </p>
    </Link>
  );
}

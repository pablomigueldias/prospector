import { IconFromName } from './Icon';
import type { Agent } from '@/lib/types';

interface MoreAgentsSectionProps {
  agents: Agent[];
}

export function MoreAgentsSection({ agents }: MoreAgentsSectionProps) {
  const upcoming = agents.filter((a) => a.status !== 'active');
  if (upcoming.length === 0) return null;

  return (
    <section className="bg-bg-alt rounded-lg p-6">
      <div className="mb-1">
        <h2 className="font-display font-semibold text-base tracking-tight text-ink">
          Próximos agentes da plataforma
        </h2>
      </div>
      <p className="text-[13px] text-ink-mute max-w-[60ch] m-0">
        A arquitetura está pronta pra plugar novos agentes — cada um vira
        um módulo no menu lateral sem precisar reescrever o dashboard.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mt-4">
        {upcoming.map((agent) => (
          <UpcomingAgentCard key={agent.slug} agent={agent} />
        ))}
      </div>
    </section>
  );
}

function UpcomingAgentCard({ agent }: { agent: Agent }) {
  return (
    <div className="bg-surface border border-dashed border-line rounded-lg p-[18px] flex flex-col gap-2">
      <div className="w-8 h-8 rounded bg-bg flex items-center justify-center text-ink-mute">
        <IconFromName name={agent.icon} className="text-base" />
      </div>
      <h4 className="font-display font-semibold text-sm text-ink-soft mt-1 mb-0">
        {agent.name}
      </h4>
      <p className="text-xs text-ink-mute leading-snug m-0">
        {agent.description}
      </p>
      {agent.roadmap_label && (
        <span className="font-mono text-[9.5px] uppercase tracking-[0.08em] text-ink-faint mt-1.5">
          {agent.roadmap_label}
        </span>
      )}
    </div>
  );
}

import Head from 'next/head';
import { useRouter } from 'next/router';
import { useMemo } from 'react';

import { DashboardLayout } from '@/components/DashboardLayout';
import { IconRocket } from '@/components/Icon';
import { LeadHistoryList } from '@/components/LeadRow';
import { MoreAgentsSection } from '@/components/MoreAgentsSection';
import { ProspectorForm } from '@/components/ProspectorForm';
import { StatCard } from '@/components/StatCard';
import { useAgent, useAgents } from '@/hooks/useAgents';
import { useProspectorHistory } from '@/hooks/useProspector';

export default function AgentPage() {
  const router = useRouter();
  const slug =
    typeof router.query.slug === 'string' ? router.query.slug : undefined;

  const { agent, loading: agentLoading } = useAgent(slug);
  const { agents } = useAgents();

  if (agentLoading) {
    return (
      <DashboardLayout>
        <div className="text-ink-mute">Carregando agente…</div>
      </DashboardLayout>
    );
  }

  if (!agent) {
    return (
      <DashboardLayout>
        <div className="text-ink">Agente não encontrado.</div>
      </DashboardLayout>
    );
  }

  return (
    <>
      <Head>
        <title>{agent.name} · Reative Systems</title>
      </Head>
      <DashboardLayout currentAgentName={agent.name}>
        {agent.slug === 'prospector' ? (
          <ProspectorScreen agents={agents} />
        ) : (
          <ComingSoonScreen agentName={agent.name} />
        )}
      </DashboardLayout>
    </>
  );
}

function ProspectorScreen({ agents }: { agents: import('@/lib/types').Agent[] }) {
  const history = useProspectorHistory(20);

  const stats = useMemo(() => {
    const todayKey = new Date().toISOString().slice(0, 10);
    const leadsHoje = history.items.filter((i) =>
      i.enviado_em?.startsWith(todayKey),
    ).length;
    return {
      leadsHoje,
      total: history.total,
    };
  }, [history.items, history.total]);

  return (
    <div className="max-w-[1200px] mx-auto">
      <header className="mb-7">
        <div className="eyebrow mb-3">Agente 01 · Prospecção comercial</div>
        <h1 className="font-display font-semibold text-[38px] leading-[1.05] tracking-tighter text-ink m-0 mb-2.5">
          Prospector
        </h1>
        <p className="text-[15px] text-ink-soft max-w-[60ch] leading-relaxed m-0">
          Cadastra empresas, descobre contatos decisores e envia tudo direto
          pro Notion. Funciona em modo manual (CNPJ + site) ou investigação
          automática.
        </p>
      </header>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-7">
        <StatCard
          label="Leads hoje"
          value={stats.leadsHoje}
          loading={history.loading}
        />
        <StatCard
          label="Total recente"
          value={stats.total}
          loading={history.loading}
        />
        <StatCard
          label="Pipeline"
          value="OK"
          trend="BrasilAPI + OpenCNPJ"
          loading={false}
        />
        <StatCard
          label="Status"
          value="Online"
          trend="API conectada"
          trendDirection="up"
          loading={false}
        />
      </div>

      <Tabs />

      <div className="mb-6">
        <ProspectorForm onLeadCreated={() => history.refetch()} />
      </div>

      <section className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-display font-semibold text-lg tracking-tight text-ink m-0">
            Histórico recente
          </h2>
          {history.total > 0 && (
            <span className="text-[12.5px] text-ink-mute">
              {history.total} {history.total === 1 ? 'lead' : 'leads'}
            </span>
          )}
        </div>
        <LeadHistoryList
          items={history.items}
          loading={history.loading}
          error={history.error}
        />
      </section>

      <MoreAgentsSection agents={agents} />
    </div>
  );
}

function ComingSoonScreen({ agentName }: { agentName: string }) {
  return (
    <div className="max-w-2xl mx-auto pt-16 text-center flex flex-col items-center gap-5">
      <div className="w-16 h-16 rounded-lg bg-brand-soft text-brand flex items-center justify-center">
        <IconRocket className="text-3xl" />
      </div>
      <div>
        <div className="eyebrow justify-center mb-3">Em construção</div>
        <h1 className="font-display font-semibold text-3xl tracking-tight text-ink mb-2">
          {agentName} chegando em breve
        </h1>
        <p className="text-[15px] text-ink-soft max-w-md mx-auto">
          A plataforma já está pronta pra receber esse agente. Quando ele
          estiver ativo, essa tela vira o painel dele — sem reescrever nada.
        </p>
      </div>
    </div>
  );
}

function Tabs() {
  return (
    <div className="flex gap-1 border-b border-line mb-6 -mb-px">
      <div className="px-4 py-2.5 text-[13.5px] font-medium border-b-2 border-brand text-brand flex items-center gap-2">
        Cadastro manual
      </div>
      <div className="px-4 py-2.5 text-[13.5px] font-medium text-ink-faint cursor-not-allowed flex items-center gap-2">
        Investigar
        <span className="font-mono text-[9px] uppercase tracking-[0.08em] bg-bg-alt text-ink-mute px-1.5 py-0.5 rounded-sm">
          em breve
        </span>
      </div>
      <div className="px-4 py-2.5 text-[13.5px] font-medium text-ink-faint cursor-not-allowed flex items-center gap-2">
        Importar CSV
        <span className="font-mono text-[9px] uppercase tracking-[0.08em] bg-bg-alt text-ink-mute px-1.5 py-0.5 rounded-sm">
          em breve
        </span>
      </div>
    </div>
  );
}

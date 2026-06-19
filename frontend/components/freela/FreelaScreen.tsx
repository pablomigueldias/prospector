import { useState } from 'react';

import { OpcoesManager } from '@/components/crm/OpcoesManager';
import { StatCard } from '@/components/shared/StatCard';
import { ClientesPanel } from '@/components/freela/ClientesPanel';
import { FilaProjetos } from '@/components/freela/FilaProjetos';
import { Kanban } from '@/components/freela/Kanban';
import { MetaForecast } from '@/components/freela/MetaForecast';
import { NovoProjetoForm } from '@/components/freela/NovoProjetoForm';
import { OndeInsistir } from '@/components/freela/OndeInsistir';
import { PerdaDialog } from '@/components/freela/PerdaDialog';
import { PlanoMetaPanel } from '@/components/freela/PlanoMetaPanel';
import { Precificador } from '@/components/freela/Precificador';
import { PropostaModal } from '@/components/freela/PropostaModal';
import { formatBRL } from '@/lib/format';
import {
  useFreelaActions,
  useFreelaClientes,
  useFreelaKanban,
  useFreelaMetricas,
  useFreelaPlataformas,
  useFreelaProjetos,
  useFreelaTaxaPorStack,
} from '@/hooks/useFreela';
import { type FreelaKanbanItem } from '@/lib/types';

/** Horas médias → "—" / "8h" / "2d 3h". */
function formatHoras(h?: number | null): string {
  if (h == null) return '—';
  const horas = Math.round(h);
  if (horas < 24) return `${horas}h`;
  const d = Math.floor(horas / 24);
  const r = horas % 24;
  return r ? `${d}d ${r}h` : `${d}d`;
}

export default function FreelaScreen() {
  const kanban = useFreelaKanban();
  const metricas = useFreelaMetricas();
  const projetos = useFreelaProjetos();
  const plataformas = useFreelaPlataformas();
  const clientes = useFreelaClientes();
  const taxaStack = useFreelaTaxaPorStack();
  const acoes = useFreelaActions();

  const [mostrarForm, setMostrarForm] = useState(false);
  const [propostaAberta, setPropostaAberta] = useState<FreelaKanbanItem | null>(null);
  const [perdaItem, setPerdaItem] = useState<FreelaKanbanItem | null>(null);
  const [gerirOpcoes, setGerirOpcoes] = useState(false);

  function refetchTudo() {
    void kanban.refetch();
    void metricas.refetch();
    void projetos.refetch();
  }

  const m = metricas.data;
  // Cold start: ainda sem nenhuma fechada → o foco é RESPOSTA, não fechamento.
  const coldStart = (m?.fechadas ?? 0) === 0;

  return (
    <div className="max-w-[1200px] mx-auto pb-16">
      <header className="mb-7">
        <div className="eyebrow mb-3">Pessoal · Copiloto de propostas</div>
        <h1 className="font-display font-semibold text-[38px] leading-[1.05] tracking-tighter text-ink m-0 mb-2.5">
          Freela
        </h1>
        <p className="text-[15px] text-ink-soft max-w-[64ch] leading-relaxed m-0">
          Cola o projeto da Workana, descobre onde vale gastar proposta,
          precifica pra receber o que você quer e acompanha tudo num Kanban. A
          IA não toca na Workana — você revisa, envia na mão e marca o status.
        </p>
      </header>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-7">
        <StatCard
          label="Propostas"
          value={m?.total_propostas ?? 0}
          trend={m ? `${m.enviadas} enviadas` : undefined}
          loading={metricas.loading}
        />
        <StatCard
          label="Taxa de resposta"
          value={m ? `${Math.round(m.taxa_resposta * 100)}%` : '—'}
          trend={m ? `${m.respondidas} responderam` : undefined}
          trendDirection={m && m.taxa_resposta >= 0.15 ? 'up' : 'neutral'}
          loading={metricas.loading}
        />
        {coldStart ? (
          <>
            <StatCard
              label="Em conversa"
              value={m?.respondidas ?? 0}
              trend="responderam ou negociando"
              loading={metricas.loading}
            />
            <StatCard
              label="Tempo até resposta"
              value={formatHoras(m?.tempo_medio_resposta_horas)}
              trend="quanto antes, melhor"
              loading={metricas.loading}
            />
          </>
        ) : (
          <>
            <StatCard
              label="Taxa de fechamento"
              value={m ? `${Math.round(m.taxa_fechamento * 100)}%` : '—'}
              loading={metricas.loading}
            />
            <StatCard
              label="Líquido fechado"
              value={formatBRL(m?.liquido_total_fechado ?? 0)}
              loading={metricas.loading}
            />
          </>
        )}
      </div>

      <PlanoMetaPanel refreshKey={m?.fechadas ?? 0} />

      <OndeInsistir itens={taxaStack.itens} loading={taxaStack.loading} />

      {!coldStart && <MetaForecast m={m} loading={metricas.loading} />}

      <Precificador
        plataformaId={plataformas.items[0]?.id ?? null}
        clientes={clientes.items.map((c) => ({ id: c.id, nome: c.nome }))}
      />

      <ClientesPanel
        clientes={clientes.items}
        loading={clientes.loading}
        salvando={acoes.loading}
        plataformas={plataformas.items.map((p) => ({ id: p.id, nome: p.nome }))}
        onCriar={acoes.criarCliente}
        onAtualizar={acoes.atualizarCliente}
        onRemover={acoes.removerCliente}
        onMudou={() => clientes.refetch()}
      />

      {/* Fila de oportunidades */}
      <div className="flex items-center justify-between mt-8 mb-4">
        <h2 className="font-display font-semibold text-lg tracking-tight text-ink m-0">
          Fila de oportunidades
        </h2>
        <button
          type="button"
          className="btn-primary"
          onClick={() => setMostrarForm((v) => !v)}
        >
          {mostrarForm ? 'Fechar' : '+ Colar projeto'}
        </button>
      </div>

      {mostrarForm && (
        <NovoProjetoForm
          loading={acoes.loading}
          erro={acoes.error?.message ?? null}
          clientes={clientes.items.map((c) => ({ id: c.id, nome: c.nome }))}
          onExtrair={acoes.extrairProjeto}
          onSubmit={async (body) => {
            const p = await acoes.criarProjeto(body);
            if (p) {
              setMostrarForm(false);
              projetos.refetch();
            }
          }}
        />
      )}

      <FilaProjetos
        items={projetos.items}
        loading={projetos.loading}
        onCriarProposta={async (projetoId, valorCotado, liquido, horas, prazo) => {
          const p = await acoes.criarProposta({
            projeto_id: projetoId,
            valor_cotado: valorCotado,
            valor_liquido_estimado: liquido,
            horas_estimadas: horas,
            prazo_proposto: prazo,
          });
          if (p) refetchTudo();
        }}
        onAnalisar={async (id) => {
          const r = await acoes.analisarProjeto(id);
          if (r) void projetos.refetch();
          return r?.analise ?? null;
        }}
        onAtualizar={async (id, patch) => {
          const r = await acoes.atualizarProjeto(id, patch);
          if (r) void projetos.refetch();
        }}
        onRemover={async (id) => {
          if (confirm('Remover este projeto e suas propostas?')) {
            await acoes.removerProjeto(id);
            refetchTudo();
          }
        }}
      />

      {/* Kanban */}
      <div className="flex items-center justify-between mt-10 mb-4">
        <h2 className="font-display font-semibold text-lg tracking-tight text-ink m-0">
          Kanban de propostas
        </h2>
        <button
          type="button"
          className="btn-ghost text-[13px]"
          onClick={() => setGerirOpcoes(true)}
          title="Gerenciar listas (motivo de perda)"
        >
          ⚙ Opções
        </button>
      </div>
      <Kanban
        colunas={kanban.colunas}
        loading={kanban.loading}
        onAbrir={setPropostaAberta}
        onMover={async (id, status) => {
          if (status === 'perdida') {
            const it = kanban.colunas.flatMap((c) => c.items).find((i) => i.id === id);
            if (it) setPerdaItem(it);
            return;
          }
          await acoes.mudarStatus(id, status, null);
          refetchTudo();
        }}
        onRemover={async (id) => {
          if (confirm('Remover esta proposta?')) {
            await acoes.removerProposta(id);
            refetchTudo();
          }
        }}
      />

      {propostaAberta && (
        <PropostaModal
          item={propostaAberta}
          onClose={() => setPropostaAberta(null)}
          onMudou={refetchTudo}
        />
      )}

      {perdaItem && (
        <PerdaDialog
          item={perdaItem}
          onCancel={() => setPerdaItem(null)}
          onConfirm={async (motivo) => {
            await acoes.mudarStatus(perdaItem.id, 'perdida', motivo);
            setPerdaItem(null);
            refetchTudo();
          }}
        />
      )}

      {gerirOpcoes && (
        <OpcoesManager
          onClose={() => setGerirOpcoes(false)}
          grupos={[{ grupo: 'freela_motivo_perda', label: 'Motivo de perda' }]}
          titulo="Opções do freela"
          descricao="Listas gerenciáveis do freela. O motivo de perda alimenta o diálogo ao marcar uma proposta como perdida."
        />
      )}
    </div>
  );
}

import { useState } from 'react';

import { Metricas } from '@/components/vagas/Metricas';
import { PainelEstudo } from '@/components/vagas/PainelEstudo';
import { FiltrosBar } from '@/components/vagas/FiltrosBar';
import { ListaVagas } from '@/components/vagas/ListaVagas';
import { VagaDetalhe } from '@/components/vagas/VagaDetalhe';
import { NovaVagaForm } from '@/components/vagas/NovaVagaForm';
import { FILTRO_VAZIO } from '@/components/vagas/_shared';
import { usePerfil } from '@/hooks/usePerfil';
import {
  useVagaActions,
  useVagas,
  useVagasEstudo,
  useVagasMetricas,
} from '@/hooks/useVagas';
import type { VagaCreate, VagasFiltro } from '@/lib/types';

export default function VagasScreen() {
  const [filtro, setFiltro] = useState<VagasFiltro>(FILTRO_VAZIO);
  const vagas = useVagas(filtro);
  const metr = useVagasMetricas();
  const est = useVagasEstudo();
  const { perfil } = usePerfil();
  const acoes = useVagaActions();
  const [selecionada, setSelecionada] = useState<string | null>(null);
  const [mostrarForm, setMostrarForm] = useState(false);

  const semPerfil = perfil === null;

  function recarregar() {
    vagas.refetch();
    metr.refetch();
    est.refetch();
  }

  async function handleCriar(body: VagaCreate) {
    const v = await acoes.criar(body);
    if (v) {
      setMostrarForm(false);
      recarregar();
      setSelecionada(v.id);
    }
  }

  return (
    <div className="max-w-[1200px] mx-auto pb-16">
      <header className="mb-7">
        <div className="eyebrow mb-3">Pessoal · Caçador de vagas</div>
        <h1 className="font-display font-semibold text-[38px] leading-[1.05] tracking-tighter text-ink m-0 mb-2.5">
          Vagas
        </h1>
        <p className="text-[15px] text-ink-soft max-w-[62ch] leading-relaxed m-0">
          Cola a descrição da vaga, deixa a IA destrinchar o que ela exige,
          mede seu match e rascunha o e-mail de candidatura no seu tom. A
          ferramenta PARA no rascunho — você revisa e envia.
        </p>
      </header>

      {semPerfil && (
        <div className="mb-6 text-[13px] text-brand-ink bg-brand-soft/60 border border-brand/30 rounded p-3">
          Você ainda não tem um <strong>Perfil Mestre</strong>. Pode registrar
          vagas, mas a análise e a geração de candidatura precisam dele — crie o
          perfil primeiro.
        </div>
      )}

      <Metricas metricas={metr.metricas} loading={metr.loading} />

      <PainelEstudo estudo={est.estudo} loading={est.loading} />

      <div className="flex items-center justify-between mb-4">
        <h2 className="font-display font-semibold text-lg tracking-tight text-ink m-0">
          Suas vagas
        </h2>
        <button
          type="button"
          className="btn-primary"
          onClick={() => setMostrarForm((v) => !v)}
        >
          {mostrarForm ? 'Fechar' : '+ Nova vaga'}
        </button>
      </div>

      {mostrarForm && (
        <NovaVagaForm
          onSubmit={handleCriar}
          onExtrair={acoes.extrair}
          loading={acoes.loading}
          erro={acoes.error?.message ?? null}
        />
      )}

      <FiltrosBar
        filtro={filtro}
        onMudar={setFiltro}
        total={vagas.total}
        loading={vagas.loading}
      />

      <div className="grid md:grid-cols-[340px_1fr] gap-5 mt-2">
        <ListaVagas
          items={vagas.items}
          loading={vagas.loading}
          selecionada={selecionada}
          onSelecionar={setSelecionada}
        />
        {/* min-w-0: sem isso a coluna 1fr cresce com conteúdo não-quebrável
            (ex.: URL longa da vaga), estourando o card e a barra de etapas. */}
        <div className="min-w-0">
          {selecionada ? (
            <VagaDetalhe
              key={selecionada}
              vagaId={selecionada}
              semPerfil={semPerfil}
              onMudou={recarregar}
              onExcluida={() => {
                setSelecionada(null);
                recarregar();
              }}
            />
          ) : (
            <div className="card p-8 text-center text-sm text-ink-mute">
              Selecione uma vaga pra ver a análise e gerar a candidatura.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}


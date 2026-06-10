import { useCallback, useMemo, useState } from 'react';

import { CartoesSection } from '@/components/CartoesSection';
import { CategoriaDonut } from '@/components/CategoriaDonut';
import { CategoriasSection } from '@/components/CategoriasSection';
import { ComprovantesGaleria } from '@/components/ComprovantesGaleria';
import { ConsumoSection } from '@/components/ConsumoSection';
import { ContasSection } from '@/components/ContasSection';
import { StatCard } from '@/components/StatCard';
import { TransacoesSection } from '@/components/TransacoesSection';
import { useContas, useResumoMes } from '@/hooks/useFinancas';
import { useFinancasEventos } from '@/hooks/useFinancasEventos';
import { FINANCAS_USUARIO_ID } from '@/lib/financas';
import { formatBRL, formatMesAno } from '@/lib/format';

function mesAnterior(ano: number, mes: number): [number, number] {
  return mes === 1 ? [ano - 1, 12] : [ano, mes - 1];
}
function mesSeguinte(ano: number, mes: number): [number, number] {
  return mes === 12 ? [ano + 1, 1] : [ano, mes + 1];
}

export default function FinancasScreen() {
  const hoje = new Date();
  const [[ano, mes], setMes] = useState<[number, number]>([
    hoje.getFullYear(),
    hoje.getMonth() + 1,
  ]);

  const { resumo, loading: resumoLoading, refetch: refetchResumo } = useResumoMes(ano, mes);
  const { contas, loading: contasLoading, refetch: refetchContas } = useContas(true);

  // Atualiza sozinho quando algo muda (ex.: gasto lançado pelo Telegram).
  const aoVivo = useFinancasEventos(
    FINANCAS_USUARIO_ID,
    useCallback(() => {
      void refetchResumo();
      void refetchContas();
    }, [refetchResumo, refetchContas]),
  );

  const saldoTotal = useMemo(
    () => contas.reduce((acc, c) => acc + Number(c.saldo_atual), 0),
    [contas],
  );

  const recarregarTudo = useCallback(() => {
    void refetchResumo();
    void refetchContas();
  }, [refetchResumo, refetchContas]);

  const saldoMes = Number(resumo?.saldo ?? 0);

  return (
    <div className="max-w-[1200px] mx-auto">
      <header className="mb-7">
        <div className="eyebrow mb-3">Pessoal · Organizador financeiro</div>
        <h1 className="font-display font-semibold text-[38px] leading-[1.05] tracking-tighter text-ink m-0 mb-2.5">
          Finanças
        </h1>
        <p className="text-[15px] text-ink-soft max-w-[60ch] leading-relaxed m-0">
          Sua visão do mês: saldo das contas, o que entrou, o que saiu e quanto
          sobrou. Lançar gasto e importar boleto é pelo Telegram.
        </p>
      </header>

      {/* Navegação de mês */}
      <div className="flex items-center gap-3 mb-5">
        <button
          type="button"
          onClick={() => setMes(mesAnterior(ano, mes))}
          className="btn-ghost px-3 py-1.5 text-sm"
          aria-label="Mês anterior"
        >
          ‹
        </button>
        <div className="font-display font-semibold text-lg tracking-tight text-ink min-w-[120px] text-center">
          {formatMesAno(ano, mes)}
        </div>
        <button
          type="button"
          onClick={() => setMes(mesSeguinte(ano, mes))}
          className="btn-ghost px-3 py-1.5 text-sm"
          aria-label="Próximo mês"
        >
          ›
        </button>
        {aoVivo && (
          <span
            className="ml-auto inline-flex items-center gap-1.5 text-[11px] text-success"
            title="Atualizando em tempo real"
          >
            <span className="w-2 h-2 rounded-full bg-success animate-pulse" />
            ao vivo
          </span>
        )}
      </div>

      {/* Cards do mês */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-7">
        <StatCard
          label="Saldo nas contas"
          value={formatBRL(saldoTotal)}
          loading={contasLoading}
        />
        <StatCard
          label="Receitas do mês"
          value={formatBRL(resumo?.total_receitas)}
          loading={resumoLoading}
        />
        <StatCard
          label="Despesas do mês"
          value={formatBRL(resumo?.total_despesas)}
          loading={resumoLoading}
        />
        <StatCard
          label="Sobra / Déficit"
          value={formatBRL(saldoMes)}
          trend={saldoMes >= 0 ? 'no azul' : 'no vermelho'}
          trendDirection={saldoMes >= 0 ? 'up' : 'down'}
          loading={resumoLoading}
        />
      </div>

      {/* Despesas por categoria */}
      <section className="mb-8">
        <h2 className="font-display font-semibold text-lg tracking-tight text-ink m-0 mb-4">
          Despesas por categoria
        </h2>
        <CategoriaDonut
          items={resumo?.por_categoria ?? []}
          loading={resumoLoading}
        />
      </section>

      {/* Contas + Reservas (com criar/editar/excluir) */}
      <ContasSection
        contas={contas}
        loading={contasLoading}
        onChanged={refetchContas}
      />

      {/* Transações: lista filtrável + lançar/excluir */}
      <TransacoesSection
        ano={ano}
        mes={mes}
        contas={contas}
        onMutate={recarregarTudo}
      />

      {/* Consumo (água/gás/luz) */}
      <section className="mb-8">
        <h2 className="font-display font-semibold text-lg tracking-tight text-ink m-0 mb-4">
          Consumo
        </h2>
        <ConsumoSection />
      </section>

      {/* Cartões */}
      <section className="mb-8">
        <h2 className="font-display font-semibold text-lg tracking-tight text-ink m-0 mb-4">
          Cartões
        </h2>
        <CartoesSection />
      </section>

      {/* Categorias (criar/editar/excluir) */}
      <CategoriasSection />

      {/* Comprovantes */}
      <section className="mb-8">
        <h2 className="font-display font-semibold text-lg tracking-tight text-ink m-0 mb-4">
          Comprovantes
        </h2>
        <ComprovantesGaleria />
      </section>
    </div>
  );
}

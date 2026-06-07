import { useMemo, useState } from 'react';

import { CartoesSection } from '@/components/CartoesSection';
import { CategoriaDonut } from '@/components/CategoriaDonut';
import { StatCard } from '@/components/StatCard';
import { useContas, useResumoMes } from '@/hooks/useFinancas';
import { formatBRL, formatMesAno } from '@/lib/format';
import type { Conta } from '@/lib/types';

const TIPO_LABEL: Record<string, string> = {
  corrente: 'Conta corrente',
  dinheiro: 'Dinheiro',
  vr: 'Vale-refeição',
  va: 'Vale-alimentação',
  reserva: 'Reserva',
  cartao_credito: 'Cartão de crédito',
};

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

  const { resumo, loading: resumoLoading } = useResumoMes(ano, mes);
  const { contas, loading: contasLoading } = useContas(true);

  const saldoTotal = useMemo(
    () => contas.reduce((acc, c) => acc + Number(c.saldo_atual), 0),
    [contas],
  );

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

      {/* Contas */}
      <section className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-display font-semibold text-lg tracking-tight text-ink m-0">
            Contas
          </h2>
          {contas.length > 0 && (
            <span className="text-[12.5px] text-ink-mute">
              {contas.length} {contas.length === 1 ? 'conta' : 'contas'}
            </span>
          )}
        </div>
        <ContasList contas={contas} loading={contasLoading} />
      </section>

      {/* Cartões */}
      <section className="mb-8">
        <h2 className="font-display font-semibold text-lg tracking-tight text-ink m-0 mb-4">
          Cartões
        </h2>
        <CartoesSection />
      </section>
    </div>
  );
}

function ContasList({ contas, loading }: { contas: Conta[]; loading: boolean }) {
  if (loading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {[0, 1, 2].map((i) => (
          <div key={i} className="card p-4 h-[84px] animate-pulse" />
        ))}
      </div>
    );
  }
  if (contas.length === 0) {
    return (
      <div className="card p-6 text-center text-ink-soft text-sm">
        Nenhuma conta ainda. Cadastre uma conta pra começar a lançar.
      </div>
    );
  }
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
      {contas.map((c) => (
        <div key={c.id} className="card p-4">
          <div className="font-mono uppercase tracking-[0.1em] text-[10px] text-ink-mute mb-1">
            {TIPO_LABEL[c.tipo] ?? c.tipo}
          </div>
          <div className="font-medium text-ink mb-1.5">{c.nome}</div>
          <div className="font-display font-semibold tracking-tight text-xl text-ink leading-none">
            {formatBRL(c.saldo_atual)}
          </div>
        </div>
      ))}
    </div>
  );
}

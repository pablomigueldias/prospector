import { useCallback, useEffect, useMemo, useState } from 'react';

import { IconPlus } from '@/components/Icon';
import { CartoesSection } from '@/components/CartoesSection';
import { CategoriaDonut } from '@/components/CategoriaDonut';
import { CategoriasSection } from '@/components/CategoriasSection';
import { ComprovantesGaleria } from '@/components/ComprovantesGaleria';
import { ConsumoSection } from '@/components/ConsumoSection';
import { ContasSection } from '@/components/ContasSection';
import { DevSyncButton } from '@/components/DevSyncButton';
import { RecorrenciasSection } from '@/components/RecorrenciasSection';
import { RelatorioSection } from '@/components/RelatorioSection';
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

/** Atalhos da sub-navegação (id da seção → rótulo). */
const SECOES: { id: string; label: string }[] = [
  { id: 'sec-visao', label: 'Visão' },
  { id: 'sec-relatorio', label: 'Relatório' },
  { id: 'sec-contas', label: 'Contas' },
  { id: 'sec-transacoes', label: 'Transações' },
  { id: 'sec-consumo', label: 'Consumo' },
  { id: 'sec-cartoes', label: 'Cartões' },
  { id: 'sec-fixas', label: 'Contas fixas' },
  { id: 'sec-categorias', label: 'Categorias' },
  { id: 'sec-comprovantes', label: 'Comprovantes' },
];

function irPara(id: string) {
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function SecaoNav() {
  return (
    <nav className="sticky top-0 z-30 -mx-8 px-8 py-2.5 mb-6 bg-bg/90 backdrop-blur border-b border-line-soft flex flex-wrap gap-1.5">
      {SECOES.map((s) => (
        <button
          key={s.id}
          type="button"
          onClick={() => irPara(s.id)}
          className="text-[12.5px] text-ink-soft hover:text-ink hover:bg-line-soft rounded-pill px-3 py-1 transition-colors"
        >
          {s.label}
        </button>
      ))}
    </nav>
  );
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

  // Modal "novo lançamento" — controlado aqui pra abrir de qualquer lugar
  // (botão na seção Transações, FAB flutuante ou atalho de teclado).
  const [lancarAberto, setLancarAberto] = useState(false);
  const podeLancar = contas.length > 0;

  // Atalhos: "N" (fora de campos) ou Ctrl/Cmd+K abrem o lançamento.
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      const alvo = e.target as HTMLElement | null;
      const digitando =
        !!alvo &&
        (alvo.tagName === 'INPUT' ||
          alvo.tagName === 'TEXTAREA' ||
          alvo.tagName === 'SELECT' ||
          alvo.isContentEditable);

      if ((e.key === 'k' || e.key === 'K') && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        if (podeLancar) setLancarAberto(true);
        return;
      }
      if (
        !digitando &&
        (e.key === 'n' || e.key === 'N') &&
        !e.metaKey &&
        !e.ctrlKey &&
        !e.altKey
      ) {
        e.preventDefault();
        if (podeLancar) setLancarAberto(true);
      }
    }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [podeLancar]);

  return (
    <div className="max-w-[1200px] mx-auto">
      <header className="mb-7">
        <div className="eyebrow mb-3">Pessoal · Organizador financeiro</div>
        <h1 className="font-display font-semibold text-[38px] leading-[1.05] tracking-tighter text-ink m-0 mb-2.5">
          Finanças
        </h1>
        <p className="text-[15px] text-ink-soft max-w-[60ch] leading-relaxed m-0">
          Sua visão do mês: saldo das contas, o que entrou, o que saiu e quanto
          sobrou. Lance e organize tudo aqui pela web ou pelo Telegram (gasto,
          ganho e boleto por foto).
        </p>
      </header>

      {/* Atalhos pra pular entre as seções (fica grudado no topo ao rolar) */}
      <SecaoNav />

      {/* Navegação de mês */}
      <div id="sec-visao" className="scroll-mt-16 flex items-center gap-3 mb-5">
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

      {/* Relatório: série mês a mês + top categorias do período + CSV */}
      <RelatorioSection ano={ano} mes={mes} />

      {/* Contas + Reservas (com criar/editar/excluir) */}
      <div id="sec-contas" className="scroll-mt-16">
        <ContasSection
          contas={contas}
          loading={contasLoading}
          onChanged={refetchContas}
        />
      </div>

      {/* Transações: lista filtrável + lançar/excluir */}
      <div id="sec-transacoes" className="scroll-mt-16">
        <TransacoesSection
          ano={ano}
          mes={mes}
          contas={contas}
          onMutate={recarregarTudo}
          novoAberto={lancarAberto}
          onNovoAbertoChange={setLancarAberto}
        />
      </div>

      {/* Consumo (água/gás/luz) */}
      <section id="sec-consumo" className="scroll-mt-16 mb-8">
        <h2 className="font-display font-semibold text-lg tracking-tight text-ink m-0 mb-4">
          Consumo
        </h2>
        <ConsumoSection />
      </section>

      {/* Cartões (criar/editar/excluir) */}
      <div id="sec-cartoes" className="scroll-mt-16">
        <CartoesSection />
      </div>

      {/* Contas fixas (recorrências: criar/editar/excluir) */}
      <div id="sec-fixas" className="scroll-mt-16">
        <RecorrenciasSection contas={contas} onMutate={recarregarTudo} />
      </div>

      {/* Categorias (criar/editar/excluir) */}
      <div id="sec-categorias" className="scroll-mt-16">
        <CategoriasSection />
      </div>

      {/* Comprovantes */}
      <section id="sec-comprovantes" className="scroll-mt-16 mb-8">
        <h2 className="font-display font-semibold text-lg tracking-tight text-ink m-0 mb-4">
          Comprovantes
        </h2>
        <ComprovantesGaleria />
      </section>

      {/* Ferramenta de dev (some em produção) */}
      <DevSyncButton />

      {/* FAB: lançar de qualquer lugar (também por "N" ou Ctrl/Cmd+K) */}
      <button
        type="button"
        onClick={() => setLancarAberto(true)}
        disabled={!podeLancar}
        title={
          podeLancar
            ? 'Lançar despesa ou receita  ·  atalho: N ou Ctrl+K'
            : 'Crie uma conta antes de lançar'
        }
        aria-label="Lançar despesa ou receita"
        className="btn-primary fixed bottom-7 right-7 z-40 !p-0 w-14 h-14 justify-center !rounded-full shadow-brand disabled:opacity-40 disabled:pointer-events-none"
      >
        <IconPlus className="text-[22px]" />
      </button>
    </div>
  );
}

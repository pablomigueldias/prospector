import { useEffect, useMemo, useState } from 'react';

import { PagarModal, type PagamentoAlvo } from '@/components/PagarModal';
import { useCategorias, useTransacoes } from '@/hooks/useFinancas';
import { api } from '@/lib/api';
import { achatarCategorias } from '@/lib/categorias';
import { formatMesAno } from '@/lib/format';
import {
  ApiError,
  type Conta,
  type TransacaoFiltro,
  type TransacaoListItem,
} from '@/lib/types';

import { LancamentoForm } from './LancamentoForm';
import { TransacoesLista } from './TransacoesLista';
import { type LancamentoInicial } from './types';

interface Props {
  /** Mês "atual" selecionado no topo do dashboard (filtro padrão da lista). */
  ano: number;
  mes: number;
  contas: Conta[];
  /** Recarrega resumo/contas do dashboard após lançar ou excluir. */
  onMutate: () => void;
  /** Modal "novo lançamento" controlado de fora (FAB / atalho de teclado). */
  novoAberto: boolean;
  onNovoAbertoChange: (aberto: boolean) => void;
  /** Cada incremento força a lista a focar o mês do dashboard (ex.: clique
   *  num mês do gráfico do Relatório). */
  focarMesSinal?: number;
}

const FILTROS_KEY = 'financas:filtros-transacoes';

interface FiltrosSalvos {
  soEsteMes: boolean;
  tipo: '' | 'despesa' | 'receita';
  contaId: string;
  categoriaId: string;
  busca: string;
}

function carregarFiltros(): Partial<FiltrosSalvos> | null {
  if (typeof window === 'undefined') return null;
  try {
    const raw = window.localStorage.getItem(FILTROS_KEY);
    return raw ? (JSON.parse(raw) as Partial<FiltrosSalvos>) : null;
  } catch {
    return null;
  }
}

export function TransacoesSection({
  ano,
  mes,
  contas,
  onMutate,
  novoAberto,
  onNovoAbertoChange,
  focarMesSinal,
}: Props) {
  // Restaura os últimos filtros usados (uma vez, na montagem).
  const inicial = useMemo(carregarFiltros, []);
  const [soEsteMes, setSoEsteMes] = useState(inicial?.soEsteMes ?? true);
  const [tipo, setTipo] = useState<'' | 'despesa' | 'receita'>(
    inicial?.tipo ?? '',
  );
  const [contaId, setContaId] = useState(inicial?.contaId ?? '');
  const [categoriaId, setCategoriaId] = useState(inicial?.categoriaId ?? '');
  const [buscaInput, setBuscaInput] = useState(inicial?.busca ?? '');
  const [busca, setBusca] = useState(inicial?.busca ?? '');

  // Debounce da busca (evita um request por tecla).
  useEffect(() => {
    const t = setTimeout(() => setBusca(buscaInput.trim()), 400);
    return () => clearTimeout(t);
  }, [buscaInput]);

  // Clique num mês do gráfico do Relatório → garante que a lista mostre só o
  // mês do dashboard (ignora o filtro "todos os meses" que estivesse ligado).
  useEffect(() => {
    if (focarMesSinal) setSoEsteMes(true);
  }, [focarMesSinal]);

  // Lembra os filtros pra próxima visita.
  useEffect(() => {
    if (typeof window === 'undefined') return;
    try {
      window.localStorage.setItem(
        FILTROS_KEY,
        JSON.stringify({ soEsteMes, tipo, contaId, categoriaId, busca: buscaInput }),
      );
    } catch {
      /* localStorage indisponível (modo privado etc.) — ignora. */
    }
  }, [soEsteMes, tipo, contaId, categoriaId, buscaInput]);

  const { arvore } = useCategorias();
  const categoriasPlanas = useMemo(() => achatarCategorias(arvore), [arvore]);

  const filtro: TransacaoFiltro = useMemo(
    () => ({
      ano: soEsteMes ? ano : undefined,
      mes: soEsteMes ? mes : undefined,
      tipo: tipo || undefined,
      conta_id: contaId || undefined,
      categoria_id: categoriaId || undefined,
      busca: busca || undefined,
      limit: 100,
    }),
    [soEsteMes, ano, mes, tipo, contaId, categoriaId, busca],
  );

  const { transacoes, total, loading, refetch } = useTransacoes(filtro);

  const recarregar = () => {
    void refetch();
    onMutate();
  };

  // Edição: busca o detalhe (pra saber a conta) e abre o form pré-preenchido.
  const [editando, setEditando] = useState<LancamentoInicial | null>(null);
  const [carregandoEdicao, setCarregandoEdicao] = useState<string | null>(null);
  const [erroEdicao, setErroEdicao] = useState('');

  async function abrirEdicao(t: TransacaoListItem) {
    setErroEdicao('');
    setCarregandoEdicao(t.id);
    try {
      const det = await api.financasTransacao(t.id);
      setEditando({
        id: det.id,
        tipo: det.tipo === 'receita' ? 'receita' : 'despesa',
        descricao: det.descricao,
        valor: String(det.valor_total),
        contaId: det.pagamentos?.[0]?.conta_id ?? '',
        categoriaId: det.categoria_id ?? '',
        data: det.data_competencia,
        prevista: det.status !== 'paga',
      });
    } catch (err) {
      setErroEdicao(
        err instanceof ApiError ? err.message : 'Falha ao abrir a edição.',
      );
    } finally {
      setCarregandoEdicao(null);
    }
  }

  // Pagar: quita uma prevista/atrasada (move o saldo). Busca o detalhe pra
  // saber se já tem conta (boleto/recorrência nascem sem) e abre o modal.
  const [pagando, setPagando] = useState<PagamentoAlvo | null>(null);
  const [carregandoPagar, setCarregandoPagar] = useState<string | null>(null);

  async function abrirPagamento(t: TransacaoListItem) {
    setErroEdicao('');
    setCarregandoPagar(t.id);
    try {
      const det = await api.financasTransacao(t.id);
      const semConta = !det.pagamentos?.[0]?.conta_id;
      const sug = semConta
        ? await api.financasSugestaoConta(t.id).catch(() => null)
        : null;
      setPagando({
        id: det.id,
        descricao: det.descricao,
        valor: String(det.valor_total),
        contaIdAtual: det.pagamentos?.[0]?.conta_id ?? null,
        contaSugeridaId: sug?.conta_id ?? null,
        contaSugeridaNome: sug?.conta_nome ?? null,
        vencimento: det.data_vencimento ?? null,
        multaPct: det.multa_percentual ?? null,
        jurosPct: det.juros_mensal_percentual ?? null,
        descontoValor: det.desconto_valor ?? null,
        descontoAte: det.desconto_ate ?? null,
      });
    } catch (err) {
      setErroEdicao(
        err instanceof ApiError ? err.message : 'Falha ao abrir o pagamento.',
      );
    } finally {
      setCarregandoPagar(null);
    }
  }

  const algumFiltro =
    !soEsteMes || !!tipo || !!contaId || !!categoriaId || !!busca;

  function limparFiltros() {
    setSoEsteMes(true);
    setTipo('');
    setContaId('');
    setCategoriaId('');
    setBuscaInput('');
    setBusca('');
  }

  return (
    <section className="mb-8">
      <div className="flex items-center justify-between mb-4">
        <h2 className="font-display font-semibold text-lg tracking-tight text-ink m-0">
          Transações
        </h2>
        <button
          type="button"
          onClick={() => onNovoAbertoChange(true)}
          className="btn-primary px-4 py-1.5 text-sm"
          disabled={contas.length === 0}
          title={
            contas.length === 0
              ? 'Crie uma conta antes de lançar'
              : 'Lançar despesa ou receita'
          }
        >
          + Novo lançamento
        </button>
      </div>

      {/* Filtros */}
      <div className="card p-3 mb-3 flex flex-wrap items-center gap-2">
        <select
          className="input w-auto py-1.5 text-sm"
          value={soEsteMes ? 'mes' : 'todos'}
          onChange={(e) => setSoEsteMes(e.target.value === 'mes')}
        >
          <option value="mes">{formatMesAno(ano, mes)}</option>
          <option value="todos">Todos os meses</option>
        </select>

        <select
          className="input w-auto py-1.5 text-sm"
          value={tipo}
          onChange={(e) => setTipo(e.target.value as typeof tipo)}
        >
          <option value="">Tipo: todos</option>
          <option value="despesa">Despesas</option>
          <option value="receita">Receitas</option>
        </select>

        <select
          className="input w-auto py-1.5 text-sm"
          value={contaId}
          onChange={(e) => setContaId(e.target.value)}
        >
          <option value="">Conta: todas</option>
          {contas.map((c) => (
            <option key={c.id} value={c.id}>
              {c.nome}
            </option>
          ))}
        </select>

        <select
          className="input w-auto py-1.5 text-sm"
          value={categoriaId}
          onChange={(e) => setCategoriaId(e.target.value)}
        >
          <option value="">Categoria: todas</option>
          {categoriasPlanas.map((c) => (
            <option key={c.id} value={c.id}>
              {`${'  '.repeat(c.depth)}${c.nome}`}
            </option>
          ))}
        </select>

        <input
          className="input flex-1 min-w-[140px] py-1.5 text-sm"
          value={buscaInput}
          onChange={(e) => setBuscaInput(e.target.value)}
          placeholder="Buscar na descrição…"
        />

        {algumFiltro && (
          <button
            type="button"
            onClick={limparFiltros}
            className="text-sm text-ink-mute hover:text-ink px-2"
          >
            limpar
          </button>
        )}
      </div>

      {erroEdicao && (
        <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded px-3 py-2 mb-2">
          {erroEdicao}
        </div>
      )}

      <TransacoesLista
        transacoes={transacoes}
        loading={loading}
        total={total}
        onExcluiu={recarregar}
        onEditar={abrirEdicao}
        editandoId={carregandoEdicao}
        onPagar={abrirPagamento}
        pagandoId={carregandoPagar}
      />

      {pagando && (
        <PagarModal
          contas={contas}
          alvo={pagando}
          onClose={() => setPagando(null)}
          onPaid={() => {
            setPagando(null);
            recarregar();
          }}
        />
      )}

      {(novoAberto || editando) && (
        <LancamentoForm
          contas={contas}
          categorias={categoriasPlanas}
          inicial={editando ?? undefined}
          onClose={() => {
            setEditando(null);
            onNovoAbertoChange(false);
          }}
          onSaved={() => {
            setEditando(null);
            onNovoAbertoChange(false);
            recarregar();
          }}
        />
      )}
    </section>
  );
}

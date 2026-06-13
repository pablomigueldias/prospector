import { useEffect, useMemo, useState, type FormEvent } from 'react';

import { Modal } from '@/components/Modal';
import { PagarModal, type PagamentoAlvo } from '@/components/PagarModal';
import { useCategorias, useTransacoes } from '@/hooks/useFinancas';
import { api } from '@/lib/api';
import { achatarCategorias, type CategoriaPlana } from '@/lib/categorias';
import { formatBRL, formatMesAno } from '@/lib/format';
import {
  ApiError,
  type Conta,
  type TransacaoFiltro,
  type TransacaoListItem,
} from '@/lib/types';

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
}

function dataCurta(iso: string): string {
  // "2026-06-10" → "10/06"
  const [, m, d] = iso.split('-');
  return d && m ? `${d}/${m}` : iso;
}

/** Valores que pré-preenchem o LancamentoForm quando se edita uma transação. */
interface LancamentoInicial {
  id: string;
  tipo: 'despesa' | 'receita';
  descricao: string;
  valor: string;
  contaId: string;
  categoriaId: string;
  data: string;
  prevista: boolean;
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
      setPagando({
        id: det.id,
        descricao: det.descricao,
        valor: String(det.valor_total),
        contaIdAtual: det.pagamentos?.[0]?.conta_id ?? null,
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
              {`${'  '.repeat(c.depth)}${c.nome}`}
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

function TransacoesLista({
  transacoes,
  loading,
  total,
  onExcluiu,
  onEditar,
  editandoId,
  onPagar,
  pagandoId,
}: {
  transacoes: TransacaoListItem[];
  loading: boolean;
  total: number;
  onExcluiu: () => void;
  onEditar: (t: TransacaoListItem) => void;
  /** Id da transação cujo detalhe está carregando (pra abrir a edição). */
  editandoId: string | null;
  onPagar: (t: TransacaoListItem) => void;
  /** Id da transação cujo detalhe está carregando (pra abrir o pagamento). */
  pagandoId: string | null;
}) {
  const [excluindo, setExcluindo] = useState<string | null>(null);
  const [erro, setErro] = useState('');

  async function excluir(t: TransacaoListItem) {
    if (
      !window.confirm(
        `Excluir “${t.descricao}” (${formatBRL(t.valor_total)})? ` +
          'Se já estava paga, o saldo da conta volta.',
      )
    ) {
      return;
    }
    setErro('');
    setExcluindo(t.id);
    try {
      await api.financasExcluirTransacao(t.id);
      onExcluiu();
    } catch (err) {
      setErro(err instanceof ApiError ? err.message : 'Falha ao excluir.');
    } finally {
      setExcluindo(null);
    }
  }

  if (loading) {
    return (
      <div className="space-y-2">
        {[0, 1, 2].map((i) => (
          <div key={i} className="card p-4 h-[58px] animate-pulse" />
        ))}
      </div>
    );
  }

  if (transacoes.length === 0) {
    return (
      <div className="card p-6 text-center text-ink-soft text-sm">
        Nenhuma transação com esses filtros.
      </div>
    );
  }

  return (
    <>
      {erro && (
        <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded px-3 py-2 mb-2">
          {erro}
        </div>
      )}
      <div className="card divide-y divide-line">
        {transacoes.map((t) => {
          const despesa = t.tipo === 'despesa';
          return (
            <div
              key={t.id}
              className="flex items-center gap-3 px-4 py-2.5 group"
            >
              <div className="w-12 shrink-0 font-mono text-[11px] text-ink-mute">
                {dataCurta(t.data_competencia)}
              </div>
              <div className="min-w-0 flex-1">
                <div className="text-sm text-ink truncate">
                  {t.descricao}
                  {t.status !== 'paga' && (
                    <span className="ml-2 text-[10px] uppercase tracking-wide text-ink-mute border border-line rounded px-1 py-0.5">
                      {t.status}
                    </span>
                  )}
                </div>
                <div className="text-[11.5px] text-ink-mute truncate">
                  {[t.categoria_nome, ...(t.contas ?? [])]
                    .filter(Boolean)
                    .join(' · ') || 'sem categoria'}
                </div>
              </div>
              <div
                className={`shrink-0 font-display font-semibold tracking-tight text-sm ${
                  despesa ? 'text-ink' : 'text-success'
                }`}
              >
                {despesa ? '−' : '+'}
                {formatBRL(t.valor_total)}
              </div>
              {/* Pagar: quita a prevista/atrasada e move o saldo. */}
              {t.status !== 'paga' && (
                <button
                  type="button"
                  onClick={() => onPagar(t)}
                  disabled={pagandoId === t.id}
                  className="shrink-0 text-[11px] font-medium text-success border border-success-soft hover:bg-success-soft rounded-pill px-2.5 py-1 transition-colors disabled:opacity-50"
                  title="Marcar como paga (move o saldo)"
                  aria-label="Pagar transação"
                >
                  {pagandoId === t.id ? '…' : '✓ Pagar'}
                </button>
              )}
              {/* Editar só faz sentido pra transação de uma conta (sem split). */}
              {(t.contas?.length ?? 0) <= 1 && (
                <button
                  type="button"
                  onClick={() => onEditar(t)}
                  disabled={editandoId === t.id}
                  className="shrink-0 text-ink-faint hover:text-brand text-sm px-1 opacity-0 group-hover:opacity-100 transition-opacity disabled:opacity-50"
                  title="Editar"
                  aria-label="Editar transação"
                >
                  {editandoId === t.id ? '…' : '✎'}
                </button>
              )}
              <button
                type="button"
                onClick={() => excluir(t)}
                disabled={excluindo === t.id}
                className="shrink-0 text-ink-faint hover:text-red-600 text-sm px-1 opacity-0 group-hover:opacity-100 transition-opacity disabled:opacity-50"
                title="Excluir"
                aria-label="Excluir transação"
              >
                ✕
              </button>
            </div>
          );
        })}
      </div>
      <div className="text-[12px] text-ink-mute mt-2">
        {total} {total === 1 ? 'transação' : 'transações'}
      </div>
    </>
  );
}

function LancamentoForm({
  contas,
  categorias,
  inicial,
  onClose,
  onSaved,
}: {
  contas: Conta[];
  categorias: CategoriaPlana[];
  /** Quando presente, o form abre em modo EDIÇÃO (PATCH em vez de lançar). */
  inicial?: LancamentoInicial;
  onClose: () => void;
  onSaved: () => void;
}) {
  const editando = !!inicial;
  const hojeIso = new Date().toISOString().slice(0, 10);
  const [tipo, setTipo] = useState<'despesa' | 'receita'>(
    inicial?.tipo ?? 'despesa',
  );
  const [descricao, setDescricao] = useState(inicial?.descricao ?? '');
  const [valor, setValor] = useState(inicial?.valor ?? '');
  const [contaId, setContaId] = useState(inicial?.contaId ?? contas[0]?.id ?? '');
  const [categoriaId, setCategoriaId] = useState(inicial?.categoriaId ?? '');
  const [data, setData] = useState(inicial?.data ?? hojeIso);
  const [prevista, setPrevista] = useState(inicial?.prevista ?? false);
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState('');

  async function salvar(e: FormEvent) {
    e.preventDefault();
    setErro('');
    if (!descricao.trim()) return setErro('Descreva o lançamento.');
    if (!contaId) return setErro('Escolha a conta.');
    const valorNum = Number(valor.replace(',', '.'));
    if (!Number.isFinite(valorNum) || valorNum <= 0) {
      return setErro('Informe um valor maior que zero.');
    }

    const body = {
      descricao: descricao.trim(),
      valor_total: String(valorNum),
      conta_id: contaId,
      categoria_id: categoriaId || null,
      data_competencia: data || null,
      status: prevista ? ('prevista' as const) : ('paga' as const),
    };

    setSalvando(true);
    try {
      if (inicial) {
        await api.financasEditarTransacao(inicial.id, { tipo, ...body });
      } else if (tipo === 'despesa') {
        await api.financasLancarDespesa(body);
      } else {
        await api.financasLancarReceita(body);
      }
      onSaved();
    } catch (err) {
      const acao = editando ? 'salvar' : 'lançar';
      setErro(err instanceof ApiError ? err.message : `Falha ao ${acao}.`);
    } finally {
      setSalvando(false);
    }
  }

  return (
    <Modal open onClose={onClose} title={editando ? 'Editar lançamento' : 'Novo lançamento'}>
      <form onSubmit={salvar} className="space-y-4">
        {/* Toggle despesa / receita */}
        <div className="grid grid-cols-2 gap-2">
          {(['despesa', 'receita'] as const).map((t) => (
            <button
              key={t}
              type="button"
              onClick={() => setTipo(t)}
              className={`py-2 rounded-lg border text-sm font-medium transition-colors ${
                tipo === t
                  ? 'border-brand bg-brand-soft text-brand-ink'
                  : 'border-line text-ink-soft hover:border-ink-mute'
              }`}
            >
              {t === 'despesa' ? 'Despesa' : 'Receita'}
            </button>
          ))}
        </div>

        <div>
          <label className="block text-[13px] font-medium text-ink-soft mb-1.5">
            Descrição
          </label>
          <input
            className="input"
            value={descricao}
            onChange={(e) => setDescricao(e.target.value)}
            placeholder={tipo === 'despesa' ? 'ex: Mercado' : 'ex: Salário'}
            autoFocus
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-[13px] font-medium text-ink-soft mb-1.5">
              Valor
            </label>
            <input
              className="input"
              value={valor}
              onChange={(e) => setValor(e.target.value)}
              inputMode="decimal"
              placeholder="0,00"
            />
          </div>
          <div>
            <label className="block text-[13px] font-medium text-ink-soft mb-1.5">
              Data
            </label>
            <input
              type="date"
              className="input"
              value={data}
              onChange={(e) => setData(e.target.value)}
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-[13px] font-medium text-ink-soft mb-1.5">
              {tipo === 'despesa' ? 'Conta (saiu de)' : 'Conta (entrou em)'}
            </label>
            <select
              className="input"
              value={contaId}
              onChange={(e) => setContaId(e.target.value)}
            >
              {contas.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.nome}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-[13px] font-medium text-ink-soft mb-1.5">
              Categoria
            </label>
            <select
              className="input"
              value={categoriaId}
              onChange={(e) => setCategoriaId(e.target.value)}
            >
              <option value="">Sem categoria</option>
              {categorias.map((c) => (
                <option key={c.id} value={c.id}>
                  {`${'  '.repeat(c.depth)}${c.nome}`}
                </option>
              ))}
            </select>
          </div>
        </div>

        <label className="flex items-center gap-2 text-sm text-ink-soft">
          <input
            type="checkbox"
            checked={prevista}
            onChange={(e) => setPrevista(e.target.checked)}
          />
          Lançar como prevista (não mexe no saldo ainda)
        </label>

        {erro && (
          <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded px-3 py-2">
            {erro}
          </div>
        )}

        <div className="flex items-center justify-end gap-2 pt-1">
          <button
            type="button"
            onClick={onClose}
            className="btn-ghost px-4 py-2 text-sm"
          >
            Cancelar
          </button>
          <button
            type="submit"
            disabled={salvando}
            className="btn-primary px-5 py-2 text-sm disabled:opacity-50"
          >
            {salvando
              ? editando
                ? 'Salvando…'
                : 'Lançando…'
              : editando
                ? 'Salvar'
                : 'Lançar'}
          </button>
        </div>
      </form>
    </Modal>
  );
}

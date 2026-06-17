import { useMemo, useState, type FormEvent } from 'react';

import { Modal } from '@/components/shared/Modal';
import { useFetch } from '@/hooks/useFetch';
import { useCategorias } from '@/hooks/useFinancas';
import { api } from '@/lib/api';
import { achatarCategorias } from '@/lib/categorias';
import { formatBRL } from '@/lib/format';
import {
  ApiError,
  type OrcamentoStatusItem,
  type OrcamentoStatusResponse,
} from '@/lib/types';

/**
 * Orçamentos por categoria: teto mensal × consumido do mês, com barra de
 * progresso (verde→laranja→vermelho), e CRUD por modal.
 */
export function OrcamentosSection({
  ano,
  mes,
  onMutate,
}: {
  ano: number;
  mes: number;
  onMutate?: () => void;
}) {
  const competencia = `${ano}-${String(mes).padStart(2, '0')}`;
  const { data, loading, refetch } = useFetch<OrcamentoStatusResponse>(
    () => api.financasOrcamentosStatus(competencia),
    [competencia],
  );
  const [modal, setModal] = useState<
    { modo: 'fechado' } | { modo: 'novo' } | { modo: 'editar'; item: OrcamentoStatusItem }
  >({ modo: 'fechado' });

  const itens = data?.items ?? [];
  const orcado = Number(data?.total_orcado ?? 0);
  const consumido = Number(data?.total_consumido ?? 0);

  function recarregar() {
    void refetch();
    onMutate?.();
  }

  return (
    <section className="mb-8">
      <div className="flex items-center justify-between mb-4">
        <h2 className="font-display font-semibold text-lg tracking-tight text-ink m-0">
          Orçamentos
        </h2>
        <div className="flex items-center gap-3">
          {orcado > 0 && (
            <span className="text-[12.5px] text-ink-mute">
              {formatBRL(consumido)} de {formatBRL(orcado)}
            </span>
          )}
          <button
            type="button"
            onClick={() => setModal({ modo: 'novo' })}
            className="btn-ghost px-3.5 py-1.5 text-sm"
          >
            + Novo orçamento
          </button>
        </div>
      </div>

      {loading ? (
        <div className="card p-4 h-[100px] animate-pulse" />
      ) : itens.length === 0 ? (
        <div className="card p-6 text-center text-ink-soft text-sm">
          Nenhum teto definido. Crie um orçamento (ex.: R$800 em Mercado) e
          acompanhe quanto já gastou no mês.
        </div>
      ) : (
        <div className="card divide-y divide-line">
          {itens.map((it) => (
            <OrcamentoRow
              key={it.orcamento_id}
              item={it}
              onEditar={() => setModal({ modo: 'editar', item: it })}
            />
          ))}
        </div>
      )}

      {modal.modo !== 'fechado' && (
        <OrcamentoForm
          item={modal.modo === 'editar' ? modal.item : null}
          onClose={() => setModal({ modo: 'fechado' })}
          onSaved={() => {
            setModal({ modo: 'fechado' });
            recarregar();
          }}
        />
      )}
    </section>
  );
}

function OrcamentoRow({
  item,
  onEditar,
}: {
  item: OrcamentoStatusItem;
  onEditar: () => void;
}) {
  const pct = item.percentual;
  const cor = pct >= 100 ? 'bg-red-500' : pct >= 80 ? 'bg-brand-deep' : 'bg-brand';
  const restante = Number(item.restante);

  return (
    <button
      type="button"
      onClick={onEditar}
      className="w-full text-left px-4 py-3 hover:bg-bg-alt/40 transition-colors group"
      title="Editar / remover"
    >
      <div className="flex items-baseline justify-between mb-1.5">
        <span className="text-sm text-ink">
          {item.categoria_nome ?? 'Categoria'}
        </span>
        <span className="text-sm tabular-nums text-ink-soft">
          {formatBRL(item.consumido)}{' '}
          <span className="text-ink-mute">/ {formatBRL(item.valor_mensal)}</span>
        </span>
      </div>
      <div className="h-1.5 rounded-full bg-line-soft overflow-hidden">
        <div
          className={`h-full rounded-full ${cor}`}
          style={{ width: `${Math.min(100, pct)}%` }}
        />
      </div>
      <div className="flex items-center justify-between mt-1">
        <span
          className={`font-mono uppercase tracking-[0.1em] text-[9px] ${
            restante < 0 ? 'text-red-600' : 'text-ink-mute'
          }`}
        >
          {restante < 0
            ? `estourou ${formatBRL(Math.abs(restante))}`
            : `restam ${formatBRL(restante)}`}{' '}
          · {Math.round(pct)}%
        </span>
        <span className="text-[11px] text-ink-faint opacity-0 group-hover:opacity-100 transition-opacity">
          editar
        </span>
      </div>
    </button>
  );
}

function OrcamentoForm({
  item,
  onClose,
  onSaved,
}: {
  item: OrcamentoStatusItem | null;
  onClose: () => void;
  onSaved: () => void;
}) {
  const editando = item !== null;
  const { arvore } = useCategorias();
  const categorias = useMemo(() => achatarCategorias(arvore), [arvore]);

  const [categoriaId, setCategoriaId] = useState(item?.categoria_id ?? '');
  const [valor, setValor] = useState(item ? String(item.valor_mensal) : '');
  const [salvando, setSalvando] = useState(false);
  const [excluindo, setExcluindo] = useState(false);
  const [erro, setErro] = useState('');

  async function salvar(e: FormEvent) {
    e.preventDefault();
    setErro('');
    if (!editando && !categoriaId) return setErro('Escolha a categoria.');
    const valorNum = Number(valor.replace(',', '.'));
    if (!Number.isFinite(valorNum) || valorNum <= 0) {
      return setErro('Informe um teto maior que zero.');
    }
    setSalvando(true);
    try {
      if (editando && item) {
        await api.financasAtualizarOrcamento(item.orcamento_id, {
          valor_mensal: String(valorNum),
        });
      } else {
        await api.financasCriarOrcamento({
          categoria_id: categoriaId,
          valor_mensal: String(valorNum),
        });
      }
      onSaved();
    } catch (err) {
      setErro(err instanceof ApiError ? err.message : 'Falha ao salvar.');
    } finally {
      setSalvando(false);
    }
  }

  async function excluir() {
    if (!item) return;
    if (!window.confirm(`Remover o orçamento de “${item.categoria_nome}”?`)) return;
    setErro('');
    setExcluindo(true);
    try {
      await api.financasExcluirOrcamento(item.orcamento_id);
      onSaved();
    } catch (err) {
      setErro(err instanceof ApiError ? err.message : 'Falha ao excluir.');
      setExcluindo(false);
    }
  }

  return (
    <Modal open onClose={onClose} title={editando ? 'Editar orçamento' : 'Novo orçamento'}>
      <form onSubmit={salvar} className="space-y-4">
        <div>
          <label className="block text-[13px] font-medium text-ink-soft mb-1.5">
            Categoria
          </label>
          {editando ? (
            <div className="input flex items-center text-ink-soft">
              {item?.categoria_nome}
            </div>
          ) : (
            <select
              className="input"
              value={categoriaId}
              onChange={(e) => setCategoriaId(e.target.value)}
              autoFocus
            >
              <option value="">Escolha…</option>
              {categorias.map((c) => (
                <option key={c.id} value={c.id}>
                  {`${'  '.repeat(c.depth)}${c.nome}`}
                </option>
              ))}
            </select>
          )}
        </div>

        <div>
          <label className="block text-[13px] font-medium text-ink-soft mb-1.5">
            Teto mensal
          </label>
          <input
            className="input"
            value={valor}
            onChange={(e) => setValor(e.target.value)}
            inputMode="decimal"
            placeholder="0,00"
          />
        </div>

        {erro && (
          <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded px-3 py-2">
            {erro}
          </div>
        )}

        <div className="flex items-center justify-between gap-3 pt-1">
          {editando ? (
            <button
              type="button"
              onClick={excluir}
              disabled={salvando || excluindo}
              className="text-sm text-red-600 hover:underline disabled:opacity-50"
            >
              {excluindo ? 'Excluindo…' : 'Excluir'}
            </button>
          ) : (
            <span />
          )}
          <div className="flex items-center gap-2">
            <button type="button" onClick={onClose} className="btn-ghost px-4 py-2 text-sm">
              Cancelar
            </button>
            <button
              type="submit"
              disabled={salvando || excluindo}
              className="btn-primary px-5 py-2 text-sm disabled:opacity-50"
            >
              {salvando ? 'Salvando…' : editando ? 'Salvar' : 'Criar'}
            </button>
          </div>
        </div>
      </form>
    </Modal>
  );
}

import { useMemo, useState, type FormEvent } from 'react';

import { SidePanel } from '@/components/shared/SidePanel';
import { useCategorias } from '@/hooks/useFinancas';
import { api } from '@/lib/api';
import { achatarCategorias, type CategoriaPlana } from '@/lib/categorias';
import { ApiError, type CategoriaTreeItem } from '@/lib/types';

type ModalState =
  | { modo: 'fechado' }
  | { modo: 'nova'; paiId: string | null }
  | { modo: 'editar'; cat: CategoriaPlana };

export function CategoriasSection() {
  const { arvore, loading, refetch } = useCategorias();
  const [modal, setModal] = useState<ModalState>({ modo: 'fechado' });

  const planas = useMemo(() => achatarCategorias(arvore), [arvore]);

  return (
    <section className="mb-8">
      <div className="flex items-center justify-between mb-4">
        <h2 className="font-display font-semibold text-lg tracking-tight text-ink m-0">
          Categorias
        </h2>
        <button
          type="button"
          onClick={() => setModal({ modo: 'nova', paiId: null })}
          className="btn-ghost px-3.5 py-1.5 text-sm"
        >
          + Nova categoria
        </button>
      </div>

      {loading ? (
        <div className="card p-4 h-[120px] animate-pulse" />
      ) : arvore.length === 0 ? (
        <div className="card p-6 text-center text-ink-soft text-sm">
          Nenhuma categoria. Clique em “Nova categoria” pra começar.
        </div>
      ) : (
        <div className="card divide-y divide-line">
          {arvore.map((c) => (
            <Arvore
              key={c.id}
              cat={c}
              depth={0}
              onEditar={(p) => setModal({ modo: 'editar', cat: p })}
              onAdicionarFilho={(paiId) => setModal({ modo: 'nova', paiId })}
            />
          ))}
        </div>
      )}

      {modal.modo !== 'fechado' && (
        <CategoriaForm
          modo={modal.modo}
          paiInicial={modal.modo === 'nova' ? modal.paiId : null}
          cat={modal.modo === 'editar' ? modal.cat : null}
          opcoes={planas}
          onClose={() => setModal({ modo: 'fechado' })}
          onSaved={() => {
            setModal({ modo: 'fechado' });
            void refetch();
          }}
        />
      )}
    </section>
  );
}

function Arvore({
  cat,
  depth,
  onEditar,
  onAdicionarFilho,
}: {
  cat: CategoriaTreeItem;
  depth: number;
  onEditar: (c: CategoriaPlana) => void;
  onAdicionarFilho: (paiId: string) => void;
}) {
  return (
    <>
      <div className="flex items-center gap-2 px-4 py-2 group">
        <div
          className="flex-1 text-sm text-ink truncate"
          style={{ paddingLeft: depth * 18 }}
        >
          {depth > 0 && <span className="text-ink-faint mr-1.5">└</span>}
          {cat.nome}
          {!cat.ativa && (
            <span className="ml-2 text-[10px] uppercase tracking-wide text-ink-mute">
              inativa
            </span>
          )}
        </div>
        <div className="flex items-center gap-3 opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            type="button"
            onClick={() => onAdicionarFilho(cat.id)}
            className="text-[12px] text-ink-mute hover:text-ink"
            title="Adicionar subcategoria"
          >
            + sub
          </button>
          <button
            type="button"
            onClick={() =>
              onEditar({ id: cat.id, nome: cat.nome, depth })
            }
            className="text-[12px] text-ink-mute hover:text-ink"
          >
            editar
          </button>
        </div>
      </div>
      {cat.filhos?.map((f) => (
        <Arvore
          key={f.id}
          cat={f}
          depth={depth + 1}
          onEditar={onEditar}
          onAdicionarFilho={onAdicionarFilho}
        />
      ))}
    </>
  );
}

function CategoriaForm({
  modo,
  paiInicial,
  cat,
  opcoes,
  onClose,
  onSaved,
}: {
  modo: 'nova' | 'editar';
  paiInicial: string | null;
  cat: CategoriaPlana | null;
  opcoes: CategoriaPlana[];
  onClose: () => void;
  onSaved: () => void;
}) {
  const editando = modo === 'editar';
  const [nome, setNome] = useState(cat?.nome ?? '');
  const [paiId, setPaiId] = useState<string>(paiInicial ?? '');
  const [salvando, setSalvando] = useState(false);
  const [excluindo, setExcluindo] = useState(false);
  const [erro, setErro] = useState('');

  // Na edição, não dá pra ser pai de si mesmo (evita ciclo simples).
  const opcoesPai = opcoes.filter((o) => o.id !== cat?.id);

  async function salvar(e: FormEvent) {
    e.preventDefault();
    setErro('');
    if (!nome.trim()) return setErro('Dê um nome pra categoria.');
    setSalvando(true);
    try {
      if (editando && cat) {
        await api.financasAtualizarCategoria(cat.id, {
          nome: nome.trim(),
          categoria_pai_id: paiId || null,
        });
      } else {
        await api.financasCriarCategoria({
          nome: nome.trim(),
          categoria_pai_id: paiId || null,
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
    if (!cat) return;
    if (
      !window.confirm(
        `Excluir a categoria “${cat.nome}”? Transações nela ficam sem categoria.`,
      )
    ) {
      return;
    }
    setErro('');
    setExcluindo(true);
    try {
      await api.financasExcluirCategoria(cat.id);
      onSaved();
    } catch (err) {
      setErro(err instanceof ApiError ? err.message : 'Falha ao excluir.');
      setExcluindo(false);
    }
  }

  return (
    <SidePanel
      open
      onClose={onClose}
      title={editando ? 'Editar categoria' : 'Nova categoria'}
    >
      <form onSubmit={salvar} className="space-y-4">
        <div>
          <label className="block text-[13px] font-medium text-ink-soft mb-1.5">
            Nome
          </label>
          <input
            className="input"
            value={nome}
            onChange={(e) => setNome(e.target.value)}
            placeholder="ex: Mercado, Transporte, Lazer"
            autoFocus
          />
        </div>

        <div>
          <label className="block text-[13px] font-medium text-ink-soft mb-1.5">
            Categoria pai
          </label>
          <select
            className="input"
            value={paiId}
            onChange={(e) => setPaiId(e.target.value)}
          >
            <option value="">Nenhuma (categoria raiz)</option>
            {opcoesPai.map((o) => (
              <option key={o.id} value={o.id}>
                {`${'  '.repeat(o.depth)}${o.nome}`}
              </option>
            ))}
          </select>
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
            <button
              type="button"
              onClick={onClose}
              className="btn-ghost px-4 py-2 text-sm"
            >
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
    </SidePanel>
  );
}

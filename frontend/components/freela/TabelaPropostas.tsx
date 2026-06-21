import { useMemo, useState } from 'react';

import { formatBRL } from '@/lib/format';
import { FREELA_STATUS, type FreelaKanbanColuna, type FreelaKanbanItem, type FreelaStatus } from '@/lib/types';

const STATUS_LABEL: Record<FreelaStatus, string> = {
  rascunho: 'Rascunho',
  enviada: 'Enviada',
  visualizada: 'Visualizada',
  respondida: 'Respondida',
  negociando: 'Negociando',
  fechada: 'Fechada',
  perdida: 'Perdida',
};

// ── Tabela de propostas (com filtro por status + busca) ───────────

export function TabelaPropostas({
  colunas,
  loading,
  onAbrir,
  onMover,
  onRemover,
}: {
  colunas: FreelaKanbanColuna[];
  loading: boolean;
  onAbrir: (item: FreelaKanbanItem) => void;
  onMover: (id: string, status: FreelaStatus) => void;
  onRemover: (id: string) => void;
}) {
  const [filtroStatus, setFiltroStatus] = useState<FreelaStatus | 'todos'>('todos');
  const [busca, setBusca] = useState('');

  const itens = useMemo(() => colunas.flatMap((c) => c.items), [colunas]);
  const filtrados = useMemo(() => {
    const q = busca.trim().toLowerCase();
    return itens.filter((it) => {
      if (filtroStatus !== 'todos' && it.status !== filtroStatus) return false;
      if (!q) return true;
      return (
        it.projeto_titulo.toLowerCase().includes(q) ||
        (it.cliente_nome ?? '').toLowerCase().includes(q)
      );
    });
  }, [itens, filtroStatus, busca]);

  if (loading) {
    return <div className="card p-6 text-sm text-ink-mute">Carregando…</div>;
  }
  if (itens.length === 0) {
    return (
      <div className="card p-6 text-center text-sm text-ink-mute">
        Nenhuma proposta ainda. Crie uma a partir de um projeto na fila.
      </div>
    );
  }

  return (
    <div>
      {/* filtros */}
      <div className="flex flex-wrap items-center gap-2 mb-3">
        <input
          className="input py-1.5 text-[13px] w-56"
          placeholder="Buscar por projeto ou cliente…"
          value={busca}
          onChange={(e) => setBusca(e.target.value)}
        />
        <select
          className="input py-1.5 text-[13px] w-44"
          value={filtroStatus}
          onChange={(e) => setFiltroStatus(e.target.value as FreelaStatus | 'todos')}
        >
          <option value="todos">Todos os status</option>
          {FREELA_STATUS.map((s) => (
            <option key={s} value={s}>
              {STATUS_LABEL[s]}
            </option>
          ))}
        </select>
        <span className="text-[12px] text-ink-mute">
          {filtrados.length} de {itens.length}
        </span>
      </div>

      <div className="card overflow-x-auto p-0">
        <table className="w-full border-collapse text-[13px]">
          <thead>
            <tr className="border-b border-line text-left text-ink-mute">
              <th className="font-medium px-4 py-2.5">Projeto</th>
              <th className="font-medium px-4 py-2.5">Cliente</th>
              <th className="font-medium px-4 py-2.5 text-right">Valor</th>
              <th className="font-medium px-4 py-2.5 text-right">Líquido</th>
              <th className="font-medium px-4 py-2.5">Status</th>
              <th className="font-medium px-4 py-2.5 text-right">Dias</th>
              <th className="font-medium px-4 py-2.5 text-right">Ações</th>
            </tr>
          </thead>
          <tbody>
            {filtrados.map((it) => (
              <tr
                key={it.id}
                onClick={() => onAbrir(it)}
                className="border-b border-line/60 last:border-0 hover:bg-bg-alt cursor-pointer"
              >
                <td className="px-4 py-2.5 font-medium text-ink">{it.projeto_titulo}</td>
                <td className="px-4 py-2.5 text-ink-soft">{it.cliente_nome ?? '—'}</td>
                <td className="px-4 py-2.5 text-right text-ink-soft">
                  {it.valor_cotado != null ? formatBRL(it.valor_cotado) : '—'}
                </td>
                <td className="px-4 py-2.5 text-right text-ink-soft">
                  {it.valor_liquido_estimado != null ? formatBRL(it.valor_liquido_estimado) : '—'}
                </td>
                <td className="px-4 py-2.5" onClick={(ev) => ev.stopPropagation()}>
                  <select
                    className="input text-[12px] py-1"
                    value={it.status}
                    onChange={(e) => onMover(it.id, e.target.value as FreelaStatus)}
                  >
                    {FREELA_STATUS.map((s) => (
                      <option key={s} value={s}>
                        {STATUS_LABEL[s]}
                      </option>
                    ))}
                  </select>
                </td>
                <td className="px-4 py-2.5 text-right text-ink-faint">
                  {it.dias_desde_envio != null ? `${it.dias_desde_envio}d` : '—'}
                </td>
                <td className="px-4 py-2.5 text-right whitespace-nowrap">
                  <button
                    type="button"
                    className="text-ink-mute hover:text-red-600 text-[12px]"
                    onClick={(ev) => {
                      ev.stopPropagation();
                      onRemover(it.id);
                    }}
                  >
                    excluir
                  </button>
                </td>
              </tr>
            ))}
            {filtrados.length === 0 && (
              <tr>
                <td colSpan={7} className="px-4 py-6 text-center text-ink-mute">
                  Nenhuma proposta com esse filtro.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

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

// ── Kanban ────────────────────────────────────────────────────────

export function Kanban({
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
  if (loading) {
    return <div className="card p-6 text-sm text-ink-mute">Carregando board…</div>;
  }
  const total = colunas.reduce((acc, c) => acc + c.items.length, 0);
  if (total === 0) {
    return (
      <div className="card p-6 text-center text-sm text-ink-mute">
        Nenhuma proposta ainda. Crie uma a partir de um projeto na fila.
      </div>
    );
  }
  return (
    <div className="flex gap-3 overflow-x-auto pb-2">
      {colunas.map((col) => (
        <div key={col.status} className="min-w-[230px] w-[230px] shrink-0">
          <div className="flex items-center justify-between mb-2 px-1">
            <span className="text-[13px] font-medium text-ink-soft">
              {STATUS_LABEL[col.status]}
            </span>
            <span className="text-[12px] text-ink-faint">{col.items.length}</span>
          </div>
          <div className="flex flex-col gap-2">
            {col.items.map((it) => (
              <div key={it.id} className="card p-3">
                <button
                  type="button"
                  className="text-[13px] font-medium text-ink truncate text-left w-full hover:text-brand"
                  title="Abrir proposta"
                  onClick={() => onAbrir(it)}
                >
                  {it.projeto_titulo}
                </button>
                {it.cliente_nome && (
                  <div className="text-[11px] text-ink-mute truncate">{it.cliente_nome}</div>
                )}
                <div className="mt-1.5 flex items-center justify-between text-[12px]">
                  <span className="text-ink-soft">
                    {it.valor_cotado != null ? formatBRL(it.valor_cotado) : '—'}
                  </span>
                  {it.dias_desde_envio != null && (
                    <span className="text-ink-faint">{it.dias_desde_envio}d</span>
                  )}
                </div>
                <div className="mt-2 flex items-center gap-1.5">
                  <select
                    className="input text-[12px] py-1 flex-1"
                    value={it.status}
                    onChange={(e) => onMover(it.id, e.target.value as FreelaStatus)}
                  >
                    {FREELA_STATUS.map((s) => (
                      <option key={s} value={s}>
                        {STATUS_LABEL[s]}
                      </option>
                    ))}
                  </select>
                  <button
                    type="button"
                    className="text-ink-faint hover:text-red-500 text-sm px-1"
                    title="Remover"
                    onClick={() => onRemover(it.id)}
                  >
                    ✕
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}


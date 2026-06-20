import { useEffect, useState } from 'react';

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

// ── Kanban (com drag-and-drop entre colunas) ──────────────────────

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
  const [arrastando, setArrastando] = useState<string | null>(null);
  const [hover, setHover] = useState<FreelaStatus | null>(null);
  // Move otimista: aplica na hora; some quando os dados reais chegam.
  const [override, setOverride] = useState<Record<string, FreelaStatus>>({});
  useEffect(() => setOverride({}), [colunas]);

  if (loading) {
    return <div className="card p-6 text-sm text-ink-mute">Carregando board…</div>;
  }

  const itens = colunas.flatMap((c) => c.items);
  if (itens.length === 0) {
    return (
      <div className="card p-6 text-center text-sm text-ink-mute">
        Nenhuma proposta ainda. Crie uma a partir de um projeto na fila.
      </div>
    );
  }

  const statusDe = (it: FreelaKanbanItem): FreelaStatus => override[it.id] ?? it.status;
  const porStatus = (s: FreelaStatus) => itens.filter((it) => statusDe(it) === s);

  function soltar(status: FreelaStatus) {
    const id = arrastando;
    setArrastando(null);
    setHover(null);
    if (!id) return;
    const it = itens.find((x) => x.id === id);
    if (!it || statusDe(it) === status) return;
    // 'perdida' pede motivo (dialog no pai) — não faz move otimista.
    if (status !== 'perdida') setOverride((o) => ({ ...o, [id]: status }));
    onMover(id, status);
  }

  return (
    <div className="flex gap-3 overflow-x-auto pb-2">
      {FREELA_STATUS.map((status) => {
        const items = porStatus(status);
        return (
          <section
            key={status}
            onDragOver={(e) => {
              e.preventDefault();
              setHover(status);
            }}
            onDragLeave={() => setHover((h) => (h === status ? null : h))}
            onDrop={() => soltar(status)}
            className={`min-w-[230px] w-[230px] shrink-0 rounded-lg p-1 transition-colors ${
              hover === status ? 'bg-brand-soft/40' : ''
            }`}
          >
            <div className="flex items-center justify-between mb-2 px-1">
              <span className="text-[13px] font-medium text-ink-soft">
                {STATUS_LABEL[status]}
              </span>
              <span className="text-[12px] text-ink-faint">{items.length}</span>
            </div>
            <div className="flex flex-col gap-2 min-h-[60px]">
              {items.map((it) => (
                <div
                  key={it.id}
                  draggable
                  onDragStart={() => setArrastando(it.id)}
                  onDragEnd={() => setArrastando(null)}
                  className={`card p-3 cursor-grab active:cursor-grabbing ${
                    arrastando === it.id ? 'opacity-40' : ''
                  }`}
                >
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
                      value={statusDe(it)}
                      onChange={(e) => onMover(it.id, e.target.value as FreelaStatus)}
                      title="Mudar status (ou arraste o card)"
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
          </section>
        );
      })}
    </div>
  );
}

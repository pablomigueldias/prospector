import { type VagaListItem } from '@/lib/types';
import { MatchPill, StatusBadge } from './_shared';

// ── Lista (master) ────────────────────────────────────────────────

export function ListaVagas({
  items,
  loading,
  selecionada,
  onSelecionar,
}: {
  items: VagaListItem[];
  loading: boolean;
  selecionada: string | null;
  onSelecionar: (id: string) => void;
}) {
  if (loading) {
    return (
      <div className="flex flex-col gap-2">
        {[0, 1, 2].map((i) => (
          <div key={i} className="card p-4 h-[72px] animate-pulse" />
        ))}
      </div>
    );
  }
  if (items.length === 0) {
    return (
      <div className="card p-6 text-center text-sm text-ink-mute">
        Nenhuma vaga ainda. Clique em &quot;Nova vaga&quot;.
      </div>
    );
  }
  return (
    <div className="flex flex-col gap-2">
      {items.map((v) => {
        const ativa = v.id === selecionada;
        return (
          <button
            key={v.id}
            type="button"
            onClick={() => onSelecionar(v.id)}
            className={[
              'card p-3.5 text-left transition-colors',
              ativa ? 'border-brand ring-1 ring-brand/30' : 'hover:border-line-strong',
            ].join(' ')}
          >
            <div className="flex items-start justify-between gap-2">
              <span className="text-sm font-medium text-ink leading-snug">
                {v.titulo}
              </span>
              {typeof v.match_score === 'number' && (
                <MatchPill score={v.match_score} />
              )}
            </div>
            <div className="text-[12px] text-ink-mute mt-0.5">
              {v.empresa || 'sem empresa'}
            </div>
            <div className="flex items-center gap-2 mt-2">
              <StatusBadge status={v.status} />
              {v.qtd_rascunhos > 0 && (
                <span className="font-mono text-[10px] text-ink-mute">
                  {v.qtd_rascunhos} rascunho(s)
                </span>
              )}
              {v.tem_curriculo && (
                <span className="font-mono text-[10px] text-ink-mute">
                  📄 currículo
                </span>
              )}
            </div>
          </button>
        );
      })}
    </div>
  );
}


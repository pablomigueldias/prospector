import { useState } from 'react';

import { useComprovantes } from '@/hooks/useFinancas';
import type { Comprovante } from '@/lib/types';

const FILTROS: { label: string; tipo?: string }[] = [
  { label: 'Todos', tipo: undefined },
  { label: 'Boletos', tipo: 'boleto' },
  { label: 'Comprovantes', tipo: 'comprovante' },
  { label: 'Notas', tipo: 'nota_fiscal' },
];

const ICONE: Record<string, string> = {
  boleto: '🧾',
  comprovante: '📄',
  nota_fiscal: '📑',
};

export function ComprovantesGaleria() {
  const [tipo, setTipo] = useState<string | undefined>(undefined);
  const { comprovantes, loading } = useComprovantes(tipo);

  return (
    <div>
      {/* Filtro */}
      <div className="flex gap-1.5 mb-4">
        {FILTROS.map((f) => {
          const ativo = f.tipo === tipo;
          return (
            <button
              key={f.label}
              type="button"
              onClick={() => setTipo(f.tipo)}
              className={[
                'px-3 py-1.5 text-[12.5px] rounded-md font-medium transition-colors',
                ativo
                  ? 'bg-brand-soft text-brand'
                  : 'text-ink-soft hover:bg-bg-alt',
              ].join(' ')}
            >
              {f.label}
            </button>
          );
        })}
      </div>

      {loading ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
          {[0, 1, 2, 3].map((i) => (
            <div key={i} className="card h-[96px] animate-pulse" />
          ))}
        </div>
      ) : comprovantes.length === 0 ? (
        <div className="card p-6 text-center text-ink-soft text-sm">
          Nenhum comprovante por aqui ainda.
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
          {comprovantes.map((c) => (
            <ComprovanteCard key={c.id} comprovante={c} />
          ))}
        </div>
      )}
    </div>
  );
}

function ComprovanteCard({ comprovante: c }: { comprovante: Comprovante }) {
  const corpo = (
    <div className="card p-4 h-full flex flex-col gap-2 hover:border-brand transition-colors">
      <div className="text-2xl leading-none">{ICONE[c.tipo] ?? '📎'}</div>
      <div className="text-[13px] text-ink truncate" title={c.nome_original ?? ''}>
        {c.nome_original || 'arquivo'}
      </div>
      <div className="mt-auto font-mono uppercase tracking-[0.08em] text-[10px] text-ink-mute">
        {c.created_at?.slice(0, 10) ?? ''}
      </div>
    </div>
  );
  if (!c.url) return corpo;
  return (
    <a href={c.url} target="_blank" rel="noopener noreferrer">
      {corpo}
    </a>
  );
}

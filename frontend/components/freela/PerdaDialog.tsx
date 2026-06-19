import { useState } from 'react';

import { useFetch } from '@/hooks/useFetch';
import { api } from '@/lib/api';
import { type FreelaKanbanItem } from '@/lib/types';

const OUTRO = '__outro__';

/**
 * Diálogo ao marcar uma proposta como "perdida": escolhe o motivo de uma lista
 * gerenciável (grupo `freela_motivo_perda` em crm_opcoes) ou digita um novo.
 * Substitui o window.prompt antigo — motivo de perda vira dado estruturado.
 */
export function PerdaDialog({
  item,
  onCancel,
  onConfirm,
}: {
  item: FreelaKanbanItem;
  onCancel: () => void;
  onConfirm: (motivo: string | null) => void;
}) {
  const { data } = useFetch(() => api.crmOpcoes(), []);
  const motivos = data?.freela_motivo_perda ?? [];
  const [sel, setSel] = useState('');
  const [outro, setOutro] = useState('');

  const motivo = (sel === OUTRO ? outro : sel).trim() || null;

  return (
    <div
      className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4"
      onClick={onCancel}
    >
      <div className="card w-full max-w-[420px] p-5" onClick={(e) => e.stopPropagation()}>
        <div className="eyebrow mb-1">Marcar como perdida</div>
        <h3 className="font-display font-semibold text-base text-ink m-0 mb-3 truncate">
          {item.projeto_titulo}
        </h3>

        <label className="text-[13px] text-ink-soft">
          Motivo (opcional)
          <select
            className="input mt-1"
            value={sel}
            onChange={(e) => setSel(e.target.value)}
          >
            <option value="">— sem motivo —</option>
            {motivos.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
            <option value={OUTRO}>Outro…</option>
          </select>
        </label>

        {sel === OUTRO && (
          <input
            autoFocus
            className="input mt-2"
            placeholder="Descreva o motivo"
            value={outro}
            onChange={(e) => setOutro(e.target.value)}
          />
        )}

        <div className="flex justify-end gap-2 mt-4">
          <button type="button" className="btn-ghost" onClick={onCancel}>
            Cancelar
          </button>
          <button type="button" className="btn-primary" onClick={() => onConfirm(motivo)}>
            Marcar perdida
          </button>
        </div>
      </div>
    </div>
  );
}

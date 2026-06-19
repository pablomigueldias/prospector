import { useEffect, useRef, useState } from 'react';

import { pilulaCor } from '@/components/crm/_crmShared';
import { api } from '@/lib/api';
import type { RecordDetalhe, RecordTipo } from '@/lib/types';

type Kind = 'text' | 'num' | 'date' | 'select' | 'bool';

/**
 * Célula editável no lugar (click-to-edit). Mostra o valor; ao clicar vira um
 * input/select; salva via PATCH /crm/record ao confirmar (Enter/blur/change).
 * Esc cancela. Usada nas tabelas do CRM e no RecordModal — manuseio direto,
 * sem abrir formulário. `onSaved` recebe o registro já atualizado.
 */
export function InlineCell({
  tipo,
  id,
  campo,
  valor,
  display,
  kind = 'text',
  opcoes,
  coresPorValor,
  vazioLabel = '—',
  className = '',
  onSaved,
}: {
  tipo: RecordTipo;
  id: string;
  campo: string;
  valor?: string | number | boolean | null;
  display?: string;
  kind?: Kind;
  opcoes?: string[];
  coresPorValor?: Record<string, string>;
  vazioLabel?: string;
  className?: string;
  onSaved?: (rec: RecordDetalhe) => void;
}) {
  const [editando, setEditando] = useState(false);
  const [rascunho, setRascunho] = useState('');
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const ref = useRef<HTMLInputElement | HTMLSelectElement>(null);

  useEffect(() => {
    if (editando) ref.current?.focus();
  }, [editando]);

  const original = valor == null ? '' : String(valor);
  const textoExibido = display ?? (original || vazioLabel);

  async function salvar(novo: unknown) {
    setEditando(false);
    if (kind !== 'bool' && String(novo) === original) return; // nada mudou
    setSalvando(true);
    setErro(null);
    try {
      const rec = await api.crmRecordPatch(tipo, id, { [campo]: novo });
      onSaved?.(rec);
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Falha ao salvar');
    } finally {
      setSalvando(false);
    }
  }

  // Bool: toggle direto, sem modo de edição.
  if (kind === 'bool') {
    return (
      <button
        type="button"
        disabled={salvando}
        onClick={(e) => {
          e.stopPropagation();
          salvar(!valor);
        }}
        title={erro ?? 'Clique p/ alternar'}
        className={`text-[12px] px-2 py-0.5 rounded-full border transition-colors ${
          valor
            ? 'bg-brand-soft text-brand border-brand/30'
            : 'bg-surface text-ink-mute border-line'
        } ${className}`}
      >
        {valor ? 'Sim' : 'Não'}
      </button>
    );
  }

  if (editando) {
    if (kind === 'select') {
      return (
        <select
          ref={ref as React.RefObject<HTMLSelectElement>}
          className="input !py-1 !text-[12.5px] max-w-[180px]"
          defaultValue={original}
          onClick={(e) => e.stopPropagation()}
          onChange={(e) => salvar(e.target.value)}
          onBlur={() => setEditando(false)}
        >
          <option value="">{vazioLabel}</option>
          {(opcoes ?? []).map((o) => (
            <option key={o} value={o}>
              {o}
            </option>
          ))}
        </select>
      );
    }
    return (
      <input
        ref={ref as React.RefObject<HTMLInputElement>}
        type={kind === 'num' ? 'number' : kind === 'date' ? 'date' : 'text'}
        className="input !py-1 !text-[12.5px] max-w-[200px]"
        value={rascunho}
        onClick={(e) => e.stopPropagation()}
        onChange={(e) => setRascunho(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter') salvar(rascunho);
          else if (e.key === 'Escape') {
            setRascunho(original); // blur subsequente vira no-op
            setEditando(false);
          }
        }}
        onBlur={() => salvar(rascunho)}
      />
    );
  }

  // Select com valor preenchido → pílula colorida (estilo Notion).
  if (kind === 'select' && original && !salvando) {
    const cor = coresPorValor?.[original];
    return (
      <button
        type="button"
        title={erro ?? 'Clique p/ editar'}
        onClick={(e) => {
          e.stopPropagation();
          setRascunho(original);
          setEditando(true);
        }}
        className={`text-[12px] px-2 py-0.5 rounded-full whitespace-nowrap hover:ring-1 hover:ring-line transition-all ${pilulaCor(
          cor,
        )} ${erro ? '!text-red-600' : ''} ${className}`}
      >
        {textoExibido}
      </button>
    );
  }

  return (
    <button
      type="button"
      disabled={salvando}
      title={erro ?? 'Clique p/ editar'}
      onClick={(e) => {
        e.stopPropagation();
        setRascunho(original);
        setEditando(true);
      }}
      className={`text-left rounded px-1 -mx-1 hover:bg-bg-alt transition-colors ${
        erro ? 'text-red-600' : original ? 'text-ink' : 'text-ink-mute'
      } ${salvando ? 'opacity-50' : ''} ${className}`}
    >
      {salvando ? '…' : textoExibido}
    </button>
  );
}

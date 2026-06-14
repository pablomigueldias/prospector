import { useState } from 'react';

import { api } from '@/lib/api';
import { formatBRL } from '@/lib/format';
import { ApiError, type TransacaoListItem } from '@/lib/types';

function dataCurta(iso: string): string {
  // "2026-06-10" → "10/06"
  const [, m, d] = iso.split('-');
  return d && m ? `${d}/${m}` : iso;
}

export function TransacoesLista({
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

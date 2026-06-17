import { useEffect, useRef, useState } from 'react';

import { Modal } from '@/components/shared/Modal';
import { api } from '@/lib/api';
import { formatBRL } from '@/lib/format';
import type { TransacaoListItem } from '@/lib/types';

/** Busca global de transações — procura em TODOS os meses pela descrição e,
 *  ao clicar num resultado, leva o dashboard pro mês daquele lançamento.
 *  Aberta pelo atalho "/" ou pelo botão na sub-navegação. */
export function BuscaGlobalModal({
  onVerMes,
  onClose,
}: {
  onVerMes: (ano: number, mes: number) => void;
  onClose: () => void;
}) {
  const [termoInput, setTermoInput] = useState('');
  const [termo, setTermo] = useState('');
  const [resultados, setResultados] = useState<TransacaoListItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);
  const reqId = useRef(0);

  // Debounce (evita um request por tecla).
  useEffect(() => {
    const t = setTimeout(() => setTermo(termoInput.trim()), 350);
    return () => clearTimeout(t);
  }, [termoInput]);

  useEffect(() => {
    if (termo.length < 2) {
      setResultados([]);
      setTotal(0);
      setLoading(false);
      return;
    }
    const id = ++reqId.current;
    setLoading(true);
    api
      .financasTransacoes({ busca: termo, limit: 25 })
      .then((r) => {
        if (id !== reqId.current) return; // resposta antiga, descarta
        setResultados(r.items);
        setTotal(r.total);
      })
      .catch(() => {
        if (id !== reqId.current) return;
        setResultados([]);
        setTotal(0);
      })
      .finally(() => {
        if (id === reqId.current) setLoading(false);
      });
  }, [termo]);

  function abrir(t: TransacaoListItem) {
    const [a, m] = t.data_competencia.split('-').map(Number);
    if (a && m) onVerMes(a, m);
    onClose();
  }

  return (
    <Modal open onClose={onClose} title="Buscar lançamentos">
      <div className="space-y-3">
        <input
          className="input"
          value={termoInput}
          onChange={(e) => setTermoInput(e.target.value)}
          placeholder="Buscar por descrição em todos os meses…"
          autoFocus
        />

        {termo.length < 2 ? (
          <p className="text-[13px] text-ink-mute m-0">
            Digite ao menos 2 letras. Procura em todas as transações, de qualquer
            mês.
          </p>
        ) : loading ? (
          <div className="space-y-2">
            {[0, 1, 2].map((i) => (
              <div key={i} className="h-[44px] rounded bg-line-soft animate-pulse" />
            ))}
          </div>
        ) : resultados.length === 0 ? (
          <p className="text-[13px] text-ink-mute m-0">
            Nada encontrado para “{termo}”.
          </p>
        ) : (
          <>
            <ul className="m-0 p-0 list-none flex flex-col divide-y divide-line-soft max-h-[50vh] overflow-auto">
              {resultados.map((t) => {
                const despesa = t.tipo === 'despesa';
                const [a, m, d] = t.data_competencia.split('-');
                return (
                  <li key={t.id}>
                    <button
                      type="button"
                      onClick={() => abrir(t)}
                      className="w-full flex items-center gap-3 py-2 px-1 -mx-1 text-left hover:bg-line-soft/50 rounded transition-colors"
                      title="Abrir o mês deste lançamento"
                    >
                      <span className="w-14 shrink-0 font-mono text-[11px] text-ink-mute">
                        {d && m ? `${d}/${m}/${a?.slice(2)}` : t.data_competencia}
                      </span>
                      <span className="min-w-0 flex-1">
                        <span className="block text-sm text-ink truncate">
                          {t.descricao}
                        </span>
                        <span className="block text-[11.5px] text-ink-mute truncate">
                          {[t.categoria_nome, ...(t.contas ?? [])]
                            .filter(Boolean)
                            .join(' · ') || 'sem categoria'}
                        </span>
                      </span>
                      <span
                        className={`shrink-0 font-display font-semibold tracking-tight text-sm ${
                          despesa ? 'text-ink' : 'text-success'
                        }`}
                      >
                        {despesa ? '−' : '+'}
                        {formatBRL(t.valor_total)}
                      </span>
                    </button>
                  </li>
                );
              })}
            </ul>
            {total > resultados.length && (
              <p className="text-[12px] text-ink-mute m-0">
                Mostrando {resultados.length} de {total}. Refine a busca pra ver
                mais.
              </p>
            )}
          </>
        )}
      </div>
    </Modal>
  );
}

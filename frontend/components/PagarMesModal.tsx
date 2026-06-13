import { useEffect, useMemo, useState } from 'react';

import { Modal } from '@/components/Modal';
import { api } from '@/lib/api';
import { formatBRL } from '@/lib/format';
import {
  ApiError,
  type Conta,
  type PagamentoMesItem,
  type PagamentoMesPreview,
} from '@/lib/types';

/** Linha selecionável: o item + a conta escolhida + se entra no pagamento. */
interface Linha {
  item: PagamentoMesItem;
  contaId: string;
  marcado: boolean;
}

/**
 * "Pagar o mês": lista as pendências do mês (boletos a pagar + faturas em
 * aberto), cada uma com a conta de onde sai, e quita as marcadas de uma vez.
 */
export function PagarMesModal({
  contas,
  onClose,
  onPaid,
}: {
  contas: Conta[];
  onClose: () => void;
  onPaid: () => void;
}) {
  const [linhas, setLinhas] = useState<Linha[] | null>(null);
  const [carregando, setCarregando] = useState(true);
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState('');

  useEffect(() => {
    let vivo = true;
    (async () => {
      try {
        const pv: PagamentoMesPreview = await api.financasPagarMesPreview();
        if (!vivo) return;
        setLinhas(
          pv.itens.map((item) => ({
            item,
            contaId: item.conta_sugerida_id ?? contas[0]?.id ?? '',
            marcado: true,
          })),
        );
      } catch (e) {
        if (vivo) setErro(e instanceof ApiError ? e.message : 'Falha ao carregar.');
      } finally {
        if (vivo) setCarregando(false);
      }
    })();
    return () => {
      vivo = false;
    };
  }, [contas]);

  const total = useMemo(
    () =>
      (linhas ?? [])
        .filter((l) => l.marcado)
        .reduce((acc, l) => acc + Number(l.item.valor), 0),
    [linhas],
  );
  const marcadas = (linhas ?? []).filter((l) => l.marcado);

  function set(i: number, patch: Partial<Linha>) {
    setLinhas((ls) => (ls ? ls.map((l, idx) => (idx === i ? { ...l, ...patch } : l)) : ls));
  }

  async function pagar() {
    if (!linhas) return;
    setErro('');
    const sel = linhas.filter((l) => l.marcado);
    if (sel.length === 0) return setErro('Marque ao menos uma pendência.');
    if (sel.some((l) => !l.contaId)) return setErro('Escolha a conta de cada item marcado.');
    setSalvando(true);
    try {
      const r = await api.financasPagarMes(
        sel.map((l) => ({ tipo: l.item.tipo, id: l.item.id, conta_id: l.contaId })),
      );
      if (r.falhas.length > 0) {
        setErro(`Pagou ${r.pagos}, mas ${r.falhas.length} falhou(ram): ${r.falhas[0]}`);
        setSalvando(false);
        onPaid(); // recarrega o que deu certo
        return;
      }
      onPaid();
    } catch (e) {
      setErro(e instanceof ApiError ? e.message : 'Falha ao pagar.');
      setSalvando(false);
    }
  }

  return (
    <Modal open onClose={onClose} title="Pagar o mês">
      {carregando ? (
        <div className="h-24 animate-pulse" />
      ) : !linhas || linhas.length === 0 ? (
        <p className="text-sm text-ink-mute m-0">
          Nada a pagar este mês. 🎉
        </p>
      ) : (
        <div className="space-y-3">
          <ul className="m-0 p-0 list-none flex flex-col divide-y divide-line-soft">
            {linhas.map((l, i) => (
              <li key={`${l.item.tipo}-${l.item.id}`} className="py-2.5">
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={l.marcado}
                    onChange={(e) => set(i, { marcado: e.target.checked })}
                  />
                  <div className="min-w-0 flex-1">
                    <div className="text-sm text-ink truncate">
                      <span
                        className={`font-mono uppercase tracking-[0.08em] text-[9px] mr-1.5 ${
                          l.item.tipo === 'fatura' ? 'text-brand-deep' : 'text-ink-mute'
                        }`}
                      >
                        {l.item.tipo}
                      </span>
                      {l.item.descricao}
                    </div>
                  </div>
                  <span className="text-ink tabular-nums shrink-0 text-sm">
                    {formatBRL(l.item.valor)}
                  </span>
                </div>
                <div className={`mt-1 pl-6 ${l.marcado ? '' : 'opacity-40'}`}>
                  <select
                    className="input h-8 py-0 text-[13px]"
                    value={l.contaId}
                    disabled={!l.marcado}
                    onChange={(e) => set(i, { contaId: e.target.value })}
                  >
                    <option value="">Conta…</option>
                    {contas.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.nome}
                      </option>
                    ))}
                  </select>
                </div>
              </li>
            ))}
          </ul>

          <div className="flex items-baseline justify-between border-t border-line pt-3">
            <span className="font-mono uppercase tracking-[0.1em] text-[10px] text-ink-mute">
              {marcadas.length} item(ns)
            </span>
            <span className="font-display font-semibold tracking-tight text-ink">
              {formatBRL(total)}
            </span>
          </div>

          {erro && <div className="text-sm text-red-600">{erro}</div>}

          <div className="flex items-center justify-end gap-2">
            <button type="button" onClick={onClose} className="btn-ghost px-4 py-2 text-sm">
              Cancelar
            </button>
            <button
              type="button"
              onClick={pagar}
              disabled={salvando || marcadas.length === 0}
              className="btn-primary px-5 py-2 text-sm disabled:opacity-50"
            >
              {salvando ? 'Pagando…' : `Pagar ${formatBRL(total)}`}
            </button>
          </div>
        </div>
      )}
    </Modal>
  );
}

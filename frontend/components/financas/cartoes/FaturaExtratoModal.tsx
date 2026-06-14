import { useState } from 'react';

import { Modal } from '@/components/Modal';
import { useFetch } from '@/hooks/useFetch';
import { useContas } from '@/hooks/useFinancas';
import { api } from '@/lib/api';
import { formatBRL } from '@/lib/format';
import { ApiError, type Compra, type Fatura, type FaturaExtrato } from '@/lib/types';

/** Modal do extrato da fatura: itens parcela a parcela, ver parcelas de uma
 *  compra, estornar compra e pagar a fatura (debita conta). */
export function FaturaExtratoModal({
  cartaoId,
  fatura,
  iniciarPagando = false,
  onClose,
  onPaid,
}: {
  cartaoId: string;
  fatura: Fatura;
  iniciarPagando?: boolean;
  onClose: () => void;
  onPaid: () => void;
}) {
  const { data, loading, error } = useFetch<FaturaExtrato>(
    () => api.financasFaturaExtrato(cartaoId, fatura.id),
    [cartaoId, fatura.id],
  );
  const { contas } = useContas(true);
  const [pagando, setPagando] = useState(iniciarPagando && fatura.status !== 'paga');
  const [contaId, setContaId] = useState('');
  const [dataPg, setDataPg] = useState(() => new Date().toISOString().slice(0, 10));
  const [valorPago, setValorPago] = useState('');
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState('');
  const [estornando, setEstornando] = useState<string | null>(null);
  const [verCompra, setVerCompra] = useState<string | null>(null);
  const [compraDet, setCompraDet] = useState<Compra | null>(null);
  const [carregandoCompra, setCarregandoCompra] = useState(false);

  const paga = fatura.status === 'paga';

  async function alternarParcelas(compraId: string) {
    if (verCompra === compraId) {
      setVerCompra(null);
      return;
    }
    setVerCompra(compraId);
    setCompraDet(null);
    setCarregandoCompra(true);
    try {
      setCompraDet(await api.financasCompra(compraId));
    } catch {
      setCompraDet(null);
    } finally {
      setCarregandoCompra(false);
    }
  }

  async function estornar(compraId: string, descricao: string, totalParcelas: number) {
    const aviso =
      totalParcelas > 1
        ? `Estornar a compra “${descricao}” inteira? As ${totalParcelas} parcelas (deste e dos próximos meses) somem e o valor sai das faturas.`
        : `Estornar a compra “${descricao}”? Ela sai da fatura.`;
    if (!window.confirm(aviso)) return;
    setErro('');
    setEstornando(compraId);
    try {
      await api.financasExcluirCompra(compraId);
      onPaid(); // fecha + recarrega o card (parcelas podem estar em vários meses)
    } catch (err) {
      setErro(err instanceof ApiError ? err.message : 'Falha ao estornar a compra.');
      setEstornando(null);
    }
  }

  async function pagar() {
    setErro('');
    if (!contaId) return setErro('Escolha a conta que pagou a fatura.');
    const valorStr = valorPago.trim()
      ? String(Number(valorPago.replace(',', '.')))
      : null;
    if (valorStr !== null && (!Number.isFinite(Number(valorStr)) || Number(valorStr) <= 0)) {
      return setErro('Valor pago inválido.');
    }
    setSalvando(true);
    try {
      await api.financasPagarFatura(cartaoId, fatura.id, {
        conta_id: contaId,
        data_pagamento: dataPg || null,
        valor_pago: valorStr,
      });
      onPaid();
    } catch (err) {
      setErro(err instanceof ApiError ? err.message : 'Falha ao pagar a fatura.');
      setSalvando(false);
    }
  }

  return (
    <Modal open onClose={onClose} title={`Fatura · vence ${fatura.vencimento}`}>
      {loading ? (
        <div className="h-24 animate-pulse" />
      ) : error ? (
        <div className="text-sm text-red-600">Falha ao carregar o extrato.</div>
      ) : (
        <div className="space-y-3">
          {!data || data.itens.length === 0 ? (
            <p className="text-sm text-ink-mute m-0">
              Nenhuma parcela nesta fatura ainda.
            </p>
          ) : (
            <ul className="m-0 p-0 list-none flex flex-col divide-y divide-line-soft">
              {data.itens.map((it) => (
                <li key={it.parcela_id} className="py-2 text-sm group">
                  <div className="flex items-center justify-between gap-3">
                    <div className="min-w-0">
                      <div className="text-ink truncate">{it.descricao}</div>
                      <div className="font-mono uppercase tracking-[0.08em] text-[10px] text-ink-mute">
                        {it.numero}/{it.total_parcelas}
                        {it.categoria_nome ? ` · ${it.categoria_nome}` : ''}
                        {Number(it.valor_juros) > 0
                          ? ` · juros ${formatBRL(it.valor_juros)}`
                          : ''}
                      </div>
                    </div>
                    <span className="text-ink tabular-nums shrink-0">
                      {formatBRL(it.valor)}
                    </span>
                    {it.total_parcelas > 1 && (
                      <button
                        type="button"
                        onClick={() => alternarParcelas(it.compra_id)}
                        className="shrink-0 text-ink-faint hover:text-brand text-sm px-1 transition-colors"
                        title="Ver todas as parcelas desta compra"
                        aria-label="Ver parcelas da compra"
                      >
                        {verCompra === it.compra_id ? '▾' : 'ⓘ'}
                      </button>
                    )}
                    {!paga && (
                      <button
                        type="button"
                        onClick={() => estornar(it.compra_id, it.descricao, it.total_parcelas)}
                        disabled={estornando === it.compra_id}
                        className="shrink-0 text-ink-faint hover:text-red-600 text-sm px-1 opacity-0 group-hover:opacity-100 transition-opacity disabled:opacity-50"
                        title={
                          it.total_parcelas > 1
                            ? 'Estornar a compra inteira (todas as parcelas)'
                            : 'Estornar a compra'
                        }
                        aria-label="Estornar a compra"
                      >
                        {estornando === it.compra_id ? '…' : '✕'}
                      </button>
                    )}
                  </div>

                  {verCompra === it.compra_id && (
                    <div className="mt-2 ml-2 pl-3 border-l-2 border-line-soft">
                      {carregandoCompra || !compraDet ? (
                        <div className="h-10 animate-pulse" />
                      ) : (
                        <ul className="m-0 p-0 list-none flex flex-col gap-1">
                          {compraDet.parcelas
                            .slice()
                            .sort((a, b) => a.numero - b.numero)
                            .map((p) => (
                              <li
                                key={p.id}
                                className="flex items-center justify-between text-[12px] text-ink-soft"
                              >
                                <span className="font-mono text-[10px] text-ink-mute">
                                  {p.numero}/{p.total_parcelas} · vence {p.vencimento}
                                </span>
                                <span className="tabular-nums">
                                  {formatBRL(p.valor)}
                                  {Number(p.valor_juros) > 0
                                    ? ` (juros ${formatBRL(p.valor_juros)})`
                                    : ''}
                                </span>
                              </li>
                            ))}
                        </ul>
                      )}
                    </div>
                  )}
                </li>
              ))}
            </ul>
          )}

          <div className="flex items-baseline justify-between border-t border-line pt-3">
            <span className="font-mono uppercase tracking-[0.1em] text-[10px] text-ink-mute">
              total da fatura
            </span>
            <span className="font-display font-semibold tracking-tight text-ink">
              {formatBRL((data ?? { fatura }).fatura.valor_total)}
            </span>
          </div>

          {paga ? (
            <div className="text-sm text-ink-mute border-t border-line-soft pt-3">
              Fatura já paga. ✓
            </div>
          ) : !pagando ? (
            <div className="flex justify-end border-t border-line-soft pt-3">
              <button
                type="button"
                onClick={() => setPagando(true)}
                className="btn-primary px-4 py-2 text-sm"
              >
                Pagar fatura
              </button>
            </div>
          ) : (
            <div className="space-y-3 border-t border-line-soft pt-3">
              <div>
                <label className="block text-[13px] font-medium text-ink-soft mb-1.5">
                  Conta
                </label>
                <select
                  className="input"
                  value={contaId}
                  onChange={(e) => setContaId(e.target.value)}
                >
                  <option value="">Escolha a conta…</option>
                  {contas.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.nome}
                    </option>
                  ))}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[13px] font-medium text-ink-soft mb-1.5">
                    Data do pagamento
                  </label>
                  <input
                    type="date"
                    className="input"
                    value={dataPg}
                    onChange={(e) => setDataPg(e.target.value)}
                  />
                </div>
                <div>
                  <label className="block text-[13px] font-medium text-ink-soft mb-1.5">
                    Valor pago (opcional)
                  </label>
                  <input
                    className="input"
                    value={valorPago}
                    onChange={(e) => setValorPago(e.target.value)}
                    inputMode="decimal"
                    placeholder={formatBRL((data ?? { fatura }).fatura.valor_total)}
                  />
                </div>
              </div>
              {erro && <div className="text-sm text-red-600">{erro}</div>}
              <div className="flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setPagando(false)}
                  className="btn-ghost px-4 py-2 text-sm"
                >
                  Voltar
                </button>
                <button
                  type="button"
                  onClick={pagar}
                  disabled={salvando}
                  className="btn-primary px-5 py-2 text-sm disabled:opacity-50"
                >
                  {salvando ? 'Pagando…' : 'Confirmar pagamento'}
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </Modal>
  );
}

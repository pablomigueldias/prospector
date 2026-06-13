import { useMemo, useState, type FormEvent } from 'react';

import { Modal } from '@/components/Modal';
import { api } from '@/lib/api';
import { calcularEncargos } from '@/lib/encargos';
import { formatBRL } from '@/lib/format';
import { ApiError, type Conta } from '@/lib/types';

/** Transação que está sendo quitada no modal "Pagar". */
export interface PagamentoAlvo {
  id: string;
  descricao: string;
  valor: string;
  /** Conta já vinculada (prevista lançada com conta) ou null (boleto/recorrência). */
  contaIdAtual: string | null;
  /** Encargos por atraso (boleto), pra projetar multa+juros até a data de pagamento. */
  vencimento?: string | null;
  multaPct?: string | number | null;
  jurosPct?: string | number | null;
}

/**
 * Modal de quitação: marca uma transação prevista/atrasada como paga e move o
 * saldo. Se a transação ainda não tem conta (boleto importado / recorrência),
 * pede pra escolher; senão usa a já vinculada.
 */
export function PagarModal({
  contas,
  alvo,
  onClose,
  onPaid,
}: {
  contas: Conta[];
  alvo: PagamentoAlvo;
  onClose: () => void;
  onPaid: () => void;
}) {
  const hojeIso = new Date().toISOString().slice(0, 10);
  const precisaConta = !alvo.contaIdAtual;
  const contaAtualNome = contas.find((c) => c.id === alvo.contaIdAtual)?.nome;
  const [contaId, setContaId] = useState(alvo.contaIdAtual ?? contas[0]?.id ?? '');
  const [data, setData] = useState(hojeIso);
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState('');

  // Multa + juros até a data escolhida (recalcula quando muda a data).
  const enc = useMemo(
    () =>
      calcularEncargos(
        alvo.valor, alvo.vencimento, alvo.multaPct, alvo.jurosPct, data,
      ),
    [alvo, data],
  );
  const totalComEncargos = Number(alvo.valor) + enc.total;

  async function confirmar(e: FormEvent) {
    e.preventDefault();
    setErro('');
    if (precisaConta && !contaId) return setErro('Escolha a conta.');
    setSalvando(true);
    try {
      await api.financasPagarTransacao(
        alvo.id,
        precisaConta ? contaId : undefined,
        data,
      );
      onPaid();
    } catch (err) {
      setErro(
        err instanceof ApiError ? err.message : 'Falha ao registrar o pagamento.',
      );
    } finally {
      setSalvando(false);
    }
  }

  return (
    <Modal open onClose={onClose} title="Registrar pagamento">
      <form onSubmit={confirmar} className="space-y-4">
        <div className="card bg-bg-alt p-3">
          <div className="flex items-center justify-between">
            <span className="text-sm text-ink truncate pr-2">{alvo.descricao}</span>
            <span className="text-sm text-ink-soft shrink-0">
              {formatBRL(alvo.valor)}
            </span>
          </div>
          {enc.total > 0 && (
            <div className="mt-2 pt-2 border-t border-line space-y-1 text-[12.5px]">
              {enc.multa > 0 && (
                <div className="flex justify-between text-ink-soft">
                  <span>Multa por atraso</span>
                  <span className="font-mono">+{formatBRL(enc.multa)}</span>
                </div>
              )}
              {enc.juros > 0 && (
                <div className="flex justify-between text-ink-soft">
                  <span>Juros de mora ({enc.dias} {enc.dias === 1 ? 'dia' : 'dias'})</span>
                  <span className="font-mono">+{formatBRL(enc.juros)}</span>
                </div>
              )}
            </div>
          )}
          <div className="mt-2 pt-2 border-t border-line flex items-center justify-between">
            <span className="text-[13px] font-medium text-ink">
              {enc.total > 0 ? 'Total a pagar' : 'Valor'}
            </span>
            <strong className="text-sm text-ink">{formatBRL(totalComEncargos)}</strong>
          </div>
        </div>

        {enc.total > 0 && (
          <p className="text-[12px] text-red-600 -mt-1">
            Boleto vencido — multa e juros calculados até a data abaixo.
          </p>
        )}

        {precisaConta ? (
          <div>
            <label className="block text-[13px] font-medium text-ink-soft mb-1.5">
              Pagar com qual conta?
            </label>
            <select
              className="input"
              value={contaId}
              onChange={(e) => setContaId(e.target.value)}
              autoFocus
            >
              {contas.length === 0 && <option value="">Nenhuma conta</option>}
              {contas.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.nome}
                </option>
              ))}
            </select>
          </div>
        ) : (
          <div className="text-[13px] text-ink-soft">
            Sai de <strong className="text-ink">{contaAtualNome ?? 'conta'}</strong>.
          </div>
        )}

        <div>
          <label className="block text-[13px] font-medium text-ink-soft mb-1.5">
            Data do pagamento
          </label>
          <input
            type="date"
            className="input"
            value={data}
            onChange={(e) => setData(e.target.value)}
          />
        </div>

        {erro && (
          <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded px-3 py-2">
            {erro}
          </div>
        )}

        <div className="flex items-center justify-end gap-2 pt-1">
          <button
            type="button"
            onClick={onClose}
            className="btn-ghost px-4 py-2 text-sm"
          >
            Cancelar
          </button>
          <button
            type="submit"
            disabled={salvando || (precisaConta && !contaId)}
            className="btn-primary px-5 py-2 text-sm disabled:opacity-50"
          >
            {salvando
              ? 'Registrando…'
              : enc.total > 0
                ? `Pagar ${formatBRL(totalComEncargos)}`
                : 'Confirmar pagamento'}
          </button>
        </div>
      </form>
    </Modal>
  );
}

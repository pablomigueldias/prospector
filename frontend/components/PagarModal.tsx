import { useState, type FormEvent } from 'react';

import { Modal } from '@/components/Modal';
import { api } from '@/lib/api';
import { formatBRL } from '@/lib/format';
import { ApiError, type Conta } from '@/lib/types';

/** Transação que está sendo quitada no modal "Pagar". */
export interface PagamentoAlvo {
  id: string;
  descricao: string;
  valor: string;
  /** Conta já vinculada (prevista lançada com conta) ou null (boleto/recorrência). */
  contaIdAtual: string | null;
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
        <div className="card bg-bg-alt p-3 flex items-center justify-between">
          <span className="text-sm text-ink truncate pr-2">{alvo.descricao}</span>
          <strong className="text-sm text-ink shrink-0">
            {formatBRL(alvo.valor)}
          </strong>
        </div>

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
            {salvando ? 'Registrando…' : 'Confirmar pagamento'}
          </button>
        </div>
      </form>
    </Modal>
  );
}

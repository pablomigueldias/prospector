import { useState } from 'react';

import { Modal } from '@/components/shared/Modal';
import { api } from '@/lib/api';
import { formatBRL } from '@/lib/format';
import { ApiError, type Conta, type Recorrencia } from '@/lib/types';

/** Modal pra marcar uma recorrência (conta fixa) como paga no mês, escolhendo
 *  a conta e, opcionalmente, o valor real. Não confundir com o PagarMesModal
 *  global (que junta boletos + faturas do mês). */
export function PagarRecorrenciaModal({
  rec,
  contas,
  competencia,
  onClose,
  onPaid,
}: {
  rec: Recorrencia;
  contas: Conta[];
  competencia: string;
  onClose: () => void;
  onPaid: () => void;
}) {
  const [contaId, setContaId] = useState(rec.conta_id ?? '');
  const [valor, setValor] = useState('');
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState('');

  async function confirmar() {
    setErro('');
    if (!contaId) return setErro('Escolha a conta que pagou.');
    const valorStr = valor.trim()
      ? String(Number(valor.replace(',', '.')))
      : null;
    if (valorStr !== null && (!Number.isFinite(Number(valorStr)) || Number(valorStr) <= 0)) {
      return setErro('Valor inválido.');
    }
    setSalvando(true);
    try {
      await api.financasPagarMesRecorrencia(rec.id, {
        competencia,
        conta_id: contaId,
        valor_pago: valorStr,
      });
      onPaid();
    } catch (err) {
      setErro(err instanceof ApiError ? err.message : 'Falha ao marcar como paga.');
      setSalvando(false);
    }
  }

  return (
    <Modal open onClose={onClose} title={`Marcar paga · ${rec.descricao}`}>
      <div className="space-y-4">
        <div>
          <label className="block text-[13px] font-medium text-ink-soft mb-1.5">
            Conta que pagou
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
        <div>
          <label className="block text-[13px] font-medium text-ink-soft mb-1.5">
            Valor pago (opcional)
          </label>
          <input
            className="input"
            value={valor}
            onChange={(e) => setValor(e.target.value)}
            inputMode="decimal"
            placeholder={formatBRL(rec.valor_estimado)}
          />
        </div>
        {erro && <div className="text-sm text-red-600">{erro}</div>}
        <div className="flex items-center justify-end gap-2">
          <button type="button" onClick={onClose} className="btn-ghost px-4 py-2 text-sm">
            Cancelar
          </button>
          <button
            type="button"
            onClick={confirmar}
            disabled={salvando}
            className="btn-primary px-5 py-2 text-sm disabled:opacity-50"
          >
            {salvando ? 'Salvando…' : 'Marcar paga'}
          </button>
        </div>
      </div>
    </Modal>
  );
}

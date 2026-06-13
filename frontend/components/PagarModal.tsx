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
  /** Conta sugerida (última usada pra pagar o mesmo beneficiário). */
  contaSugeridaId?: string | null;
  contaSugeridaNome?: string | null;
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
  const [contaId, setContaId] = useState(
    alvo.contaIdAtual ?? alvo.contaSugeridaId ?? contas[0]?.id ?? '',
  );
  const [data, setData] = useState(hojeIso);
  // Multa/juros editáveis: prefill do que veio (IA), mas dá pra corrigir aqui
  // ou preencher boleto antigo que não tinha essa info.
  const pctInicial = (v: string | number | null | undefined) =>
    v == null || v === '' ? '' : String(v);
  const [multaPct, setMultaPct] = useState(pctInicial(alvo.multaPct));
  const [jurosPct, setJurosPct] = useState(pctInicial(alvo.jurosPct));
  const [ajustar, setAjustar] = useState(false);
  const [valorPago, setValorPago] = useState('');
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState('');

  // Só faz sentido cobrar encargos quando há vencimento (boleto/conta datada).
  const temVencimento = !!alvo.vencimento;

  // Multa + juros até a data escolhida (recalcula quando muda data ou %).
  const enc = useMemo(
    () => calcularEncargos(alvo.valor, alvo.vencimento, multaPct, jurosPct, data),
    [alvo.valor, alvo.vencimento, multaPct, jurosPct, data],
  );
  const totalCalculado = Number(alvo.valor) + enc.total;
  const valorPagoNum = Number(valorPago.replace(',', '.'));
  const ajusteValido = ajustar && Number.isFinite(valorPagoNum) && valorPagoNum > 0;
  const totalComEncargos = ajusteValido ? valorPagoNum : totalCalculado;

  async function confirmar(e: FormEvent) {
    e.preventDefault();
    setErro('');
    if (precisaConta && !contaId) return setErro('Escolha a conta.');
    setSalvando(true);
    try {
      await api.financasPagarTransacao(alvo.id, {
        contaId: precisaConta ? contaId : undefined,
        dataPagamento: data,
        // Salva os encargos informados (só quando há vencimento pra aplicar).
        multaPercentual: temVencimento && multaPct !== '' ? multaPct : null,
        jurosMensalPercentual: temVencimento && jurosPct !== '' ? jurosPct : null,
        // Valor manual sobrescreve o total calculado (acordo/desconto).
        valorPago: ajusteValido ? String(valorPagoNum) : null,
      });
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
              {ajusteValido ? 'Valor pago (ajustado)' : enc.total > 0 ? 'Total a pagar' : 'Valor'}
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
            {alvo.contaSugeridaNome && (
              <p className="text-[11.5px] text-ink-mute mt-1">
                Sugerida: <strong className="text-ink-soft">{alvo.contaSugeridaNome}</strong>{' '}
                (última vez que você pagou esse beneficiário)
              </p>
            )}
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

        {temVencimento && (
          <details open={enc.total > 0} className="group">
            <summary className="text-[12.5px] text-ink-soft cursor-pointer select-none hover:text-ink">
              Encargos por atraso (multa e juros do boleto)
            </summary>
            <div className="grid grid-cols-2 gap-3 mt-2">
              <div>
                <label className="block text-[12px] text-ink-soft mb-1">
                  Multa (%)
                </label>
                <input
                  className="input"
                  value={multaPct}
                  onChange={(e) => setMultaPct(e.target.value)}
                  inputMode="decimal"
                  placeholder="ex: 2"
                />
              </div>
              <div>
                <label className="block text-[12px] text-ink-soft mb-1">
                  Juros (% ao mês)
                </label>
                <input
                  className="input"
                  value={jurosPct}
                  onChange={(e) => setJurosPct(e.target.value)}
                  inputMode="decimal"
                  placeholder="ex: 1"
                />
              </div>
            </div>
            <p className="text-[11.5px] text-ink-mute mt-1.5">
              Preencha se a IA não pegou do boleto. Fica salvo na conta.
            </p>
          </details>
        )}

        <div>
          <label className="flex items-center gap-2 text-[12.5px] text-ink-soft cursor-pointer select-none">
            <input
              type="checkbox"
              checked={ajustar}
              onChange={(e) => {
                setAjustar(e.target.checked);
                if (e.target.checked && valorPago === '') {
                  setValorPago(totalCalculado.toFixed(2));
                }
              }}
            />
            Paguei um valor diferente (acordo, desconto, arredondamento)
          </label>
          {ajustar && (
            <input
              className="input mt-2"
              value={valorPago}
              onChange={(e) => setValorPago(e.target.value)}
              inputMode="decimal"
              placeholder="valor pago"
              autoFocus
            />
          )}
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

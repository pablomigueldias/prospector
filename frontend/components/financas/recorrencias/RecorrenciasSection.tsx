import { useMemo, useState } from 'react';

import { useFetch } from '@/hooks/useFetch';
import { useRecorrencias } from '@/hooks/useFinancas';
import { api } from '@/lib/api';
import { formatBRL } from '@/lib/format';
import {
  type Conta,
  type Recorrencia,
  type RecorrenciaStatusItem,
  type RecorrenciaStatusResponse,
} from '@/lib/types';

import { PagarRecorrenciaModal } from './PagarRecorrenciaModal';
import { RecorrenciaForm } from './RecorrenciaForm';
import { RecorrenciaRow } from './RecorrenciaRow';

interface Props {
  contas: Conta[];
  ano: number;
  mes: number;
  /** Recarrega resumo/contas do dashboard (marcar pago mexe em saldo). */
  onMutate?: () => void;
}

type ModalState =
  | { modo: 'fechado' }
  | { modo: 'nova' }
  | { modo: 'editar'; rec: Recorrencia };

export function RecorrenciasSection({ contas, ano, mes, onMutate }: Props) {
  const { recorrencias, loading, refetch } = useRecorrencias();
  const competencia = `${ano}-${String(mes).padStart(2, '0')}`;
  const {
    data: statusData,
    refetch: refetchStatus,
  } = useFetch<RecorrenciaStatusResponse>(
    () => api.financasRecorrenciasStatus(competencia),
    [competencia],
  );
  const [modal, setModal] = useState<ModalState>({ modo: 'fechado' });
  const [pagarRec, setPagarRec] = useState<Recorrencia | null>(null);
  const [processando, setProcessando] = useState(false);

  async function processar() {
    setProcessando(true);
    try {
      await api.financasProcessarRecorrencias();
      recarregar();
    } catch {
      /* silencioso — o cron diário também roda isso */
    } finally {
      setProcessando(false);
    }
  }

  const statusMap = useMemo(() => {
    const m = new Map<string, RecorrenciaStatusItem['situacao']>();
    for (const i of statusData?.items ?? []) m.set(i.recorrencia_id, i.situacao);
    return m;
  }, [statusData]);

  const recarregar = () => {
    void refetch();
    void refetchStatus();
    onMutate?.();
  };

  const totalMensal = recorrencias
    .filter((r) => r.tipo === 'despesa' && r.ativa)
    .reduce((acc, r) => acc + Number(r.valor_estimado), 0);

  async function marcar(rec: Recorrencia) {
    // Cartão: lança direto na fatura (sem conta). Conta/boleto com conta
    // definida: paga direto. Senão, abre o modal pra escolher a conta.
    if (rec.forma_pagamento === 'cartao' || rec.conta_id) {
      try {
        await api.financasPagarMesRecorrencia(rec.id, { competencia });
        recarregar();
      } catch {
        setPagarRec(rec); // deixa o usuário ajustar (ex.: faltou conta)
      }
      return;
    }
    setPagarRec(rec);
  }

  return (
    <section className="mb-8">
      <div className="flex items-center justify-between mb-4">
        <h2 className="font-display font-semibold text-lg tracking-tight text-ink m-0">
          Contas fixas
        </h2>
        <div className="flex items-center gap-3">
          {totalMensal > 0 && (
            <span className="text-[12.5px] text-ink-mute">
              ~{formatBRL(totalMensal)}/mês
            </span>
          )}
          <button
            type="button"
            onClick={() => void processar()}
            disabled={processando}
            className="btn-ghost px-3.5 py-1.5 text-sm disabled:opacity-50"
            title="Gera as previstas do mês e marca as atrasadas (o cron diário também faz)"
          >
            {processando ? 'Gerando…' : 'Gerar previstas'}
          </button>
          <button
            type="button"
            onClick={() => setModal({ modo: 'nova' })}
            className="btn-ghost px-3.5 py-1.5 text-sm"
          >
            + Nova fixa
          </button>
        </div>
      </div>

      {loading ? (
        <div className="card p-4 h-[84px] animate-pulse" />
      ) : recorrencias.length === 0 ? (
        <div className="card p-6 text-center text-ink-soft text-sm">
          Nenhuma conta fixa. Cadastre aluguel, assinaturas, salário etc. — o
          sistema gera as previstas todo mês.
        </div>
      ) : (
        <div className="card divide-y divide-line">
          {recorrencias.map((r) => (
            <RecorrenciaRow
              key={r.id}
              rec={r}
              situacao={statusMap.get(r.id) ?? 'nenhuma'}
              onEditar={() => setModal({ modo: 'editar', rec: r })}
              onMarcar={() => void marcar(r)}
            />
          ))}
        </div>
      )}

      {modal.modo !== 'fechado' && (
        <RecorrenciaForm
          rec={modal.modo === 'editar' ? modal.rec : null}
          contas={contas}
          onClose={() => setModal({ modo: 'fechado' })}
          onSaved={() => {
            setModal({ modo: 'fechado' });
            recarregar();
          }}
        />
      )}

      {pagarRec && (
        <PagarRecorrenciaModal
          rec={pagarRec}
          contas={contas}
          competencia={competencia}
          onClose={() => setPagarRec(null)}
          onPaid={() => {
            setPagarRec(null);
            recarregar();
          }}
        />
      )}
    </section>
  );
}

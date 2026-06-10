import { useState, type FormEvent } from 'react';

import { Modal } from '@/components/Modal';
import { api } from '@/lib/api';
import { formatBRL } from '@/lib/format';
import { ApiError, type Conta, type TipoConta } from '@/lib/types';

const TIPO_LABEL: Record<string, string> = {
  corrente: 'Conta corrente',
  dinheiro: 'Dinheiro',
  vr: 'Vale-refeição',
  va: 'Vale-alimentação',
  reserva: 'Reserva',
  cartao_credito: 'Cartão de crédito',
};

const TIPOS: TipoConta[] = [
  'corrente',
  'dinheiro',
  'vr',
  'va',
  'reserva',
  'cartao_credito',
];

interface Props {
  contas: Conta[];
  loading: boolean;
  /** Chamado após criar/editar/excluir pra recarregar a lista. */
  onChanged: () => void;
}

type ModalState =
  | { modo: 'fechado' }
  | { modo: 'nova' }
  | { modo: 'editar'; conta: Conta };

export function ContasSection({ contas, loading, onChanged }: Props) {
  const [modal, setModal] = useState<ModalState>({ modo: 'fechado' });

  const contasNormais = contas.filter((c) => c.tipo !== 'reserva');
  const reservas = contas.filter((c) => c.tipo === 'reserva');
  const totalGuardado = reservas.reduce(
    (acc, c) => acc + Number(c.saldo_atual),
    0,
  );

  return (
    <>
      {/* Contas */}
      <section className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-display font-semibold text-lg tracking-tight text-ink m-0">
            Contas
          </h2>
          <div className="flex items-center gap-3">
            {contas.length > 0 && (
              <span className="text-[12.5px] text-ink-mute">
                {contas.length} {contas.length === 1 ? 'conta' : 'contas'}
              </span>
            )}
            <button
              type="button"
              onClick={() => setModal({ modo: 'nova' })}
              className="btn-ghost px-3.5 py-1.5 text-sm"
            >
              + Nova conta
            </button>
          </div>
        </div>
        <ContasGrid
          contas={contasNormais}
          loading={loading}
          emptyHint="Nenhuma conta ainda. Clique em “Nova conta” pra começar."
          onEdit={(conta) => setModal({ modo: 'editar', conta })}
        />
      </section>

      {/* Reservas (dinheiro guardado) */}
      <section className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-display font-semibold text-lg tracking-tight text-ink m-0">
            Reservas
          </h2>
          {reservas.length > 0 && (
            <span className="text-[12.5px] text-ink-mute">
              guardado: {formatBRL(totalGuardado)}
            </span>
          )}
        </div>
        {loading ? (
          <div className="card p-4 h-[84px] animate-pulse" />
        ) : reservas.length === 0 ? (
          <div className="card p-6 text-center text-ink-soft text-sm">
            Sem reservas. Crie uma conta do tipo “reserva” pra guardar dinheiro.
          </div>
        ) : (
          <ContasGrid
            contas={reservas}
            loading={false}
            emptyHint=""
            onEdit={(conta) => setModal({ modo: 'editar', conta })}
          />
        )}
      </section>

      {modal.modo !== 'fechado' && (
        <ContaForm
          conta={modal.modo === 'editar' ? modal.conta : null}
          onClose={() => setModal({ modo: 'fechado' })}
          onSaved={() => {
            setModal({ modo: 'fechado' });
            onChanged();
          }}
        />
      )}
    </>
  );
}

function ContasGrid({
  contas,
  loading,
  emptyHint,
  onEdit,
}: {
  contas: Conta[];
  loading: boolean;
  emptyHint: string;
  onEdit: (c: Conta) => void;
}) {
  if (loading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {[0, 1, 2].map((i) => (
          <div key={i} className="card p-4 h-[84px] animate-pulse" />
        ))}
      </div>
    );
  }
  if (contas.length === 0) {
    return emptyHint ? (
      <div className="card p-6 text-center text-ink-soft text-sm">
        {emptyHint}
      </div>
    ) : null;
  }
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
      {contas.map((c) => (
        <button
          key={c.id}
          type="button"
          onClick={() => onEdit(c)}
          className="card p-4 text-left transition-colors hover:border-ink-mute group"
          title="Editar conta"
        >
          <div className="flex items-start justify-between">
            <div className="font-mono uppercase tracking-[0.1em] text-[10px] text-ink-mute mb-1">
              {TIPO_LABEL[c.tipo] ?? c.tipo}
            </div>
            <span className="text-[11px] text-ink-faint opacity-0 group-hover:opacity-100 transition-opacity">
              editar
            </span>
          </div>
          <div className="font-medium text-ink mb-1.5">{c.nome}</div>
          <div className="font-display font-semibold tracking-tight text-xl text-ink leading-none">
            {formatBRL(c.saldo_atual)}
          </div>
        </button>
      ))}
    </div>
  );
}

function ContaForm({
  conta,
  onClose,
  onSaved,
}: {
  conta: Conta | null;
  onClose: () => void;
  onSaved: () => void;
}) {
  const editando = conta !== null;
  const [nome, setNome] = useState(conta?.nome ?? '');
  const [tipo, setTipo] = useState<TipoConta>(
    (conta?.tipo as TipoConta) ?? 'corrente',
  );
  const [saldo, setSaldo] = useState(conta?.saldo_atual ?? '0');
  const [salvando, setSalvando] = useState(false);
  const [excluindo, setExcluindo] = useState(false);
  const [erro, setErro] = useState('');

  async function salvar(e: FormEvent) {
    e.preventDefault();
    setErro('');
    if (!nome.trim()) {
      setErro('Dê um nome pra conta.');
      return;
    }
    setSalvando(true);
    try {
      if (editando && conta) {
        await api.financasAtualizarConta(conta.id, { nome: nome.trim(), tipo });
      } else {
        await api.financasCriarConta({
          nome: nome.trim(),
          tipo,
          saldo_atual: saldo.trim() || '0',
        });
      }
      onSaved();
    } catch (err) {
      setErro(err instanceof ApiError ? err.message : 'Falha ao salvar.');
    } finally {
      setSalvando(false);
    }
  }

  async function excluir() {
    if (!conta) return;
    if (
      !window.confirm(
        `Excluir a conta “${conta.nome}”? As transações ligadas a ela podem ser afetadas.`,
      )
    ) {
      return;
    }
    setErro('');
    setExcluindo(true);
    try {
      await api.financasExcluirConta(conta.id);
      onSaved();
    } catch (err) {
      setErro(err instanceof ApiError ? err.message : 'Falha ao excluir.');
      setExcluindo(false);
    }
  }

  return (
    <Modal
      open
      onClose={onClose}
      title={editando ? 'Editar conta' : 'Nova conta'}
    >
      <form onSubmit={salvar} className="space-y-4">
        <div>
          <label className="block text-[13px] font-medium text-ink-soft mb-1.5">
            Nome
          </label>
          <input
            className="input"
            value={nome}
            onChange={(e) => setNome(e.target.value)}
            placeholder='ex: "Nubank", "Carteira", "VR Caju"'
            autoFocus
          />
        </div>

        <div>
          <label className="block text-[13px] font-medium text-ink-soft mb-1.5">
            Tipo
          </label>
          <select
            className="input"
            value={tipo}
            onChange={(e) => setTipo(e.target.value as TipoConta)}
          >
            {TIPOS.map((t) => (
              <option key={t} value={t}>
                {TIPO_LABEL[t]}
              </option>
            ))}
          </select>
        </div>

        {!editando && (
          <div>
            <label className="block text-[13px] font-medium text-ink-soft mb-1.5">
              Saldo inicial
            </label>
            <input
              className="input"
              value={saldo}
              onChange={(e) => setSaldo(e.target.value)}
              inputMode="decimal"
              placeholder="0,00"
            />
            <p className="text-[11.5px] text-ink-mute mt-1">
              Saldo de abertura. Depois é mantido pelos lançamentos.
            </p>
          </div>
        )}

        {erro && (
          <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded px-3 py-2">
            {erro}
          </div>
        )}

        <div className="flex items-center justify-between gap-3 pt-1">
          {editando ? (
            <button
              type="button"
              onClick={excluir}
              disabled={salvando || excluindo}
              className="text-sm text-red-600 hover:underline disabled:opacity-50"
            >
              {excluindo ? 'Excluindo…' : 'Excluir'}
            </button>
          ) : (
            <span />
          )}
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={onClose}
              className="btn-ghost px-4 py-2 text-sm"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={salvando || excluindo}
              className="btn-primary px-5 py-2 text-sm disabled:opacity-50"
            >
              {salvando ? 'Salvando…' : editando ? 'Salvar' : 'Criar conta'}
            </button>
          </div>
        </div>
      </form>
    </Modal>
  );
}

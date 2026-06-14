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
  | { modo: 'editar'; conta: Conta }
  | { modo: 'guardar'; reserva: Conta };

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
            onGuardar={(reserva) => setModal({ modo: 'guardar', reserva })}
          />
        )}
      </section>

      {(modal.modo === 'nova' || modal.modo === 'editar') && (
        <ContaForm
          conta={modal.modo === 'editar' ? modal.conta : null}
          onClose={() => setModal({ modo: 'fechado' })}
          onSaved={() => {
            setModal({ modo: 'fechado' });
            onChanged();
          }}
        />
      )}

      {modal.modo === 'guardar' && (
        <GuardarReservaModal
          reserva={modal.reserva}
          origens={contasNormais}
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
  onGuardar,
}: {
  contas: Conta[];
  loading: boolean;
  emptyHint: string;
  onEdit: (c: Conta) => void;
  /** Quando presente, mostra "Guardar" no card (aporte na reserva). */
  onGuardar?: (c: Conta) => void;
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
        <div key={c.id} className="card p-4 group">
          <button
            type="button"
            onClick={() => onEdit(c)}
            className="block w-full text-left"
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
            {c.meta && Number(c.meta) > 0 && (
              <MetaProgresso saldo={Number(c.saldo_atual)} meta={Number(c.meta)} />
            )}
          </button>
          {onGuardar && (
            <button
              type="button"
              onClick={() => onGuardar(c)}
              className="btn-ghost mt-3 w-full justify-center py-1.5 text-[13px]"
            >
              + Guardar aqui
            </button>
          )}
        </div>
      ))}
    </div>
  );
}

function GuardarReservaModal({
  reserva,
  origens,
  onClose,
  onSaved,
}: {
  reserva: Conta;
  origens: Conta[];
  onClose: () => void;
  onSaved: () => void;
}) {
  const [valor, setValor] = useState('');
  const [origemId, setOrigemId] = useState(origens[0]?.id ?? '');
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState('');

  async function salvar(e: FormEvent) {
    e.preventDefault();
    setErro('');
    const v = Number(valor.replace(',', '.'));
    if (!Number.isFinite(v) || v <= 0) {
      setErro('Informe um valor maior que zero.');
      return;
    }
    if (!origemId) {
      setErro('Escolha de qual conta sai o dinheiro.');
      return;
    }
    setSalvando(true);
    try {
      await api.financasTransferir({
        origem_conta_id: origemId,
        destino_conta_id: reserva.id,
        valor: String(v),
        descricao: `Guardado em ${reserva.nome}`,
      });
      onSaved();
    } catch (err) {
      setErro(err instanceof ApiError ? err.message : 'Falha ao guardar.');
      setSalvando(false);
    }
  }

  return (
    <Modal open onClose={onClose} title={`Guardar em ${reserva.nome}`}>
      {origens.length === 0 ? (
        <p className="text-sm text-ink-soft m-0">
          Você precisa de outra conta (corrente/dinheiro) pra tirar o dinheiro e
          guardar na reserva.
        </p>
      ) : (
        <form onSubmit={salvar} className="space-y-4">
          <p className="text-[13px] text-ink-soft m-0">
            Move dinheiro de uma conta pra esta reserva. Não conta como
            despesa/receita do mês — é só transferência.
          </p>
          <div>
            <label className="block text-[13px] font-medium text-ink-soft mb-1.5">
              Valor
            </label>
            <input
              className="input"
              value={valor}
              onChange={(e) => setValor(e.target.value)}
              inputMode="decimal"
              placeholder="0,00"
              autoFocus
            />
          </div>
          <div>
            <label className="block text-[13px] font-medium text-ink-soft mb-1.5">
              De qual conta
            </label>
            <select
              className="input"
              value={origemId}
              onChange={(e) => setOrigemId(e.target.value)}
            >
              {origens.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.nome}
                </option>
              ))}
            </select>
          </div>
          {erro && (
            <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded px-3 py-2">
              {erro}
            </div>
          )}
          <div className="flex items-center justify-end gap-2 pt-1">
            <button type="button" onClick={onClose} className="btn-ghost px-4 py-2 text-sm">
              Cancelar
            </button>
            <button
              type="submit"
              disabled={salvando}
              className="btn-primary px-5 py-2 text-sm disabled:opacity-50"
            >
              {salvando ? 'Guardando…' : 'Guardar'}
            </button>
          </div>
        </form>
      )}
    </Modal>
  );
}

function MetaProgresso({ saldo, meta }: { saldo: number; meta: number }) {
  const pct = Math.min(100, Math.max(0, (saldo / meta) * 100));
  const completo = saldo >= meta;
  return (
    <div className="mt-2.5">
      <div className="h-1.5 rounded-full bg-line-soft overflow-hidden">
        <div
          className={`h-full rounded-full ${completo ? 'bg-success' : 'bg-brand'}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <div className="font-mono uppercase tracking-[0.1em] text-[9px] text-ink-mute mt-1">
        {completo ? '🎉 meta atingida' : `${Math.round(pct)}% de ${formatBRL(meta)}`}
      </div>
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
  const [meta, setMeta] = useState(conta?.meta ?? '');
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
    const metaStr =
      tipo === 'reserva' && meta.trim()
        ? String(Number(meta.replace(',', '.')))
        : null;
    if (metaStr !== null && (!Number.isFinite(Number(metaStr)) || Number(metaStr) < 0)) {
      setErro('Meta inválida.');
      return;
    }
    setSalvando(true);
    try {
      if (editando && conta) {
        await api.financasAtualizarConta(conta.id, {
          nome: nome.trim(), tipo, meta: metaStr,
        });
      } else {
        await api.financasCriarConta({
          nome: nome.trim(),
          tipo,
          saldo_atual: saldo.trim() || '0',
          meta: metaStr,
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

        {tipo === 'reserva' && (
          <div>
            <label className="block text-[13px] font-medium text-ink-soft mb-1.5">
              Meta / objetivo (opcional)
            </label>
            <input
              className="input"
              value={meta}
              onChange={(e) => setMeta(e.target.value)}
              inputMode="decimal"
              placeholder='ex: 5000 (a reserva mostra uma barra de progresso)'
            />
            <p className="text-[11.5px] text-ink-mute mt-1">
              Quanto você quer juntar nessa reserva (ex.: viagem). Deixe vazio pra
              não ter meta.
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

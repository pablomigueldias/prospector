import { useState, type FormEvent } from 'react';

import { Modal } from '@/components/Modal';
import { useCartaoFaturas, useCartoes } from '@/hooks/useFinancas';
import { api } from '@/lib/api';
import { formatBRL } from '@/lib/format';
import { ApiError, type Cartao, type Fatura } from '@/lib/types';

type ModalState =
  | { modo: 'fechado' }
  | { modo: 'novo' }
  | { modo: 'editar'; cartao: Cartao };

export function CartoesSection() {
  const { cartoes, loading, refetch } = useCartoes();
  const [modal, setModal] = useState<ModalState>({ modo: 'fechado' });

  return (
    <section className="mb-8">
      <div className="flex items-center justify-between mb-4">
        <h2 className="font-display font-semibold text-lg tracking-tight text-ink m-0">
          Cartões
        </h2>
        <button
          type="button"
          onClick={() => setModal({ modo: 'novo' })}
          className="btn-ghost px-3.5 py-1.5 text-sm"
        >
          + Novo cartão
        </button>
      </div>

      {loading ? (
        <div className="card p-4 h-[120px] animate-pulse" />
      ) : cartoes.length === 0 ? (
        <div className="card p-6 text-center text-ink-soft text-sm">
          Nenhum cartão cadastrado. Clique em “Novo cartão” pra começar.
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
          {cartoes.map((c) => (
            <CartaoCard
              key={c.id}
              cartao={c}
              onEditar={() => setModal({ modo: 'editar', cartao: c })}
            />
          ))}
        </div>
      )}

      {modal.modo !== 'fechado' && (
        <CartaoForm
          cartao={modal.modo === 'editar' ? modal.cartao : null}
          onClose={() => setModal({ modo: 'fechado' })}
          onSaved={() => {
            setModal({ modo: 'fechado' });
            void refetch();
          }}
        />
      )}
    </section>
  );
}

function CartaoCard({
  cartao,
  onEditar,
}: {
  cartao: Cartao;
  onEditar: () => void;
}) {
  const { dados, loading } = useCartaoFaturas(cartao.id);
  const abertas = (dados?.faturas ?? []).filter((f) => f.status !== 'paga');

  return (
    <div className={`card p-4 ${!cartao.ativo ? 'opacity-60' : ''}`}>
      <div className="flex items-baseline justify-between mb-3">
        <button
          type="button"
          onClick={onEditar}
          className="text-left group"
          title="Editar cartão"
        >
          <div className="font-medium text-ink flex items-center gap-2">
            {cartao.nome}
            {!cartao.ativo && (
              <span className="text-[10px] uppercase tracking-wide text-ink-mute border border-line rounded px-1 py-0.5">
                inativo
              </span>
            )}
            <span className="text-[11px] text-ink-faint opacity-0 group-hover:opacity-100 transition-opacity">
              editar
            </span>
          </div>
          <div className="font-mono uppercase tracking-[0.1em] text-[10px] text-ink-mute">
            {cartao.bandeira || 'cartão'} · fecha dia {cartao.dia_fechamento} · vence dia{' '}
            {cartao.dia_vencimento}
          </div>
        </button>
        {dados && Number(dados.total_juros) > 0 && (
          <div className="text-right">
            <div className="font-mono uppercase tracking-[0.1em] text-[9px] text-ink-mute">
              juros
            </div>
            <div className="text-brand-deep text-sm font-medium">
              {formatBRL(dados.total_juros)}
            </div>
          </div>
        )}
      </div>

      <div className="flex items-baseline gap-1.5 mb-3">
        <span className="font-mono uppercase tracking-[0.1em] text-[10px] text-ink-mute">
          em aberto
        </span>
        <span className="font-display font-semibold tracking-tight text-lg text-ink">
          {loading ? '…' : formatBRL(dados?.total_em_aberto)}
        </span>
        {cartao.limite && (
          <span className="ml-auto text-[11.5px] text-ink-mute">
            limite {formatBRL(cartao.limite)}
          </span>
        )}
      </div>

      {abertas.length > 0 && (
        <ul className="m-0 p-0 list-none flex flex-col gap-1.5 border-t border-line-soft pt-3">
          {abertas.slice(0, 4).map((f) => (
            <FaturaRow key={f.id} fatura={f} />
          ))}
        </ul>
      )}
    </div>
  );
}

function FaturaRow({ fatura }: { fatura: Fatura }) {
  return (
    <li className="flex items-center justify-between text-sm">
      <span className="text-ink-soft">
        vence {fatura.vencimento}
        <span className="ml-2 font-mono text-[10px] uppercase tracking-wide text-ink-mute">
          {fatura.status}
        </span>
      </span>
      <span className="text-ink tabular-nums">{formatBRL(fatura.valor_total)}</span>
    </li>
  );
}

function CartaoForm({
  cartao,
  onClose,
  onSaved,
}: {
  cartao: Cartao | null;
  onClose: () => void;
  onSaved: () => void;
}) {
  const editando = cartao !== null;
  const [nome, setNome] = useState(cartao?.nome ?? '');
  const [bandeira, setBandeira] = useState(cartao?.bandeira ?? '');
  const [fechamento, setFechamento] = useState(String(cartao?.dia_fechamento ?? 1));
  const [vencimento, setVencimento] = useState(String(cartao?.dia_vencimento ?? 10));
  const [limite, setLimite] = useState(cartao?.limite ?? '');
  const [ativo, setAtivo] = useState(cartao?.ativo ?? true);
  const [salvando, setSalvando] = useState(false);
  const [excluindo, setExcluindo] = useState(false);
  const [erro, setErro] = useState('');

  function diaValido(s: string): number | null {
    const n = Number(s);
    return Number.isInteger(n) && n >= 1 && n <= 31 ? n : null;
  }

  async function salvar(e: FormEvent) {
    e.preventDefault();
    setErro('');
    if (!nome.trim()) return setErro('Dê um nome pro cartão.');
    const fech = diaValido(fechamento);
    const venc = diaValido(vencimento);
    if (fech === null) return setErro('Dia de fechamento entre 1 e 31.');
    if (venc === null) return setErro('Dia de vencimento entre 1 e 31.');
    const limiteStr = limite.trim()
      ? String(Number(limite.replace(',', '.')))
      : null;
    if (limiteStr !== null && !Number.isFinite(Number(limiteStr))) {
      return setErro('Limite inválido.');
    }

    setSalvando(true);
    try {
      if (editando && cartao) {
        await api.financasAtualizarCartao(cartao.id, {
          nome: nome.trim(),
          bandeira: bandeira.trim() || null,
          dia_fechamento: fech,
          dia_vencimento: venc,
          limite: limiteStr,
          ativo,
        });
      } else {
        await api.financasCriarCartao({
          nome: nome.trim(),
          bandeira: bandeira.trim() || null,
          dia_fechamento: fech,
          dia_vencimento: venc,
          limite: limiteStr,
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
    if (!cartao) return;
    if (
      !window.confirm(
        `Excluir o cartão “${cartao.nome}”? As faturas dele são removidas junto. ` +
          'Compras parceladas continuam, sem o vínculo.',
      )
    ) {
      return;
    }
    setErro('');
    setExcluindo(true);
    try {
      await api.financasExcluirCartao(cartao.id);
      onSaved();
    } catch (err) {
      setErro(err instanceof ApiError ? err.message : 'Falha ao excluir.');
      setExcluindo(false);
    }
  }

  return (
    <Modal open onClose={onClose} title={editando ? 'Editar cartão' : 'Novo cartão'}>
      <form onSubmit={salvar} className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-[13px] font-medium text-ink-soft mb-1.5">
              Nome
            </label>
            <input
              className="input"
              value={nome}
              onChange={(e) => setNome(e.target.value)}
              placeholder="ex: Nubank"
              autoFocus
            />
          </div>
          <div>
            <label className="block text-[13px] font-medium text-ink-soft mb-1.5">
              Bandeira (opcional)
            </label>
            <input
              className="input"
              value={bandeira}
              onChange={(e) => setBandeira(e.target.value)}
              placeholder="ex: Mastercard"
            />
          </div>
        </div>

        <div className="grid grid-cols-3 gap-3">
          <div>
            <label className="block text-[13px] font-medium text-ink-soft mb-1.5">
              Fecha dia
            </label>
            <input
              className="input"
              value={fechamento}
              onChange={(e) => setFechamento(e.target.value)}
              inputMode="numeric"
            />
          </div>
          <div>
            <label className="block text-[13px] font-medium text-ink-soft mb-1.5">
              Vence dia
            </label>
            <input
              className="input"
              value={vencimento}
              onChange={(e) => setVencimento(e.target.value)}
              inputMode="numeric"
            />
          </div>
          <div>
            <label className="block text-[13px] font-medium text-ink-soft mb-1.5">
              Limite
            </label>
            <input
              className="input"
              value={limite}
              onChange={(e) => setLimite(e.target.value)}
              inputMode="decimal"
              placeholder="0,00"
            />
          </div>
        </div>

        {editando && (
          <label className="flex items-center gap-2 text-sm text-ink-soft">
            <input
              type="checkbox"
              checked={ativo}
              onChange={(e) => setAtivo(e.target.checked)}
            />
            Ativo
          </label>
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
              {salvando ? 'Salvando…' : editando ? 'Salvar' : 'Criar cartão'}
            </button>
          </div>
        </div>
      </form>
    </Modal>
  );
}

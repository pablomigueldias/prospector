import { useMemo, useState, type FormEvent } from 'react';

import { Modal } from '@/components/Modal';
import { useCartoes, useCategorias, useRecorrencias } from '@/hooks/useFinancas';
import { api } from '@/lib/api';
import { achatarCategorias } from '@/lib/categorias';
import { formatBRL } from '@/lib/format';
import {
  ApiError,
  type Conta,
  type FormaPagamento,
  type Recorrencia,
} from '@/lib/types';

interface Props {
  contas: Conta[];
  /** Recarrega resumo/contas do dashboard (recorrência não mexe em saldo, mas
   *  mantém o padrão das outras seções). */
  onMutate?: () => void;
}

type ModalState =
  | { modo: 'fechado' }
  | { modo: 'nova' }
  | { modo: 'editar'; rec: Recorrencia };

export function RecorrenciasSection({ contas, onMutate }: Props) {
  const { recorrencias, loading, refetch } = useRecorrencias();
  const [modal, setModal] = useState<ModalState>({ modo: 'fechado' });

  const recarregar = () => {
    void refetch();
    onMutate?.();
  };

  const totalMensal = recorrencias
    .filter((r) => r.tipo === 'despesa' && r.ativa)
    .reduce((acc, r) => acc + Number(r.valor_estimado), 0);

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
            <button
              key={r.id}
              type="button"
              onClick={() => setModal({ modo: 'editar', rec: r })}
              className="w-full flex items-center gap-3 px-4 py-2.5 text-left hover:bg-bg-alt/40 transition-colors group"
              title="Editar"
            >
              <div className="w-12 shrink-0 text-center">
                <div className="font-mono text-[10px] text-ink-mute uppercase tracking-wide">
                  dia
                </div>
                <div className="font-display font-semibold text-ink leading-none">
                  {r.dia_vencimento}
                </div>
              </div>
              <div className="min-w-0 flex-1">
                <div className="text-sm text-ink truncate">
                  {r.descricao}
                  {!r.ativa && (
                    <span className="ml-2 text-[10px] uppercase tracking-wide text-ink-mute border border-line rounded px-1 py-0.5">
                      pausada
                    </span>
                  )}
                </div>
                <div className="text-[11.5px] text-ink-mute">
                  {r.tipo === 'despesa' ? 'Despesa' : 'Receita'} · {r.frequencia}
                </div>
              </div>
              <div
                className={`shrink-0 font-display font-semibold tracking-tight text-sm ${
                  r.tipo === 'despesa' ? 'text-ink' : 'text-success'
                } ${!r.ativa ? 'opacity-50' : ''}`}
              >
                {r.tipo === 'despesa' ? '−' : '+'}
                {formatBRL(r.valor_estimado)}
              </div>
              <span className="shrink-0 text-[11px] text-ink-faint opacity-0 group-hover:opacity-100 transition-opacity">
                editar
              </span>
            </button>
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
    </section>
  );
}

function RecorrenciaForm({
  rec,
  contas,
  onClose,
  onSaved,
}: {
  rec: Recorrencia | null;
  contas: Conta[];
  onClose: () => void;
  onSaved: () => void;
}) {
  const editando = rec !== null;
  const { arvore } = useCategorias();
  const categorias = useMemo(() => achatarCategorias(arvore), [arvore]);

  const [descricao, setDescricao] = useState(rec?.descricao ?? '');
  const [tipo, setTipo] = useState<'despesa' | 'receita'>(
    (rec?.tipo as 'despesa' | 'receita') ?? 'despesa',
  );
  const [valor, setValor] = useState(rec?.valor_estimado ?? '');
  const [dia, setDia] = useState(String(rec?.dia_vencimento ?? 5));
  const [contaId, setContaId] = useState(rec?.conta_id ?? '');
  const [categoriaId, setCategoriaId] = useState(rec?.categoria_id ?? '');
  const [forma, setForma] = useState<FormaPagamento>(
    (rec?.forma_pagamento as FormaPagamento) ?? 'conta',
  );
  const [cartaoId, setCartaoId] = useState(rec?.cartao_id ?? '');
  const { cartoes } = useCartoes();
  const [ativa, setAtiva] = useState(rec?.ativa ?? true);
  const [salvando, setSalvando] = useState(false);
  const [excluindo, setExcluindo] = useState(false);
  const [erro, setErro] = useState('');

  async function salvar(e: FormEvent) {
    e.preventDefault();
    setErro('');
    if (!descricao.trim()) return setErro('Descreva a conta fixa.');
    const valorNum = Number(valor.replace(',', '.'));
    if (!Number.isFinite(valorNum) || valorNum <= 0) {
      return setErro('Informe um valor maior que zero.');
    }
    const diaNum = Number(dia);
    if (!Number.isInteger(diaNum) || diaNum < 1 || diaNum > 31) {
      return setErro('Dia de vencimento entre 1 e 31.');
    }
    if (forma === 'cartao' && !cartaoId) {
      return setErro('Escolha o cartão onde essa conta é cobrada.');
    }

    setSalvando(true);
    try {
      const cartaoFinal = forma === 'cartao' ? cartaoId || null : null;
      if (editando && rec) {
        await api.financasAtualizarRecorrencia(rec.id, {
          descricao: descricao.trim(),
          tipo,
          valor_estimado: String(valorNum),
          dia_vencimento: diaNum,
          conta_id: contaId || null,
          categoria_id: categoriaId || null,
          forma_pagamento: forma,
          cartao_id: cartaoFinal,
          ativa,
        });
      } else {
        await api.financasCriarRecorrencia({
          descricao: descricao.trim(),
          tipo,
          valor_estimado: String(valorNum),
          dia_vencimento: diaNum,
          conta_id: contaId || null,
          categoria_id: categoriaId || null,
          forma_pagamento: forma,
          cartao_id: cartaoFinal,
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
    if (!rec) return;
    if (
      !window.confirm(
        `Excluir a conta fixa “${rec.descricao}”? As transações já geradas por ` +
          'ela continuam, só perdem o vínculo.',
      )
    ) {
      return;
    }
    setErro('');
    setExcluindo(true);
    try {
      await api.financasExcluirRecorrencia(rec.id);
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
      title={editando ? 'Editar conta fixa' : 'Nova conta fixa'}
    >
      <form onSubmit={salvar} className="space-y-4">
        <div className="grid grid-cols-2 gap-2">
          {(['despesa', 'receita'] as const).map((t) => (
            <button
              key={t}
              type="button"
              onClick={() => setTipo(t)}
              className={`py-2 rounded-lg border text-sm font-medium transition-colors ${
                tipo === t
                  ? 'border-brand bg-brand-soft text-brand-ink'
                  : 'border-line text-ink-soft hover:border-ink-mute'
              }`}
            >
              {t === 'despesa' ? 'Despesa fixa' : 'Receita fixa'}
            </button>
          ))}
        </div>

        <div>
          <label className="block text-[13px] font-medium text-ink-soft mb-1.5">
            Descrição
          </label>
          <input
            className="input"
            value={descricao}
            onChange={(e) => setDescricao(e.target.value)}
            placeholder={tipo === 'despesa' ? 'ex: Aluguel, Netflix' : 'ex: Salário'}
            autoFocus
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-[13px] font-medium text-ink-soft mb-1.5">
              Valor estimado
            </label>
            <input
              className="input"
              value={valor}
              onChange={(e) => setValor(e.target.value)}
              inputMode="decimal"
              placeholder="0,00"
            />
          </div>
          <div>
            <label className="block text-[13px] font-medium text-ink-soft mb-1.5">
              Dia do vencimento
            </label>
            <input
              className="input"
              value={dia}
              onChange={(e) => setDia(e.target.value)}
              inputMode="numeric"
              placeholder="5"
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-[13px] font-medium text-ink-soft mb-1.5">
              Conta (opcional)
            </label>
            <select
              className="input"
              value={contaId}
              onChange={(e) => setContaId(e.target.value)}
            >
              <option value="">Não definir</option>
              {contas.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.nome}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-[13px] font-medium text-ink-soft mb-1.5">
              Categoria (opcional)
            </label>
            <select
              className="input"
              value={categoriaId}
              onChange={(e) => setCategoriaId(e.target.value)}
            >
              <option value="">Sem categoria</option>
              {categorias.map((c) => (
                <option key={c.id} value={c.id}>
                  {`${'  '.repeat(c.depth)}${c.nome}`}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div>
          <label className="block text-[13px] font-medium text-ink-soft mb-1.5">
            Forma de pagamento
          </label>
          <div className="grid grid-cols-3 gap-2">
            {(
              [
                ['conta', 'Conta'],
                ['cartao', 'Cartão'],
                ['boleto', 'Boleto'],
              ] as const
            ).map(([f, rotulo]) => (
              <button
                key={f}
                type="button"
                onClick={() => setForma(f)}
                className={`py-2 rounded-lg border text-sm font-medium transition-colors ${
                  forma === f
                    ? 'border-brand bg-brand-soft text-brand-ink'
                    : 'border-line text-ink-soft hover:border-ink-mute'
                }`}
              >
                {rotulo}
              </button>
            ))}
          </div>
          {forma === 'cartao' && (
            <select
              className="input mt-2"
              value={cartaoId}
              onChange={(e) => setCartaoId(e.target.value)}
            >
              <option value="">Escolha o cartão…</option>
              {cartoes.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.nome}
                </option>
              ))}
            </select>
          )}
          <p className="text-[12px] text-ink-mute mt-1.5 m-0">
            {forma === 'cartao'
              ? 'Ao marcar paga, vira uma compra na fatura desse cartão.'
              : forma === 'boleto'
                ? 'Paga por boleto — pode ligar ao boleto importado do mês.'
                : 'Débito direto na conta ao marcar como paga.'}
          </p>
        </div>

        {editando && (
          <label className="flex items-center gap-2 text-sm text-ink-soft">
            <input
              type="checkbox"
              checked={ativa}
              onChange={(e) => setAtiva(e.target.checked)}
            />
            Ativa (gera previstas todo mês)
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
              {salvando ? 'Salvando…' : editando ? 'Salvar' : 'Criar'}
            </button>
          </div>
        </div>
      </form>
    </Modal>
  );
}

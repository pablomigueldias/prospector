import { useMemo, useState, type FormEvent } from 'react';

import { Modal } from '@/components/Modal';
import { useFetch } from '@/hooks/useFetch';
import { useCartoes, useCategorias, useRecorrencias } from '@/hooks/useFinancas';
import { api } from '@/lib/api';
import { achatarCategorias } from '@/lib/categorias';
import { formatBRL } from '@/lib/format';
import {
  ApiError,
  type Conta,
  type FormaPagamento,
  type Recorrencia,
  type RecorrenciaStatusItem,
  type RecorrenciaStatusResponse,
} from '@/lib/types';

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
        <PagarMesModal
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

const BADGE: Record<
  RecorrenciaStatusItem['situacao'],
  { texto: string; cls: string } | null
> = {
  paga: { texto: '✓ pago', cls: 'text-success border-success/40' },
  lancada_cartao: { texto: 'na fatura', cls: 'text-brand-deep border-brand/40' },
  prevista: { texto: 'a pagar', cls: 'text-ink-soft border-line' },
  atrasada: { texto: 'vencida', cls: 'text-red-600 border-red-300' },
  nenhuma: null,
};

function RecorrenciaRow({
  rec,
  situacao,
  onEditar,
  onMarcar,
}: {
  rec: Recorrencia;
  situacao: RecorrenciaStatusItem['situacao'];
  onEditar: () => void;
  onMarcar: () => void;
}) {
  const badge = BADGE[situacao];
  const feito = situacao === 'paga' || situacao === 'lancada_cartao';
  const acaoLabel = rec.forma_pagamento === 'cartao' ? 'Lançar' : 'Marcar pago';

  return (
    <div className="flex items-center gap-3 px-4 py-2.5 hover:bg-bg-alt/40 transition-colors group">
      <button
        type="button"
        onClick={onEditar}
        className="flex items-center gap-3 flex-1 min-w-0 text-left"
        title="Editar"
      >
        <div className="w-12 shrink-0 text-center">
          <div className="font-mono text-[10px] text-ink-mute uppercase tracking-wide">
            dia
          </div>
          <div className="font-display font-semibold text-ink leading-none">
            {rec.dia_vencimento}
          </div>
        </div>
        <div className="min-w-0 flex-1">
          <div className="text-sm text-ink truncate flex items-center gap-2">
            {rec.descricao}
            {!rec.ativa && (
              <span className="text-[10px] uppercase tracking-wide text-ink-mute border border-line rounded px-1 py-0.5">
                pausada
              </span>
            )}
            {badge && (
              <span
                className={`text-[10px] uppercase tracking-wide rounded border px-1 py-0.5 ${badge.cls}`}
              >
                {badge.texto}
              </span>
            )}
          </div>
          <div className="text-[11.5px] text-ink-mute">
            {rec.tipo === 'despesa' ? 'Despesa' : 'Receita'} ·{' '}
            {rec.forma_pagamento === 'cartao'
              ? 'cartão'
              : rec.forma_pagamento === 'boleto'
                ? 'boleto'
                : 'conta'}
          </div>
        </div>
      </button>

      <div
        className={`shrink-0 font-display font-semibold tracking-tight text-sm ${
          rec.tipo === 'despesa' ? 'text-ink' : 'text-success'
        } ${!rec.ativa ? 'opacity-50' : ''}`}
      >
        {rec.tipo === 'despesa' ? '−' : '+'}
        {formatBRL(rec.valor_estimado)}
      </div>

      {rec.ativa && !feito && (
        <button
          type="button"
          onClick={onMarcar}
          className="shrink-0 btn-ghost px-2.5 py-1 text-[12px]"
          title={
            rec.forma_pagamento === 'cartao'
              ? 'Lançar na fatura do cartão deste mês'
              : 'Marcar como paga neste mês'
          }
        >
          {acaoLabel}
        </button>
      )}
    </div>
  );
}

function PagarMesModal({
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

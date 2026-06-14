import { useMemo, useState, type FormEvent } from 'react';

import { Modal } from '@/components/Modal';
import { useFetch } from '@/hooks/useFetch';
import {
  useCartaoFaturas,
  useCartoes,
  useCategorias,
  useContas,
  useProjecaoCartoes,
} from '@/hooks/useFinancas';
import { api } from '@/lib/api';
import { achatarCategorias } from '@/lib/categorias';
import { formatBRL, formatMesAno } from '@/lib/format';
import {
  ApiError,
  type Cartao,
  type Compra,
  type Fatura,
  type FaturaExtrato,
  type ProjecaoFaturas,
} from '@/lib/types';

type ModalState =
  | { modo: 'fechado' }
  | { modo: 'novo' }
  | { modo: 'editar'; cartao: Cartao };

export function CartoesSection() {
  const { cartoes, loading, refetch } = useCartoes();
  const [modal, setModal] = useState<ModalState>({ modo: 'fechado' });
  // Bumpa quando um card muda (compra/estorno/pagar) pra a projeção atualizar.
  const [mutacao, setMutacao] = useState(0);
  const bump = () => setMutacao((n) => n + 1);
  const { projecao } = useProjecaoCartoes(6, mutacao);

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
        <>
          {projecao && projecao.meses.length > 0 && <ProjecaoBlock projecao={projecao} />}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
            {cartoes.map((c) => (
              <CartaoCard
                key={c.id}
                cartao={c}
                onEditar={() => setModal({ modo: 'editar', cartao: c })}
                onMutou={bump}
              />
            ))}
          </div>
        </>
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

function ProjecaoBlock({ projecao }: { projecao: ProjecaoFaturas }) {
  const maximo = Math.max(...projecao.meses.map((m) => Number(m.total)), 1);
  return (
    <div className="card p-4 mb-3">
      <div className="flex items-baseline justify-between mb-3">
        <h3 className="font-mono uppercase tracking-[0.1em] text-[10px] text-ink-mute m-0">
          comprometido nos próximos meses
        </h3>
        <span className="text-[12px] text-ink-soft">
          total{' '}
          <span className="font-display font-semibold text-ink">
            {formatBRL(projecao.total)}
          </span>
        </span>
      </div>
      <ul className="m-0 p-0 list-none flex items-end gap-3 min-h-[88px]">
        {projecao.meses.map((m) => {
          const [a, mes] = m.mes_referencia.split('-').map(Number);
          const altura = Math.max(6, Math.round((Number(m.total) / maximo) * 56));
          return (
            <li key={m.mes_referencia} className="flex-1 flex flex-col items-center justify-end gap-1.5">
              <span className="text-[11px] tabular-nums text-ink-soft">
                {formatBRL(m.total)}
              </span>
              <div
                className="w-full max-w-[40px] rounded-t bg-brand"
                style={{ height: `${altura}px` }}
                title={`${formatMesAno(a, mes)}: ${formatBRL(m.total)}`}
              />
              <span className="font-mono uppercase tracking-[0.08em] text-[9px] text-ink-mute">
                {a && mes ? formatMesAno(a, mes) : m.mes_referencia}
              </span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

function CartaoCard({
  cartao,
  onEditar,
  onMutou,
}: {
  cartao: Cartao;
  onEditar: () => void;
  /** Avisa o pai que algo mudou (compra/estorno/pagamento) pra a projeção atualizar. */
  onMutou?: () => void;
}) {
  const { dados, loading, refetch } = useCartaoFaturas(cartao.id);
  const recarregar = () => {
    void refetch();
    onMutou?.();
  };
  const [comprando, setComprando] = useState(false);
  const [faturaAberta, setFaturaAberta] = useState<Fatura | null>(null);
  const [pagarDireto, setPagarDireto] = useState(false);
  const abertas = (dados?.faturas ?? []).filter((f) => f.status !== 'paga');
  // Faturas vêm em ordem decrescente (mês mais novo primeiro); a que se paga
  // agora é a mais antiga em aberto (vencendo/vencida) — a última da lista.
  const faturaAPagar = abertas.length > 0 ? abertas[abertas.length - 1] : null;

  // Limite / disponível: o "em aberto" já soma todas as faturas não pagas
  // (inclui as parcelas dos próximos meses), então é o comprometido.
  const limite = cartao.limite ? Number(cartao.limite) : null;
  const emAberto = Number(dados?.total_em_aberto ?? 0);
  const disponivel = limite != null ? limite - emAberto : null;
  const usoPct =
    limite != null && limite > 0
      ? Math.min(100, Math.max(0, (emAberto / limite) * 100))
      : null;

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

      <div className="flex items-baseline gap-1.5 mb-1">
        <span className="font-mono uppercase tracking-[0.1em] text-[10px] text-ink-mute">
          em aberto
        </span>
        <span className="font-display font-semibold tracking-tight text-lg text-ink">
          {loading ? '…' : formatBRL(emAberto)}
        </span>
        {disponivel != null && (
          <span
            className={`ml-auto text-[11.5px] ${
              disponivel < 0 ? 'text-red-600' : 'text-ink-mute'
            }`}
          >
            {disponivel < 0 ? 'estourou ' : 'disponível '}
            {formatBRL(Math.abs(disponivel))}
          </span>
        )}
      </div>

      {usoPct != null && (
        <div className="mb-3">
          <div className="h-1.5 rounded-full bg-line-soft overflow-hidden">
            <div
              className={`h-full rounded-full ${
                usoPct >= 100 ? 'bg-red-500' : usoPct >= 80 ? 'bg-brand-deep' : 'bg-brand'
              }`}
              style={{ width: `${usoPct}%` }}
            />
          </div>
          <div className="font-mono uppercase tracking-[0.1em] text-[9px] text-ink-mute mt-1">
            {Math.round(usoPct)}% de {formatBRL(limite!)}
          </div>
        </div>
      )}

      {abertas.length > 0 && (
        <div className="border-t border-line-soft pt-3">
          <div className="font-mono uppercase tracking-[0.1em] text-[9px] text-ink-mute mb-1.5">
            próximas faturas
          </div>
          <ul className="m-0 p-0 list-none flex flex-col gap-1.5">
            {abertas.slice(0, 4).map((f) => (
              <FaturaRow
                key={f.id}
                fatura={f}
                onAbrir={() => {
                  setPagarDireto(false);
                  setFaturaAberta(f);
                }}
              />
            ))}
          </ul>
        </div>
      )}

      <div className="flex items-center justify-end gap-2 mt-3 pt-3 border-t border-line-soft">
        {faturaAPagar && (
          <button
            type="button"
            onClick={() => {
              setPagarDireto(true);
              setFaturaAberta(faturaAPagar);
            }}
            className="btn-ghost px-3 py-1 text-[13px]"
            title="Pagar a fatura em aberto (boleto/pix)"
          >
            Pagar fatura
          </button>
        )}
        <button
          type="button"
          onClick={() => setComprando(true)}
          className="btn-ghost px-3 py-1 text-[13px]"
        >
          + Compra
        </button>
      </div>

      {comprando && (
        <CompraForm
          cartao={cartao}
          onClose={() => setComprando(false)}
          onSaved={() => {
            setComprando(false);
            recarregar();
          }}
        />
      )}

      {faturaAberta && (
        <FaturaExtratoModal
          cartaoId={cartao.id}
          fatura={faturaAberta}
          iniciarPagando={pagarDireto}
          onClose={() => setFaturaAberta(null)}
          onPaid={() => {
            setFaturaAberta(null);
            recarregar();
          }}
        />
      )}
    </div>
  );
}

function FaturaRow({ fatura, onAbrir }: { fatura: Fatura; onAbrir: () => void }) {
  // mes_referencia vem como "YYYY-MM-01" → rótulo "Mês/Ano".
  const [a, m] = fatura.mes_referencia.split('-').map(Number);
  const rotuloMes = a && m ? formatMesAno(a, m) : fatura.mes_referencia;
  return (
    <li>
      <button
        type="button"
        onClick={onAbrir}
        className="w-full flex items-center justify-between text-sm text-left hover:bg-line-soft/40 rounded px-1 -mx-1 py-0.5 transition-colors"
        title="Ver o extrato da fatura"
      >
        <span className="text-ink-soft">
          {rotuloMes}
          <span className="ml-2 text-[11px] text-ink-mute">vence {fatura.vencimento}</span>
        </span>
        <span className="text-ink tabular-nums">{formatBRL(fatura.valor_total)}</span>
      </button>
    </li>
  );
}

function FaturaExtratoModal({
  cartaoId,
  fatura,
  iniciarPagando = false,
  onClose,
  onPaid,
}: {
  cartaoId: string;
  fatura: Fatura;
  iniciarPagando?: boolean;
  onClose: () => void;
  onPaid: () => void;
}) {
  const { data, loading, error } = useFetch<FaturaExtrato>(
    () => api.financasFaturaExtrato(cartaoId, fatura.id),
    [cartaoId, fatura.id],
  );
  const { contas } = useContas(true);
  const [pagando, setPagando] = useState(iniciarPagando && fatura.status !== 'paga');
  const [contaId, setContaId] = useState('');
  const [dataPg, setDataPg] = useState(() => new Date().toISOString().slice(0, 10));
  const [valorPago, setValorPago] = useState('');
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState('');
  const [estornando, setEstornando] = useState<string | null>(null);
  const [verCompra, setVerCompra] = useState<string | null>(null);
  const [compraDet, setCompraDet] = useState<Compra | null>(null);
  const [carregandoCompra, setCarregandoCompra] = useState(false);

  const paga = fatura.status === 'paga';

  async function alternarParcelas(compraId: string) {
    if (verCompra === compraId) {
      setVerCompra(null);
      return;
    }
    setVerCompra(compraId);
    setCompraDet(null);
    setCarregandoCompra(true);
    try {
      setCompraDet(await api.financasCompra(compraId));
    } catch {
      setCompraDet(null);
    } finally {
      setCarregandoCompra(false);
    }
  }

  async function estornar(compraId: string, descricao: string, totalParcelas: number) {
    const aviso =
      totalParcelas > 1
        ? `Estornar a compra “${descricao}” inteira? As ${totalParcelas} parcelas (deste e dos próximos meses) somem e o valor sai das faturas.`
        : `Estornar a compra “${descricao}”? Ela sai da fatura.`;
    if (!window.confirm(aviso)) return;
    setErro('');
    setEstornando(compraId);
    try {
      await api.financasExcluirCompra(compraId);
      onPaid(); // fecha + recarrega o card (parcelas podem estar em vários meses)
    } catch (err) {
      setErro(err instanceof ApiError ? err.message : 'Falha ao estornar a compra.');
      setEstornando(null);
    }
  }

  async function pagar() {
    setErro('');
    if (!contaId) return setErro('Escolha a conta que pagou a fatura.');
    const valorStr = valorPago.trim()
      ? String(Number(valorPago.replace(',', '.')))
      : null;
    if (valorStr !== null && (!Number.isFinite(Number(valorStr)) || Number(valorStr) <= 0)) {
      return setErro('Valor pago inválido.');
    }
    setSalvando(true);
    try {
      await api.financasPagarFatura(cartaoId, fatura.id, {
        conta_id: contaId,
        data_pagamento: dataPg || null,
        valor_pago: valorStr,
      });
      onPaid();
    } catch (err) {
      setErro(err instanceof ApiError ? err.message : 'Falha ao pagar a fatura.');
      setSalvando(false);
    }
  }

  return (
    <Modal open onClose={onClose} title={`Fatura · vence ${fatura.vencimento}`}>
      {loading ? (
        <div className="h-24 animate-pulse" />
      ) : error ? (
        <div className="text-sm text-red-600">Falha ao carregar o extrato.</div>
      ) : (
        <div className="space-y-3">
          {!data || data.itens.length === 0 ? (
            <p className="text-sm text-ink-mute m-0">
              Nenhuma parcela nesta fatura ainda.
            </p>
          ) : (
            <ul className="m-0 p-0 list-none flex flex-col divide-y divide-line-soft">
              {data.itens.map((it) => (
                <li key={it.parcela_id} className="py-2 text-sm group">
                  <div className="flex items-center justify-between gap-3">
                    <div className="min-w-0">
                      <div className="text-ink truncate">{it.descricao}</div>
                      <div className="font-mono uppercase tracking-[0.08em] text-[10px] text-ink-mute">
                        {it.numero}/{it.total_parcelas}
                        {it.categoria_nome ? ` · ${it.categoria_nome}` : ''}
                        {Number(it.valor_juros) > 0
                          ? ` · juros ${formatBRL(it.valor_juros)}`
                          : ''}
                      </div>
                    </div>
                    <span className="text-ink tabular-nums shrink-0">
                      {formatBRL(it.valor)}
                    </span>
                    {it.total_parcelas > 1 && (
                      <button
                        type="button"
                        onClick={() => alternarParcelas(it.compra_id)}
                        className="shrink-0 text-ink-faint hover:text-brand text-sm px-1 transition-colors"
                        title="Ver todas as parcelas desta compra"
                        aria-label="Ver parcelas da compra"
                      >
                        {verCompra === it.compra_id ? '▾' : 'ⓘ'}
                      </button>
                    )}
                    {!paga && (
                      <button
                        type="button"
                        onClick={() => estornar(it.compra_id, it.descricao, it.total_parcelas)}
                        disabled={estornando === it.compra_id}
                        className="shrink-0 text-ink-faint hover:text-red-600 text-sm px-1 opacity-0 group-hover:opacity-100 transition-opacity disabled:opacity-50"
                        title={
                          it.total_parcelas > 1
                            ? 'Estornar a compra inteira (todas as parcelas)'
                            : 'Estornar a compra'
                        }
                        aria-label="Estornar a compra"
                      >
                        {estornando === it.compra_id ? '…' : '✕'}
                      </button>
                    )}
                  </div>

                  {verCompra === it.compra_id && (
                    <div className="mt-2 ml-2 pl-3 border-l-2 border-line-soft">
                      {carregandoCompra || !compraDet ? (
                        <div className="h-10 animate-pulse" />
                      ) : (
                        <ul className="m-0 p-0 list-none flex flex-col gap-1">
                          {compraDet.parcelas
                            .slice()
                            .sort((a, b) => a.numero - b.numero)
                            .map((p) => (
                              <li
                                key={p.id}
                                className="flex items-center justify-between text-[12px] text-ink-soft"
                              >
                                <span className="font-mono text-[10px] text-ink-mute">
                                  {p.numero}/{p.total_parcelas} · vence {p.vencimento}
                                </span>
                                <span className="tabular-nums">
                                  {formatBRL(p.valor)}
                                  {Number(p.valor_juros) > 0
                                    ? ` (juros ${formatBRL(p.valor_juros)})`
                                    : ''}
                                </span>
                              </li>
                            ))}
                        </ul>
                      )}
                    </div>
                  )}
                </li>
              ))}
            </ul>
          )}

          <div className="flex items-baseline justify-between border-t border-line pt-3">
            <span className="font-mono uppercase tracking-[0.1em] text-[10px] text-ink-mute">
              total da fatura
            </span>
            <span className="font-display font-semibold tracking-tight text-ink">
              {formatBRL((data ?? { fatura }).fatura.valor_total)}
            </span>
          </div>

          {paga ? (
            <div className="text-sm text-ink-mute border-t border-line-soft pt-3">
              Fatura já paga. ✓
            </div>
          ) : !pagando ? (
            <div className="flex justify-end border-t border-line-soft pt-3">
              <button
                type="button"
                onClick={() => setPagando(true)}
                className="btn-primary px-4 py-2 text-sm"
              >
                Pagar fatura
              </button>
            </div>
          ) : (
            <div className="space-y-3 border-t border-line-soft pt-3">
              <div>
                <label className="block text-[13px] font-medium text-ink-soft mb-1.5">
                  Conta
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
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[13px] font-medium text-ink-soft mb-1.5">
                    Data do pagamento
                  </label>
                  <input
                    type="date"
                    className="input"
                    value={dataPg}
                    onChange={(e) => setDataPg(e.target.value)}
                  />
                </div>
                <div>
                  <label className="block text-[13px] font-medium text-ink-soft mb-1.5">
                    Valor pago (opcional)
                  </label>
                  <input
                    className="input"
                    value={valorPago}
                    onChange={(e) => setValorPago(e.target.value)}
                    inputMode="decimal"
                    placeholder={formatBRL((data ?? { fatura }).fatura.valor_total)}
                  />
                </div>
              </div>
              {erro && <div className="text-sm text-red-600">{erro}</div>}
              <div className="flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setPagando(false)}
                  className="btn-ghost px-4 py-2 text-sm"
                >
                  Voltar
                </button>
                <button
                  type="button"
                  onClick={pagar}
                  disabled={salvando}
                  className="btn-primary px-5 py-2 text-sm disabled:opacity-50"
                >
                  {salvando ? 'Pagando…' : 'Confirmar pagamento'}
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </Modal>
  );
}

function CompraForm({
  cartao,
  onClose,
  onSaved,
}: {
  cartao: Cartao;
  onClose: () => void;
  onSaved: () => void;
}) {
  const { arvore } = useCategorias();
  const categorias = useMemo(() => achatarCategorias(arvore), [arvore]);

  const [descricao, setDescricao] = useState('');
  const [valor, setValor] = useState('');
  const [parcelas, setParcelas] = useState('1');
  const [dataCompra, setDataCompra] = useState(
    () => new Date().toISOString().slice(0, 10),
  );
  const [categoriaId, setCategoriaId] = useState('');
  const [catReaproveitada, setCatReaproveitada] = useState('');
  const [comJuros, setComJuros] = useState(false);
  const [juros, setJuros] = useState('');
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState('');

  // Auto-categoria: ao sair do campo de descrição, se ainda não escolheu
  // categoria, reaproveita a da última compra com a mesma descrição.
  async function sugerirCategoria() {
    if (categoriaId || !descricao.trim()) return;
    try {
      const s = await api.financasSugestaoCategoriaCompra(descricao.trim());
      if (s.categoria_id) {
        setCategoriaId(s.categoria_id);
        setCatReaproveitada(s.categoria_nome ?? '');
      }
    } catch {
      /* sugestão é best-effort — ignora falha */
    }
  }

  const nParcelas = Number(parcelas);
  const valorNum = Number(valor.replace(',', '.'));
  const parcelaUnit =
    Number.isFinite(valorNum) && nParcelas >= 1 ? valorNum / nParcelas : 0;

  async function salvar(e: FormEvent) {
    e.preventDefault();
    setErro('');
    if (!descricao.trim()) return setErro('Descreva a compra.');
    if (!Number.isFinite(valorNum) || valorNum <= 0) {
      return setErro('Informe um valor maior que zero.');
    }
    if (!Number.isInteger(nParcelas) || nParcelas < 1 || nParcelas > 120) {
      return setErro('Número de parcelas entre 1 e 120.');
    }
    const jurosStr = comJuros && juros.trim()
      ? String(Number(juros.replace(',', '.')))
      : '0';
    if (!Number.isFinite(Number(jurosStr)) || Number(jurosStr) < 0) {
      return setErro('Juros inválido.');
    }
    if (Number(jurosStr) > valorNum) {
      return setErro('O juro não pode ser maior que o total.');
    }

    setSalvando(true);
    try {
      await api.financasCriarCompra({
        cartao_id: cartao.id,
        descricao: descricao.trim(),
        valor_total: String(valorNum),
        total_parcelas: nParcelas,
        data_compra: dataCompra || null,
        categoria_id: categoriaId || null,
        valor_juros_total: jurosStr,
      });
      onSaved();
    } catch (err) {
      setErro(err instanceof ApiError ? err.message : 'Falha ao lançar a compra.');
    } finally {
      setSalvando(false);
    }
  }

  return (
    <Modal open onClose={onClose} title={`Compra no ${cartao.nome}`}>
      <form onSubmit={salvar} className="space-y-4">
        <div>
          <label className="block text-[13px] font-medium text-ink-soft mb-1.5">
            Descrição
          </label>
          <input
            className="input"
            value={descricao}
            onChange={(e) => setDescricao(e.target.value)}
            onBlur={sugerirCategoria}
            placeholder="ex: Geladeira"
            autoFocus
          />
        </div>

        <div className="grid grid-cols-3 gap-3">
          <div>
            <label className="block text-[13px] font-medium text-ink-soft mb-1.5">
              Valor total
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
              Parcelas
            </label>
            <input
              className="input"
              value={parcelas}
              onChange={(e) => setParcelas(e.target.value)}
              inputMode="numeric"
            />
          </div>
          <div>
            <label className="block text-[13px] font-medium text-ink-soft mb-1.5">
              Data da compra
            </label>
            <input
              type="date"
              className="input"
              value={dataCompra}
              onChange={(e) => setDataCompra(e.target.value)}
            />
          </div>
        </div>

        {parcelaUnit > 0 && (
          <p className="text-[12.5px] text-ink-mute m-0">
            {nParcelas === 1
              ? `À vista — entra na próxima fatura: ${formatBRL(valorNum)}`
              : `${nParcelas}× de ${formatBRL(parcelaUnit)} (a última ajusta os centavos)`}
          </p>
        )}

        <div>
          <label className="block text-[13px] font-medium text-ink-soft mb-1.5">
            Categoria (opcional)
          </label>
          <select
            className="input"
            value={categoriaId}
            onChange={(e) => {
              setCategoriaId(e.target.value);
              setCatReaproveitada('');
            }}
          >
            <option value="">Sem categoria</option>
            {categorias.map((c) => (
              <option key={c.id} value={c.id}>
                {`${'  '.repeat(c.depth)}${c.nome}`}
              </option>
            ))}
          </select>
          {catReaproveitada && (
            <p className="text-[11.5px] text-ink-mute mt-1 m-0">
              categoria reaproveitada de uma compra parecida ({catReaproveitada})
            </p>
          )}
        </div>

        <div>
          <label className="flex items-center gap-2 text-sm text-ink-soft">
            <input
              type="checkbox"
              checked={comJuros}
              onChange={(e) => setComJuros(e.target.checked)}
            />
            Tem juros embutido
          </label>
          {comJuros && (
            <input
              className="input mt-2"
              value={juros}
              onChange={(e) => setJuros(e.target.value)}
              inputMode="decimal"
              placeholder="Quanto do total é juro (0,00)"
            />
          )}
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
            {salvando ? 'Lançando…' : 'Lançar compra'}
          </button>
        </div>
      </form>
    </Modal>
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

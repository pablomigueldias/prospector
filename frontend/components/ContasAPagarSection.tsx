import { useMemo, useState } from 'react';

import { CopiarLinha } from '@/components/CopiarLinha';
import { EditarPrevistaModal } from '@/components/EditarPrevistaModal';
import { PagarModal, type PagamentoAlvo } from '@/components/PagarModal';
import { useCategorias, useTransacoes } from '@/hooks/useFinancas';
import { api } from '@/lib/api';
import { achatarCategorias } from '@/lib/categorias';
import { calcularEncargos } from '@/lib/encargos';
import { formatBRL } from '@/lib/format';
import {
  ApiError,
  type Conta,
  type TransacaoListItem,
  type TransacaoResponse,
} from '@/lib/types';

interface Props {
  contas: Conta[];
  /** Recarrega resumo/contas do dashboard depois de quitar. */
  onMutate: () => void;
}

type Aba = 'a_pagar' | 'pagas';

function hojeIso(): string {
  return new Date().toISOString().slice(0, 10);
}

/** Dias de atraso (>0 vencido, 0 vence hoje, <0 ainda no prazo); null sem venc. */
function diasParaVencer(venc?: string | null): number | null {
  if (!venc) return null;
  const hoje = new Date(hojeIso() + 'T00:00:00');
  const d = new Date(venc + 'T00:00:00');
  return Math.round((hoje.getTime() - d.getTime()) / 86_400_000);
}

function vencLabel(venc?: string | null): { texto: string; vencido: boolean } {
  if (!venc) return { texto: 'sem vencimento', vencido: false };
  const [, m, d] = venc.split('-');
  const curto = `${d}/${m}`;
  const dias = diasParaVencer(venc);
  if (dias === null) return { texto: curto, vencido: false };
  if (dias > 0) return { texto: `venceu ${curto} (${dias}d)`, vencido: true };
  if (dias === 0) return { texto: `vence hoje`, vencido: true };
  return { texto: `vence ${curto}`, vencido: false };
}

export function ContasAPagarSection({ contas, onMutate }: Props) {
  const [aba, setAba] = useState<Aba>('a_pagar');

  const filtro = useMemo(
    () =>
      aba === 'a_pagar'
        ? {
            tipo: 'despesa' as const,
            status: ['prevista', 'atrasada'],
            por_vencimento: true,
            limit: 100,
          }
        : { tipo: 'despesa' as const, status: ['paga'], limit: 50 },
    [aba],
  );

  const { transacoes, total, loading, refetch } = useTransacoes(filtro);

  const { arvore } = useCategorias();
  const categorias = useMemo(() => achatarCategorias(arvore), [arvore]);

  // Quitação (reusa o PagarModal). Busca o detalhe pra saber se já tem conta.
  const [pagando, setPagando] = useState<PagamentoAlvo | null>(null);
  const [carregandoPagar, setCarregandoPagar] = useState<string | null>(null);
  const [erro, setErro] = useState('');

  // Edição da conta a pagar (detalhar verbas etc.) — busca o detalhe completo.
  const [editando, setEditando] = useState<TransacaoResponse | null>(null);
  const [carregandoEditar, setCarregandoEditar] = useState<string | null>(null);

  async function abrirEdicao(t: TransacaoListItem) {
    setErro('');
    setCarregandoEditar(t.id);
    try {
      setEditando(await api.financasTransacao(t.id));
    } catch (err) {
      setErro(err instanceof ApiError ? err.message : 'Falha ao abrir a edição.');
    } finally {
      setCarregandoEditar(null);
    }
  }

  async function abrirPagamento(t: TransacaoListItem) {
    setErro('');
    setCarregandoPagar(t.id);
    try {
      const det = await api.financasTransacao(t.id);
      setPagando({
        id: det.id,
        descricao: det.descricao,
        valor: String(det.valor_total),
        contaIdAtual: det.pagamentos?.[0]?.conta_id ?? null,
        vencimento: det.data_vencimento ?? null,
        multaPct: det.multa_percentual ?? null,
        jurosPct: det.juros_mensal_percentual ?? null,
      });
    } catch (err) {
      setErro(err instanceof ApiError ? err.message : 'Falha ao abrir o pagamento.');
    } finally {
      setCarregandoPagar(null);
    }
  }

  const recarregar = () => {
    void refetch();
    onMutate();
  };

  // Resumo do que está a pagar (só faz sentido na aba "a pagar").
  const resumo = useMemo(() => {
    if (aba !== 'a_pagar') return null;
    let totalValor = 0;
    let vencidas = 0;
    for (const t of transacoes) {
      const enc = calcularEncargos(
        t.valor_total, t.data_vencimento,
        t.multa_percentual, t.juros_mensal_percentual, hojeIso(),
      );
      totalValor += Number(t.valor_total) + enc.total;
      const dias = diasParaVencer(t.data_vencimento);
      if (dias !== null && dias >= 0) vencidas += 1;
    }
    return { totalValor, vencidas };
  }, [aba, transacoes]);

  return (
    <section id="sec-a-pagar" className="scroll-mt-16 mb-8">
      <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
        <h2 className="font-display font-semibold text-lg tracking-tight text-ink m-0">
          Contas a pagar
        </h2>
        <div className="flex gap-1.5">
          {([
            ['a_pagar', 'A pagar'],
            ['pagas', 'Pagas'],
          ] as [Aba, string][]).map(([id, label]) => (
            <button
              key={id}
              type="button"
              onClick={() => setAba(id)}
              className={[
                'px-3 py-1.5 text-[12.5px] rounded-md font-medium transition-colors',
                aba === id ? 'bg-brand-soft text-brand' : 'text-ink-soft hover:bg-bg-alt',
              ].join(' ')}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {resumo && !loading && transacoes.length > 0 && (
        <div className="flex flex-wrap items-center gap-x-5 gap-y-1 mb-3 text-sm">
          <span className="text-ink-soft">
            {total} {total === 1 ? 'conta' : 'contas'} a pagar ·{' '}
            <strong className="text-ink">{formatBRL(resumo.totalValor)}</strong>
          </span>
          {resumo.vencidas > 0 && (
            <span className="text-red-600 font-medium">
              {resumo.vencidas} vencida{resumo.vencidas > 1 ? 's' : ''}
            </span>
          )}
        </div>
      )}

      {erro && (
        <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded px-3 py-2 mb-2">
          {erro}
        </div>
      )}

      {loading ? (
        <div className="space-y-2">
          {[0, 1, 2].map((i) => (
            <div key={i} className="card p-4 h-[58px] animate-pulse" />
          ))}
        </div>
      ) : transacoes.length === 0 ? (
        <div className="card p-6 text-center text-ink-soft text-sm">
          {aba === 'a_pagar'
            ? 'Nada a pagar por aqui. 🎉'
            : 'Nenhuma conta paga ainda.'}
        </div>
      ) : (
        <div className="card divide-y divide-line">
          {transacoes.map((t) => {
            const venc = vencLabel(t.data_vencimento);
            const paga = aba === 'pagas';
            // Juros/multa acumulados até hoje (só faz sentido nas a pagar vencidas).
            const enc = paga
              ? null
              : calcularEncargos(
                  t.valor_total, t.data_vencimento,
                  t.multa_percentual, t.juros_mensal_percentual, hojeIso(),
                );
            return (
              <div key={t.id} className="flex items-center gap-3 px-4 py-2.5">
                <div className="min-w-0 flex-1">
                  <div className="text-sm text-ink truncate">{t.descricao}</div>
                  <div className="text-[11.5px] truncate">
                    {paga ? (
                      <span className="text-ink-mute">
                        {t.data_pagamento
                          ? `pago em ${t.data_pagamento.split('-').reverse().slice(0, 2).join('/')}`
                          : 'pago'}
                        {t.categoria_nome ? ` · ${t.categoria_nome}` : ''}
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-2">
                        <span className={venc.vencido ? 'text-red-600 font-medium' : 'text-ink-mute'}>
                          {venc.texto}
                          {t.categoria_nome ? (
                            <span className="text-ink-mute"> · {t.categoria_nome}</span>
                          ) : ''}
                        </span>
                        {t.linha_digitavel && <CopiarLinha linha={t.linha_digitavel} />}
                      </span>
                    )}
                  </div>
                </div>
                <div className="shrink-0 text-right">
                  <div className="font-display font-semibold tracking-tight text-sm text-ink">
                    −{formatBRL(enc && enc.total > 0 ? Number(t.valor_total) + enc.total : t.valor_total)}
                  </div>
                  {enc && enc.total > 0 && (
                    <div className="text-[10.5px] text-red-600">
                      inclui +{formatBRL(enc.total)} juros/multa
                    </div>
                  )}
                </div>
                {paga ? (
                  <span className="shrink-0 text-[10px] uppercase tracking-wide text-success border border-success-soft rounded px-1.5 py-0.5">
                    pago
                  </span>
                ) : (
                  <>
                    <button
                      type="button"
                      onClick={() => abrirEdicao(t)}
                      disabled={carregandoEditar === t.id}
                      className="shrink-0 text-ink-faint hover:text-brand text-sm px-1 disabled:opacity-50"
                      title="Editar (detalhar verbas, valor, vencimento…)"
                      aria-label="Editar conta a pagar"
                    >
                      {carregandoEditar === t.id ? '…' : '✎'}
                    </button>
                    <button
                      type="button"
                      onClick={() => abrirPagamento(t)}
                      disabled={carregandoPagar === t.id}
                      className="shrink-0 text-[11px] font-medium text-success border border-success-soft hover:bg-success-soft rounded-pill px-2.5 py-1 transition-colors disabled:opacity-50"
                      title="Marcar como paga (move o saldo)"
                    >
                      {carregandoPagar === t.id ? '…' : '✓ Pagar'}
                    </button>
                  </>
                )}
              </div>
            );
          })}
        </div>
      )}

      {pagando && (
        <PagarModal
          contas={contas}
          alvo={pagando}
          onClose={() => setPagando(null)}
          onPaid={() => {
            setPagando(null);
            recarregar();
          }}
        />
      )}

      {editando && (
        <EditarPrevistaModal
          detalhe={editando}
          categorias={categorias}
          onClose={() => setEditando(null)}
          onSaved={() => {
            setEditando(null);
            recarregar();
          }}
        />
      )}
    </section>
  );
}

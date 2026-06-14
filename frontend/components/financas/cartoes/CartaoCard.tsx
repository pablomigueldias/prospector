import { useState } from 'react';

import { useCartaoFaturas } from '@/hooks/useFinancas';
import { formatBRL, formatMesAno } from '@/lib/format';
import type { Cartao, Fatura } from '@/lib/types';

import { CompraForm } from './CompraForm';
import { FaturaExtratoModal } from './FaturaExtratoModal';

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

/** Card de um cartão: limite/uso, próximas faturas, + Compra e Pagar fatura. */
export function CartaoCard({
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

import { useCartaoFaturas, useCartoes } from '@/hooks/useFinancas';
import { formatBRL } from '@/lib/format';
import type { Cartao, Fatura } from '@/lib/types';

export function CartoesSection() {
  const { cartoes, loading } = useCartoes();

  if (loading) {
    return <div className="card p-4 h-[120px] animate-pulse" />;
  }
  if (cartoes.length === 0) {
    return (
      <div className="card p-6 text-center text-ink-soft text-sm">
        Nenhum cartão cadastrado.
      </div>
    );
  }
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
      {cartoes.map((c) => (
        <CartaoCard key={c.id} cartao={c} />
      ))}
    </div>
  );
}

function CartaoCard({ cartao }: { cartao: Cartao }) {
  const { dados, loading } = useCartaoFaturas(cartao.id);
  const abertas = (dados?.faturas ?? []).filter((f) => f.status !== 'paga');

  return (
    <div className="card p-4">
      <div className="flex items-baseline justify-between mb-3">
        <div>
          <div className="font-medium text-ink">{cartao.nome}</div>
          <div className="font-mono uppercase tracking-[0.1em] text-[10px] text-ink-mute">
            {cartao.bandeira || 'cartão'} · fecha dia {cartao.dia_fechamento} · vence dia{' '}
            {cartao.dia_vencimento}
          </div>
        </div>
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

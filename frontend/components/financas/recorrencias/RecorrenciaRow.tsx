import { formatBRL } from '@/lib/format';
import type { Recorrencia, RecorrenciaStatusItem } from '@/lib/types';

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

export function RecorrenciaRow({
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

import { useMemo } from 'react';

import { useLeituras } from '@/hooks/useFinancas';
import type { LeituraConsumo } from '@/lib/types';

const TIPO_LABEL: Record<string, string> = {
  agua: '💧 Água',
  gas: '🔥 Gás',
  luz: '💡 Luz',
};

export function ConsumoSection() {
  const { leituras, loading } = useLeituras();

  const porTipo = useMemo(() => {
    const m: Record<string, LeituraConsumo[]> = {};
    for (const l of leituras) {
      (m[l.tipo] ??= []).push(l);
    }
    return m;
  }, [leituras]);

  if (loading) {
    return <div className="card p-4 h-[120px] animate-pulse" />;
  }
  const tipos = Object.keys(porTipo);
  if (tipos.length === 0) {
    return (
      <div className="card p-6 text-center text-ink-soft text-sm">
        Sem leituras de consumo ainda. Elas chegam pelos boletos de condomínio.
      </div>
    );
  }
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
      {tipos.map((tipo) => (
        <ConsumoCard key={tipo} tipo={tipo} leituras={porTipo[tipo]} />
      ))}
    </div>
  );
}

function ConsumoCard({ tipo, leituras }: { tipo: string; leituras: LeituraConsumo[] }) {
  const valores = leituras.map((l) => Number(l.consumo ?? 0));
  const max = Math.max(1, ...valores);
  const ultimo = valores[valores.length - 1] ?? 0;

  return (
    <div className="card p-4">
      <div className="flex items-baseline justify-between mb-3">
        <span className="font-medium text-ink">{TIPO_LABEL[tipo] ?? tipo}</span>
        <span className="text-ink-soft text-sm tabular-nums">
          {ultimo.toLocaleString('pt-BR')} <span className="text-ink-mute text-[11px]">último</span>
        </span>
      </div>
      <div className="flex items-end gap-1 h-12">
        {leituras.map((l) => {
          const v = Number(l.consumo ?? 0);
          const h = Math.round((v / max) * 100);
          return (
            <div
              key={l.id}
              className="flex-1 bg-brand-soft rounded-sm min-h-[2px]"
              style={{ height: `${h}%` }}
              title={`${l.mes_referencia}: ${v.toLocaleString('pt-BR')}`}
            />
          );
        })}
      </div>
    </div>
  );
}

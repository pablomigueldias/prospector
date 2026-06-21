import { useState } from 'react';

import { formatBRL } from '@/lib/format';
import { useFreelaActions } from '@/hooks/useFreela';
import { type FreelaPrecificarResponse } from '@/lib/types';

// ── Precificador ──────────────────────────────────────────────────

export function Precificador({
  plataformaId,
  clientes,
}: {
  plataformaId: string | null;
  clientes: { id: string; nome: string }[];
}) {
  const acoes = useFreelaActions();
  const [aberto, setAberto] = useState(false);
  const [liquido, setLiquido] = useState('1400');
  const [clienteId, setClienteId] = useState('');
  const [jaPagou, setJaPagou] = useState('0');
  const [horas, setHoras] = useState('');
  const [valorHora, setValorHora] = useState('');
  const [orcMin, setOrcMin] = useState('');
  const [orcMax, setOrcMax] = useState('');
  const [res, setRes] = useState<FreelaPrecificarResponse | null>(null);

  async function calcular() {
    const r = await acoes.precificar({
      liquido_desejado: Number(liquido) || 0,
      cliente_id: clienteId || null,
      ja_me_pagou_usd: clienteId ? null : Number(jaPagou) || 0,
      plataforma_id: plataformaId,
      horas_estimadas: horas ? Number(horas) : null,
      valor_hora_alvo: valorHora ? Number(valorHora) : null,
      orcamento_min: orcMin ? Number(orcMin) : null,
      orcamento_max: orcMax ? Number(orcMax) : null,
    });
    if (r) setRes(r);
  }

  return (
    <div className="card p-5">
      <button
        type="button"
        className="flex items-center justify-between w-full text-left"
        onClick={() => setAberto((v) => !v)}
      >
        <span className="font-display font-semibold text-[15px] text-ink">
          💰 Precificador — quanto cotar pra receber o que você quer
        </span>
        <span className="text-ink-mute text-sm">{aberto ? '▲' : '▼'}</span>
      </button>

      {aberto && (
        <div className="mt-4">
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            <label className="text-[13px] text-ink-soft">
              Quero receber (R$)
              <input
                className="input mt-1"
                type="number"
                value={liquido}
                onChange={(e) => setLiquido(e.target.value)}
              />
            </label>
            <label className="text-[13px] text-ink-soft">
              Cliente
              <select
                className="input mt-1"
                value={clienteId}
                onChange={(e) => setClienteId(e.target.value)}
              >
                <option value="">Novo (informo abaixo)</option>
                {clientes.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.nome}
                  </option>
                ))}
              </select>
            </label>
            {!clienteId && (
              <label className="text-[13px] text-ink-soft">
                Já me pagou (US$)
                <input
                  className="input mt-1"
                  type="number"
                  value={jaPagou}
                  onChange={(e) => setJaPagou(e.target.value)}
                />
              </label>
            )}
            <label className="text-[13px] text-ink-soft">
              Horas estimadas
              <input
                className="input mt-1"
                type="number"
                value={horas}
                onChange={(e) => setHoras(e.target.value)}
              />
            </label>
            <label className="text-[13px] text-ink-soft">
              Valor-hora alvo (R$)
              <input
                className="input mt-1"
                type="number"
                value={valorHora}
                onChange={(e) => setValorHora(e.target.value)}
              />
            </label>
            <label className="text-[13px] text-ink-soft">
              Orçamento do cliente — mín (R$)
              <input
                className="input mt-1"
                type="number"
                value={orcMin}
                placeholder="opcional"
                onChange={(e) => setOrcMin(e.target.value)}
              />
            </label>
            <label className="text-[13px] text-ink-soft">
              Orçamento do cliente — máx (R$)
              <input
                className="input mt-1"
                type="number"
                value={orcMax}
                placeholder="opcional"
                onChange={(e) => setOrcMax(e.target.value)}
              />
            </label>
            <div className="flex items-end">
              <button
                type="button"
                className="btn-primary w-full"
                onClick={calcular}
                disabled={acoes.loading}
              >
                {acoes.loading ? 'Calculando…' : 'Calcular'}
              </button>
            </div>
          </div>

          {res && (
            <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-3">
              <ResultBox titulo="Comissão" valor={`${Math.round(res.pct_comissao * 100)}%`} />
              <ResultBox titulo="Cotar (valor total)" valor={formatBRL(res.valor_a_cotar)} forte />
              <ResultBox titulo="Cliente paga" valor={formatBRL(res.cliente_paga)} />
              <ResultBox
                titulo="Líquido / hora"
                valor={res.liquido_por_hora != null ? formatBRL(res.liquido_por_hora) : '—'}
              />
              {res.alerta && (
                <div className="col-span-2 md:col-span-4 text-[13px] text-amber-700 bg-amber-50 border border-amber-200 rounded p-2.5">
                  ⚠️ {res.alerta}
                </div>
              )}
              {res.alerta_orcamento && (
                <div
                  className={`col-span-2 md:col-span-4 text-[13px] rounded p-2.5 border ${
                    res.orcamento_status === 'acima'
                      ? 'text-red-700 bg-red-50 border-red-200'
                      : 'text-amber-700 bg-amber-50 border-amber-200'
                  }`}
                >
                  {res.orcamento_status === 'acima' ? '🔴' : '🟡'} {res.alerta_orcamento}
                </div>
              )}
              {res.orcamento_status === 'dentro' && (
                <div className="col-span-2 md:col-span-4 text-[13px] text-emerald-700 bg-emerald-50 border border-emerald-200 rounded p-2.5">
                  🟢 Lance dentro da faixa de orçamento informada.
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function ResultBox({ titulo, valor, forte }: { titulo: string; valor: string; forte?: boolean }) {
  return (
    <div className={`rounded border p-3 ${forte ? 'bg-brand-soft/50 border-brand/30' : 'bg-bg-alt border-transparent'}`}>
      <div className="text-[11px] uppercase tracking-wide text-ink-mute">{titulo}</div>
      <div className={`mt-0.5 ${forte ? 'text-ink font-display font-semibold text-lg' : 'text-ink text-[15px]'}`}>
        {valor}
      </div>
    </div>
  );
}


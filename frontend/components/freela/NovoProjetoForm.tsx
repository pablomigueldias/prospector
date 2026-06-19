import { useState } from 'react';

import { type FreelaExtrairProjeto } from '@/lib/types';

// ── Form de novo projeto ──────────────────────────────────────────

export function NovoProjetoForm({
  loading,
  erro,
  clientes,
  onSubmit,
  onExtrair,
}: {
  loading: boolean;
  erro: string | null;
  clientes: { id: string; nome: string }[];
  onSubmit: (body: {
    titulo: string;
    descricao: string;
    cliente_id?: string | null;
    faixa_orcamento_min?: number | null;
    faixa_orcamento_max?: number | null;
    n_propostas_concorrentes?: number | null;
    n_interessados?: number | null;
    habilidades?: string[];
    publicado_em?: string | null;
  }) => void;
  onExtrair: (texto: string) => Promise<FreelaExtrairProjeto | null>;
}) {
  const [titulo, setTitulo] = useState('');
  const [descricao, setDescricao] = useState('');
  const [clienteId, setClienteId] = useState('');
  const [min, setMin] = useState('');
  const [max, setMax] = useState('');
  const [nProp, setNProp] = useState('');
  const [nInteress, setNInteress] = useState('');
  const [habilidades, setHabilidades] = useState('');
  const [pubEm, setPubEm] = useState('');
  const [extraindo, setExtraindo] = useState(false);

  async function autoPreencher() {
    if (!descricao.trim()) return;
    setExtraindo(true);
    const r = await onExtrair(descricao.trim());
    setExtraindo(false);
    if (!r) return;
    if (r.titulo && !titulo.trim()) setTitulo(r.titulo);
    if (r.faixa_orcamento_min != null) setMin(String(r.faixa_orcamento_min));
    if (r.faixa_orcamento_max != null) setMax(String(r.faixa_orcamento_max));
    if (r.n_propostas_concorrentes != null) setNProp(String(r.n_propostas_concorrentes));
    if (r.n_interessados != null) setNInteress(String(r.n_interessados));
    if (r.habilidades?.length && !habilidades.trim()) setHabilidades(r.habilidades.join(', '));
  }

  return (
    <div className="card p-5 mb-4">
      <div className="grid gap-3">
        <label className="text-[13px] text-ink-soft">
          Título do projeto
          <input className="input mt-1" value={titulo} onChange={(e) => setTitulo(e.target.value)} />
        </label>
        <div>
          <div className="flex items-center justify-between gap-2 mb-1">
            <span className="text-[13px] text-ink-soft">
              Descrição (cole o texto do projeto)
            </span>
            <button
              type="button"
              className="btn-ghost text-[12px] px-2 py-1 disabled:opacity-40"
              onClick={autoPreencher}
              disabled={extraindo || !descricao.trim()}
              title="A IA lê o texto e preenche título, orçamento, propostas, interessados e habilidades exigidas"
            >
              {extraindo ? 'Lendo…' : '✨ Auto-preencher do texto'}
            </button>
          </div>
          <textarea
            className="input min-h-[120px]"
            value={descricao}
            onChange={(e) => setDescricao(e.target.value)}
          />
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <label className="text-[13px] text-ink-soft">
            Cliente
            <select className="input mt-1" value={clienteId} onChange={(e) => setClienteId(e.target.value)}>
              <option value="">—</option>
              {clientes.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.nome}
                </option>
              ))}
            </select>
          </label>
          <label className="text-[13px] text-ink-soft">
            Orçamento mín
            <input className="input mt-1" type="number" value={min} onChange={(e) => setMin(e.target.value)} />
          </label>
          <label className="text-[13px] text-ink-soft">
            Orçamento máx
            <input className="input mt-1" type="number" value={max} onChange={(e) => setMax(e.target.value)} />
          </label>
          <label className="text-[13px] text-ink-soft">
            Nº propostas
            <input className="input mt-1" type="number" value={nProp} onChange={(e) => setNProp(e.target.value)} />
          </label>
          <label className="text-[13px] text-ink-soft">
            Nº interessados
            <input className="input mt-1" type="number" value={nInteress} onChange={(e) => setNInteress(e.target.value)} />
          </label>
          <label className="text-[13px] text-ink-soft">
            Publicado em
            <input className="input mt-1" type="date" value={pubEm} onChange={(e) => setPubEm(e.target.value)} />
          </label>
        </div>
        <label className="text-[13px] text-ink-soft">
          Habilidades exigidas <span className="text-ink-faint">(separe por vírgula)</span>
          <input
            className="input mt-1"
            value={habilidades}
            placeholder="React, FastAPI, PostgreSQL…"
            onChange={(e) => setHabilidades(e.target.value)}
          />
        </label>
        {erro && <div className="text-[13px] text-red-600">{erro}</div>}
        <div>
          <button
            type="button"
            className="btn-primary"
            disabled={loading || !titulo.trim() || !descricao.trim()}
            onClick={() =>
              onSubmit({
                titulo: titulo.trim(),
                descricao: descricao.trim(),
                cliente_id: clienteId || null,
                faixa_orcamento_min: min ? Number(min) : null,
                faixa_orcamento_max: max ? Number(max) : null,
                n_propostas_concorrentes: nProp ? Number(nProp) : null,
                n_interessados: nInteress ? Number(nInteress) : null,
                habilidades: habilidades
                  .split(',')
                  .map((s) => s.trim())
                  .filter(Boolean),
                publicado_em: pubEm || null,
              })
            }
          >
            {loading ? 'Salvando…' : 'Salvar projeto'}
          </button>
        </div>
      </div>
    </div>
  );
}

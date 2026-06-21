import { useMemo, useState } from 'react';

import { SidePanel } from '@/components/shared/SidePanel';
import {
  type FreelaCliente,
  type FreelaClienteCreate,
} from '@/lib/types';

type Aberto = FreelaCliente | 'novo' | null;

/** Campos editáveis de um cliente (espelha ClienteUpdate no backend). */
type FormState = {
  nome: string;
  plataforma_id: string;
  rating: string;
  projetos_publicados: string;
  projetos_pagos: string;
  pagamento_verificado: boolean;
  membro_desde: string;
  ja_me_pagou_usd: string;
  notas: string;
};

function paraForm(c: FreelaCliente | null): FormState {
  return {
    nome: c?.nome ?? '',
    plataforma_id: c?.plataforma_id ?? '',
    rating: c?.rating != null ? String(c.rating) : '',
    projetos_publicados: c?.projetos_publicados != null ? String(c.projetos_publicados) : '',
    projetos_pagos: c?.projetos_pagos != null ? String(c.projetos_pagos) : '',
    pagamento_verificado: c?.pagamento_verificado ?? false,
    membro_desde: c?.membro_desde ?? '',
    ja_me_pagou_usd: c?.ja_me_pagou_usd != null ? String(c.ja_me_pagou_usd) : '',
    notas: c?.notas ?? '',
  };
}

const num = (s: string): number | null => (s.trim() ? Number(s) : null);

/**
 * Gestão de clientes do freela na própria tela (§2.A do PLANO-MESTRE). Lista os
 * clientes e abre um drawer (SidePanel) pra criar/editar/excluir — antes só dava
 * via API. Reusa o SidePanel genérico do CRM.
 */
export function ClientesPanel({
  clientes,
  loading,
  salvando,
  plataformas,
  onCriar,
  onAtualizar,
  onRemover,
  onMudou,
}: {
  clientes: FreelaCliente[];
  loading: boolean;
  salvando: boolean;
  plataformas: { id: string; nome: string }[];
  onCriar: (body: FreelaClienteCreate) => Promise<FreelaCliente | null>;
  onAtualizar: (id: string, body: Partial<FreelaCliente>) => Promise<FreelaCliente | null>;
  onRemover: (id: string) => Promise<void | null>;
  onMudou: () => void;
}) {
  const [aberto, setAberto] = useState<Aberto>(null);
  const [busca, setBusca] = useState('');
  const [filtroPlataforma, setFiltroPlataforma] = useState('todas');
  const nomePlataforma = (id?: string | null) =>
    plataformas.find((p) => p.id === id)?.nome ?? '—';

  const filtrados = useMemo(() => {
    const q = busca.trim().toLowerCase();
    return clientes.filter((c) => {
      if (filtroPlataforma === 'todas') {
        /* sem filtro de plataforma */
      } else if (filtroPlataforma === 'sem') {
        if (c.plataforma_id) return false;
      } else if (c.plataforma_id !== filtroPlataforma) {
        return false;
      }
      if (!q) return true;
      return (
        c.nome.toLowerCase().includes(q) ||
        (c.notas ?? '').toLowerCase().includes(q)
      );
    });
  }, [clientes, busca, filtroPlataforma]);

  return (
    <section>
      <div className="flex items-center justify-between mb-4">
        <h2 className="font-display font-semibold text-lg tracking-tight text-ink m-0">
          Clientes
        </h2>
        <button type="button" className="btn-primary" onClick={() => setAberto('novo')}>
          + Cliente
        </button>
      </div>

      {loading ? (
        <div className="text-[13px] text-ink-mute">Carregando…</div>
      ) : clientes.length === 0 ? (
        <div className="card p-5 text-[13px] text-ink-mute">
          Nenhum cliente ainda. Cadastre um pra reaproveitar nos projetos e propostas.
        </div>
      ) : (
        <>
        <div className="flex flex-wrap items-center gap-2 mb-3">
          <input
            className="input py-1.5 text-[13px] w-56"
            placeholder="Buscar por nome ou nota…"
            value={busca}
            onChange={(e) => setBusca(e.target.value)}
          />
          <select
            className="input py-1.5 text-[13px] w-44"
            value={filtroPlataforma}
            onChange={(e) => setFiltroPlataforma(e.target.value)}
          >
            <option value="todas">Todas as plataformas</option>
            {plataformas.map((p) => (
              <option key={p.id} value={p.id}>
                {p.nome}
              </option>
            ))}
            <option value="sem">Sem plataforma</option>
          </select>
          <span className="text-[12px] text-ink-mute">
            {filtrados.length} de {clientes.length}
          </span>
        </div>
        <div className="card overflow-x-auto p-0">
          <table className="w-full border-collapse text-[13px]">
            <thead>
              <tr className="border-b border-line text-left text-ink-mute">
                <th className="font-medium px-4 py-2.5">Cliente</th>
                <th className="font-medium px-4 py-2.5">Plataforma</th>
                <th className="font-medium px-4 py-2.5 text-right">Rating</th>
                <th className="font-medium px-4 py-2.5 text-right">Pagos</th>
                <th className="font-medium px-4 py-2.5 text-right">Já me pagou</th>
                <th className="font-medium px-4 py-2.5">Pagamento</th>
              </tr>
            </thead>
            <tbody>
              {filtrados.map((c) => (
                <tr
                  key={c.id}
                  onClick={() => setAberto(c)}
                  className="border-b border-line/60 last:border-0 hover:bg-bg-alt cursor-pointer"
                >
                  <td className="px-4 py-2.5 font-medium text-ink">{c.nome}</td>
                  <td className="px-4 py-2.5 text-ink-soft">{nomePlataforma(c.plataforma_id)}</td>
                  <td className="px-4 py-2.5 text-right text-ink-soft">
                    {c.rating != null ? `★ ${c.rating}` : '—'}
                  </td>
                  <td className="px-4 py-2.5 text-right text-ink-soft">{c.projetos_pagos ?? 0}</td>
                  <td className="px-4 py-2.5 text-right text-ink-soft">
                    {c.ja_me_pagou_usd > 0 ? `US$ ${c.ja_me_pagou_usd}` : '—'}
                  </td>
                  <td className="px-4 py-2.5">
                    {c.pagamento_verificado ? (
                      <span className="text-[11px] px-2 py-0.5 rounded-full bg-brand-soft text-brand border border-brand/30 whitespace-nowrap">
                        ✓ verificado
                      </span>
                    ) : (
                      <span className="text-ink-faint">—</span>
                    )}
                  </td>
                </tr>
              ))}
              {filtrados.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-4 py-6 text-center text-ink-mute">
                    Nenhum cliente com esse filtro.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        </>
      )}

      {aberto && (
        <ClienteDrawer
          key={aberto === 'novo' ? 'novo' : aberto.id}
          cliente={aberto === 'novo' ? null : aberto}
          plataformas={plataformas}
          salvando={salvando}
          onClose={() => setAberto(null)}
          onSalvar={async (form) => {
            const payload: FreelaClienteCreate = {
              nome: form.nome.trim(),
              plataforma_id: form.plataforma_id || null,
              rating: num(form.rating),
              projetos_publicados: num(form.projetos_publicados),
              projetos_pagos: num(form.projetos_pagos),
              pagamento_verificado: form.pagamento_verificado,
              membro_desde: form.membro_desde.trim() || null,
              ja_me_pagou_usd: num(form.ja_me_pagou_usd) ?? 0,
              notas: form.notas.trim() || null,
            };
            const r =
              aberto === 'novo'
                ? await onCriar(payload)
                : await onAtualizar(aberto.id, payload);
            if (r) {
              setAberto(null);
              onMudou();
            }
          }}
          onExcluir={async () => {
            if (aberto === 'novo') return;
            if (!confirm(`Excluir o cliente "${aberto.nome}"?`)) return;
            await onRemover(aberto.id);
            setAberto(null);
            onMudou();
          }}
        />
      )}
    </section>
  );
}

function ClienteDrawer({
  cliente,
  plataformas,
  salvando,
  onClose,
  onSalvar,
  onExcluir,
}: {
  cliente: FreelaCliente | null;
  plataformas: { id: string; nome: string }[];
  salvando: boolean;
  onClose: () => void;
  onSalvar: (form: FormState) => void;
  onExcluir: () => void;
}) {
  const [form, setForm] = useState<FormState>(() => paraForm(cliente));
  const set = <K extends keyof FormState>(k: K, v: FormState[K]) =>
    setForm((f) => ({ ...f, [k]: v }));

  return (
    <SidePanel
      open
      onClose={onClose}
      title={cliente ? cliente.nome : 'Novo cliente'}
      acoes={
        cliente ? (
          <button
            type="button"
            className="btn-ghost text-[12px] px-2 py-1 text-red-600"
            onClick={onExcluir}
            disabled={salvando}
          >
            Excluir
          </button>
        ) : undefined
      }
    >
      <div className="grid gap-3">
        <label className="text-[13px] text-ink-soft">
          Nome
          <input
            className="input mt-1"
            value={form.nome}
            onChange={(e) => set('nome', e.target.value)}
          />
        </label>
        <label className="text-[13px] text-ink-soft">
          Plataforma
          <select
            className="input mt-1"
            value={form.plataforma_id}
            onChange={(e) => set('plataforma_id', e.target.value)}
          >
            <option value="">—</option>
            {plataformas.map((p) => (
              <option key={p.id} value={p.id}>
                {p.nome}
              </option>
            ))}
          </select>
        </label>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          <label className="text-[13px] text-ink-soft">
            Rating
            <input
              className="input mt-1"
              type="number"
              step="0.1"
              value={form.rating}
              onChange={(e) => set('rating', e.target.value)}
            />
          </label>
          <label className="text-[13px] text-ink-soft">
            Projetos publicados
            <input
              className="input mt-1"
              type="number"
              value={form.projetos_publicados}
              onChange={(e) => set('projetos_publicados', e.target.value)}
            />
          </label>
          <label className="text-[13px] text-ink-soft">
            Projetos pagos
            <input
              className="input mt-1"
              type="number"
              value={form.projetos_pagos}
              onChange={(e) => set('projetos_pagos', e.target.value)}
            />
          </label>
          <label className="text-[13px] text-ink-soft">
            Já me pagou (US$)
            <input
              className="input mt-1"
              type="number"
              step="0.01"
              value={form.ja_me_pagou_usd}
              onChange={(e) => set('ja_me_pagou_usd', e.target.value)}
            />
          </label>
          <label className="text-[13px] text-ink-soft">
            Membro desde
            <input
              className="input mt-1"
              value={form.membro_desde}
              placeholder="2023 ou jan/2023"
              onChange={(e) => set('membro_desde', e.target.value)}
            />
          </label>
        </div>
        <label className="flex items-center gap-2 text-[13px] text-ink-soft">
          <input
            type="checkbox"
            checked={form.pagamento_verificado}
            onChange={(e) => set('pagamento_verificado', e.target.checked)}
          />
          Pagamento verificado
        </label>
        <label className="text-[13px] text-ink-soft">
          Notas
          <textarea
            className="input mt-1 min-h-[90px]"
            value={form.notas}
            onChange={(e) => set('notas', e.target.value)}
          />
        </label>
        <div className="flex justify-end gap-2 pt-1">
          <button type="button" className="btn-ghost" onClick={onClose} disabled={salvando}>
            Cancelar
          </button>
          <button
            type="button"
            className="btn-primary"
            disabled={salvando || !form.nome.trim()}
            onClick={() => onSalvar(form)}
          >
            {salvando ? 'Salvando…' : 'Salvar'}
          </button>
        </div>
      </div>
    </SidePanel>
  );
}

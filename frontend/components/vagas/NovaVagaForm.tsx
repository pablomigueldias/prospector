import { useState } from 'react';

import { type VagaCreate } from '@/lib/types';
import { Campo } from './_shared';

// ── Form de nova vaga ─────────────────────────────────────────────

export function NovaVagaForm({
  onSubmit,
  loading,
  erro,
}: {
  onSubmit: (body: VagaCreate) => void;
  loading: boolean;
  erro: string | null;
}) {
  const [f, setF] = useState<VagaCreate>({ titulo: '', descricao: '' });

  function set<K extends keyof VagaCreate>(k: K, v: VagaCreate[K]) {
    setF((prev) => ({ ...prev, [k]: v }));
  }

  return (
    <div className="card p-6 mb-5">
      {erro && (
        <div className="text-[13px] text-brand-ink bg-brand-soft/60 border border-brand/30 rounded p-3 mb-4">
          {erro}
        </div>
      )}
      <div className="grid md:grid-cols-2 gap-4">
        <Campo label="Título da vaga" obrigatorio>
          <input
            className="input"
            value={f.titulo}
            onChange={(e) => set('titulo', e.target.value)}
          />
        </Campo>
        <Campo label="Empresa">
          <input
            className="input"
            value={f.empresa ?? ''}
            onChange={(e) => set('empresa', e.target.value)}
          />
        </Campo>
        <Campo label="Link da vaga">
          <input
            className="input"
            value={f.link ?? ''}
            onChange={(e) => set('link', e.target.value)}
          />
        </Campo>
        <Campo label="E-mail de contato">
          <input
            className="input"
            value={f.contato_email ?? ''}
            onChange={(e) => set('contato_email', e.target.value)}
          />
        </Campo>
        <Campo label="Modelo (remoto/híbrido/presencial)">
          <input
            className="input"
            value={f.modelo ?? ''}
            onChange={(e) => set('modelo', e.target.value)}
          />
        </Campo>
        <Campo label="Senioridade">
          <input
            className="input"
            value={f.senioridade ?? ''}
            onChange={(e) => set('senioridade', e.target.value)}
          />
        </Campo>
      </div>
      <div className="mt-4">
        <Campo label="Descrição da vaga (cole aqui)" obrigatorio>
          <textarea
            className="input resize-y min-h-[140px]"
            value={f.descricao}
            onChange={(e) => set('descricao', e.target.value)}
          />
        </Campo>
      </div>
      <div className="flex justify-end mt-4">
        <button
          type="button"
          className="btn-primary disabled:opacity-40"
          onClick={() => onSubmit(f)}
          disabled={loading}
        >
          {loading ? 'Salvando…' : 'Registrar vaga'}
        </button>
      </div>
    </div>
  );
}


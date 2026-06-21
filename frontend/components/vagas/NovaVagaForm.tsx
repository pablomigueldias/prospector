import { useState } from 'react';

import { type ExtrairVaga, type VagaCreate } from '@/lib/types';
import { Campo } from './_shared';

// ── Form de nova vaga ─────────────────────────────────────────────

export function NovaVagaForm({
  onSubmit,
  onExtrair,
  loading,
  erro,
}: {
  onSubmit: (body: VagaCreate) => void;
  onExtrair: (origem: { texto?: string; url?: string }) => Promise<ExtrairVaga | null>;
  loading: boolean;
  erro: string | null;
}) {
  const [f, setF] = useState<VagaCreate>({ titulo: '', descricao: '' });
  const [extraindo, setExtraindo] = useState(false);
  const [importando, setImportando] = useState(false);

  function set<K extends keyof VagaCreate>(k: K, v: VagaCreate[K]) {
    setF((prev) => ({ ...prev, [k]: v }));
  }

  /** Preenche os campos com o que a IA extraiu (sem sobrescrever o que já tem). */
  function aplicar(r: ExtrairVaga) {
    setF((prev) => ({
      ...prev,
      titulo: prev.titulo.trim() || r.titulo || prev.titulo,
      descricao: prev.descricao.trim() || r.descricao || prev.descricao,
      link: prev.link?.trim() || r.link || prev.link,
      empresa: prev.empresa?.trim() || r.empresa || prev.empresa,
      localizacao: prev.localizacao?.trim() || r.localizacao || prev.localizacao,
      modelo: prev.modelo?.trim() || r.modelo || prev.modelo,
      senioridade: prev.senioridade?.trim() || r.senioridade || prev.senioridade,
    }));
  }

  async function importarDaUrl() {
    if (!f.link?.trim()) return;
    setImportando(true);
    const r = await onExtrair({ url: f.link.trim() });
    setImportando(false);
    if (r) aplicar(r);
  }

  async function autoPreencher() {
    if (!f.descricao.trim()) return;
    setExtraindo(true);
    const r = await onExtrair({ texto: f.descricao.trim() });
    setExtraindo(false);
    if (r) aplicar(r);
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
        <div>
          <div className="flex items-center justify-between gap-2 mb-1">
            <span className="text-[13px] text-ink-soft font-medium">Link da vaga</span>
            <button
              type="button"
              className="btn-ghost text-[12px] px-2 py-1 disabled:opacity-40"
              onClick={importarDaUrl}
              disabled={importando || !f.link?.trim()}
              title="Busca a página, lê o texto e preenche descrição, título, empresa, localização, modelo e senioridade"
            >
              {importando ? 'Importando…' : '🔗 Importar da URL'}
            </button>
          </div>
          <input
            className="input"
            value={f.link ?? ''}
            placeholder="https://…"
            onChange={(e) => set('link', e.target.value)}
          />
        </div>
        <Campo label="E-mail de contato">
          <input
            className="input"
            value={f.contato_email ?? ''}
            onChange={(e) => set('contato_email', e.target.value)}
          />
        </Campo>
        <Campo label="Localização">
          <input
            className="input"
            value={f.localizacao ?? ''}
            onChange={(e) => set('localizacao', e.target.value)}
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
        <div className="flex items-center justify-between gap-2 mb-1">
          <span className="text-[13px] text-ink-soft font-medium">
            Descrição da vaga (cole aqui) <span className="text-brand">*</span>
          </span>
          <button
            type="button"
            className="btn-ghost text-[12px] px-2 py-1 disabled:opacity-40"
            onClick={autoPreencher}
            disabled={extraindo || !f.descricao.trim()}
            title="A IA lê o texto colado e preenche título, empresa, localização, modelo e senioridade"
          >
            {extraindo ? 'Lendo…' : '✨ Auto-preencher do texto'}
          </button>
        </div>
        <textarea
          className="input resize-y min-h-[140px]"
          value={f.descricao}
          onChange={(e) => set('descricao', e.target.value)}
        />
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

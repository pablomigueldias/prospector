import { useState } from 'react';

import { Campo } from '@/components/crm/_crmShared';
import { Modal } from '@/components/shared/Modal';
import { api } from '@/lib/api';
import type {
  ContatoListItem,
  ContatoUpsert,
  EmpresaListItem,
} from '@/lib/types';

function vazio(empresaId = ''): ContatoUpsert {
  return {
    empresa_id: empresaId,
    nome: '',
    cargo: '',
    decisor: false,
    email: '',
    telefone: '',
    whatsapp: '',
    linkedin: '',
    origem_contato: '',
  };
}

function deItem(c: ContatoListItem): ContatoUpsert {
  return {
    empresa_id: c.empresa_id,
    nome: c.nome,
    cargo: c.cargo ?? '',
    decisor: c.decisor,
    email: c.email ?? '',
    telefone: c.telefone ?? '',
    whatsapp: c.whatsapp ?? '',
    linkedin: c.linkedin ?? '',
    origem_contato: c.origem_contato ?? '',
  };
}

export function ContatoForm({
  contato,
  inicial,
  empresas,
  onClose,
  onSaved,
}: {
  contato?: ContatoListItem | null;
  inicial?: Partial<ContatoUpsert>;
  empresas: EmpresaListItem[];
  onClose: () => void;
  onSaved: () => void;
}) {
  const editando = !!contato;
  const [form, setForm] = useState<ContatoUpsert>(
    contato ? deItem(contato) : { ...vazio(), ...inicial },
  );
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  function set<K extends keyof ContatoUpsert>(k: K, v: ContatoUpsert[K]) {
    setForm((f) => ({ ...f, [k]: v }));
  }

  async function salvar() {
    setErro(null);
    if (!form.nome.trim()) {
      setErro('Nome é obrigatório.');
      return;
    }
    if (!form.empresa_id) {
      setErro('Escolha a empresa do contato.');
      return;
    }
    setSalvando(true);
    try {
      if (editando && contato) {
        await api.crmContatoSalvar(contato.id, form);
      } else {
        await api.crmContatoCriar(form);
      }
      onSaved();
      onClose();
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Falha ao salvar.');
    } finally {
      setSalvando(false);
    }
  }

  return (
    <Modal open onClose={onClose} title={editando ? 'Editar contato' : 'Novo contato'}>
      <div className="flex flex-col gap-4">
        <div className="grid md:grid-cols-2 gap-4">
          <Campo label="Empresa *" span2>
            <select
              className="input"
              value={form.empresa_id}
              onChange={(e) => set('empresa_id', e.target.value)}
            >
              <option value="">— escolha —</option>
              {empresas.map((e) => (
                <option key={e.id} value={e.id}>
                  {e.nome}
                </option>
              ))}
            </select>
          </Campo>
          <Campo label="Nome *">
            <input
              className="input"
              value={form.nome}
              onChange={(e) => set('nome', e.target.value)}
            />
          </Campo>
          <Campo label="Cargo">
            <input
              className="input"
              value={form.cargo ?? ''}
              onChange={(e) => set('cargo', e.target.value)}
            />
          </Campo>
          <Campo label="E-mail">
            <input
              className="input"
              value={form.email ?? ''}
              onChange={(e) => set('email', e.target.value)}
            />
          </Campo>
          <Campo label="Telefone">
            <input
              className="input"
              value={form.telefone ?? ''}
              onChange={(e) => set('telefone', e.target.value)}
            />
          </Campo>
          <Campo label="WhatsApp">
            <input
              className="input"
              value={form.whatsapp ?? ''}
              onChange={(e) => set('whatsapp', e.target.value)}
            />
          </Campo>
          <Campo label="LinkedIn">
            <input
              className="input"
              value={form.linkedin ?? ''}
              onChange={(e) => set('linkedin', e.target.value)}
            />
          </Campo>
          <Campo label="Origem">
            <input
              className="input"
              value={form.origem_contato ?? ''}
              onChange={(e) => set('origem_contato', e.target.value)}
            />
          </Campo>
        </div>

        <label className="flex items-center gap-2 text-[13px] text-ink">
          <input
            type="checkbox"
            checked={form.decisor}
            onChange={(e) => set('decisor', e.target.checked)}
          />
          É decisor
        </label>

        {erro && <p className="text-[13px] text-red-600 m-0">{erro}</p>}

        <div className="flex justify-end gap-3 pt-1">
          <button type="button" className="btn-ghost" onClick={onClose}>
            Cancelar
          </button>
          <button
            type="button"
            className="btn-primary disabled:opacity-40"
            onClick={salvar}
            disabled={salvando}
          >
            {salvando ? 'Salvando…' : editando ? 'Salvar' : 'Criar'}
          </button>
        </div>
      </div>
    </Modal>
  );
}

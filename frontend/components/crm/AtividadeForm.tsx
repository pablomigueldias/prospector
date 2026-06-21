import { useState } from 'react';

import { Campo, SelectCampo } from '@/components/crm/_crmShared';
import { Modal } from '@/components/shared/Modal';
import { useFetch } from '@/hooks/useFetch';
import { api } from '@/lib/api';
import type { AtividadeListItem, AtividadeUpsert } from '@/lib/types';

// O backend aceita ISO (date ou datetime). O input datetime-local dá
// "YYYY-MM-DDTHH:mm" — válido como ISO.
function vazio(): AtividadeUpsert {
  return {
    titulo: '',
    tipo: '',
    status: '🟡 Agendada',
    data: '',
    resumo: '',
    proximos_passos: '',
    negocio_id: '',
    contato_id: '',
  };
}

function deItem(a: AtividadeListItem): AtividadeUpsert {
  return {
    titulo: a.titulo,
    tipo: a.tipo ?? '',
    status: a.status ?? '',
    data: a.data ? a.data.slice(0, 16) : '',
    resumo: a.resumo ?? '',
    proximos_passos: a.proximos_passos ?? '',
    negocio_id: a.negocio_id ?? '',
    contato_id: '',
  };
}

export function AtividadeForm({
  atividade,
  inicial,
  onClose,
  onSaved,
}: {
  atividade?: AtividadeListItem | null;
  inicial?: Partial<AtividadeUpsert>;
  onClose: () => void;
  onSaved: () => void;
}) {
  const editando = !!atividade;
  const [form, setForm] = useState<AtividadeUpsert>(
    atividade ? deItem(atividade) : { ...vazio(), ...inicial },
  );
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  const { data: negocios } = useFetch(() => api.crmNegocios(), []);
  const { data: contatosResp } = useFetch(() => api.crmContatos({ limit: 500 }), []);
  const { data: opcoes } = useFetch(() => api.crmOpcoes(), []);
  const contatos = contatosResp?.items ?? [];

  function set<K extends keyof AtividadeUpsert>(k: K, v: AtividadeUpsert[K]) {
    setForm((f) => ({ ...f, [k]: v }));
  }

  async function salvar() {
    setErro(null);
    if (!form.titulo.trim()) {
      setErro('Título é obrigatório.');
      return;
    }
    setSalvando(true);
    try {
      if (editando && atividade) await api.crmAtividadeSalvar(atividade.id, form);
      else await api.crmAtividadeCriar(form);
      onSaved();
      onClose();
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Falha ao salvar.');
    } finally {
      setSalvando(false);
    }
  }

  return (
    <Modal open onClose={onClose} title={editando ? 'Editar atividade' : 'Nova atividade'}>
      <div className="flex flex-col gap-4">
        <div className="grid md:grid-cols-2 gap-4">
          <Campo label="Título *" span2>
            <input
              className="input"
              value={form.titulo}
              onChange={(e) => set('titulo', e.target.value)}
            />
          </Campo>
          <SelectCampo
            label="Tipo"
            value={form.tipo}
            opcoes={opcoes?.atividade_tipo}
            onChange={(v) => set('tipo', v)}
          />
          <SelectCampo
            label="Status"
            value={form.status}
            opcoes={opcoes?.atividade_status}
            onChange={(v) => set('status', v)}
          />
          <Campo label="Quando">
            <input
              className="input"
              type="datetime-local"
              value={form.data ?? ''}
              onChange={(e) => set('data', e.target.value)}
            />
          </Campo>
          <Campo label="Negócio">
            <select
              className="input"
              value={form.negocio_id ?? ''}
              onChange={(e) => set('negocio_id', e.target.value)}
            >
              <option value="">—</option>
              {(negocios ?? []).map((n) => (
                <option key={n.id} value={n.id}>
                  {n.nome}
                </option>
              ))}
            </select>
          </Campo>
          <Campo label="Contato">
            <select
              className="input"
              value={form.contato_id ?? ''}
              onChange={(e) => set('contato_id', e.target.value)}
            >
              <option value="">—</option>
              {contatos.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.nome}
                </option>
              ))}
            </select>
          </Campo>
        </div>
        <Campo label="Resumo">
          <textarea
            className="input resize-y min-h-[60px]"
            value={form.resumo ?? ''}
            onChange={(e) => set('resumo', e.target.value)}
          />
        </Campo>
        <Campo label="Próximos passos">
          <textarea
            className="input resize-y min-h-[60px]"
            value={form.proximos_passos ?? ''}
            onChange={(e) => set('proximos_passos', e.target.value)}
          />
        </Campo>

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

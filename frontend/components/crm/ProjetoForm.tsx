import { useState } from 'react';

import { Campo, SelectCampo } from '@/components/crm/_crmShared';
import { Modal } from '@/components/shared/Modal';
import { useFetch } from '@/hooks/useFetch';
import { api } from '@/lib/api';
import type { ProjetoListItem, ProjetoUpsert } from '@/lib/types';

function vazio(): ProjetoUpsert {
  return {
    nome: '',
    status: '🚀 Em produção',
    tipo_servico: '',
    valor_total: null,
    valor_recebido: null,
    briefing: '',
    link_producao: '',
    repo_github: '',
    forma_pagamento: '',
    prazo_entrega: '',
    data_inicio: '',
    data_entrega_real: '',
    empresa_id: '',
    negocio_id: '',
  };
}

function deItem(p: ProjetoListItem): ProjetoUpsert {
  return {
    nome: p.nome,
    status: p.status ?? '',
    tipo_servico: p.tipo_servico ?? '',
    valor_total: p.valor_total ?? null,
    valor_recebido: p.valor_recebido ?? null,
    briefing: p.briefing ?? '',
    link_producao: p.link_producao ?? '',
    repo_github: p.repo_github ?? '',
    forma_pagamento: '',
    prazo_entrega: p.prazo_entrega ?? '',
    data_inicio: '',
    data_entrega_real: p.data_entrega_real ?? '',
    empresa_id: '',
    negocio_id: '',
  };
}

export function ProjetoForm({
  projeto,
  inicial,
  onClose,
  onSaved,
}: {
  projeto?: ProjetoListItem | null;
  inicial?: Partial<ProjetoUpsert>;
  onClose: () => void;
  onSaved: () => void;
}) {
  const editando = !!projeto;
  const [form, setForm] = useState<ProjetoUpsert>(
    projeto ? deItem(projeto) : { ...vazio(), ...inicial },
  );
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  const { data: empresasResp } = useFetch(
    () => api.crmEmpresas({ limit: 500, ordenar_por: 'nome' }),
    [],
  );
  const { data: negocios } = useFetch(() => api.crmNegocios(), []);
  const { data: opcoes } = useFetch(() => api.crmOpcoes(), []);
  const empresas = empresasResp?.items ?? [];

  function set<K extends keyof ProjetoUpsert>(k: K, v: ProjetoUpsert[K]) {
    setForm((f) => ({ ...f, [k]: v }));
  }

  async function salvar() {
    setErro(null);
    if (!form.nome.trim()) {
      setErro('Nome é obrigatório.');
      return;
    }
    setSalvando(true);
    try {
      if (editando && projeto) await api.crmProjetoSalvar(projeto.id, form);
      else await api.crmProjetoCriar(form);
      onSaved();
      onClose();
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Falha ao salvar.');
    } finally {
      setSalvando(false);
    }
  }

  return (
    <Modal open onClose={onClose} title={editando ? 'Editar projeto' : 'Novo projeto'}>
      <div className="flex flex-col gap-4">
        <div className="grid md:grid-cols-2 gap-4">
          <Campo label="Nome *" span2>
            <input
              className="input"
              value={form.nome}
              onChange={(e) => set('nome', e.target.value)}
            />
          </Campo>
          <SelectCampo
            label="Status"
            value={form.status}
            opcoes={opcoes?.projeto_status}
            onChange={(v) => set('status', v)}
          />
          <SelectCampo
            label="Tipo de serviço"
            value={form.tipo_servico}
            opcoes={opcoes?.tipo_servico}
            onChange={(v) => set('tipo_servico', v)}
          />
          <SelectCampo
            label="Forma de pagamento"
            value={form.forma_pagamento}
            opcoes={opcoes?.forma_pagamento}
            onChange={(v) => set('forma_pagamento', v)}
          />
          <Campo label="Valor total (R$)">
            <input
              className="input"
              type="number"
              value={form.valor_total ?? ''}
              onChange={(e) =>
                set('valor_total', e.target.value ? Number(e.target.value) : null)
              }
            />
          </Campo>
          <Campo label="Valor recebido (R$)">
            <input
              className="input"
              type="number"
              value={form.valor_recebido ?? ''}
              onChange={(e) =>
                set('valor_recebido', e.target.value ? Number(e.target.value) : null)
              }
            />
          </Campo>
          <Campo label="Empresa">
            <select
              className="input"
              value={form.empresa_id ?? ''}
              onChange={(e) => set('empresa_id', e.target.value)}
            >
              <option value="">—</option>
              {empresas.map((e) => (
                <option key={e.id} value={e.id}>
                  {e.nome}
                </option>
              ))}
            </select>
          </Campo>
          <Campo label="Negócio origem">
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
          <Campo label="Prazo de entrega">
            <input
              className="input"
              type="date"
              value={form.prazo_entrega ?? ''}
              onChange={(e) => set('prazo_entrega', e.target.value)}
            />
          </Campo>
          <Campo label="Data entrega real">
            <input
              className="input"
              type="date"
              value={form.data_entrega_real ?? ''}
              onChange={(e) => set('data_entrega_real', e.target.value)}
            />
          </Campo>
          <Campo label="Link produção">
            <input
              className="input"
              value={form.link_producao ?? ''}
              onChange={(e) => set('link_producao', e.target.value)}
            />
          </Campo>
          <Campo label="Repo GitHub">
            <input
              className="input"
              value={form.repo_github ?? ''}
              onChange={(e) => set('repo_github', e.target.value)}
            />
          </Campo>
        </div>
        <Campo label="Briefing">
          <textarea
            className="input resize-y min-h-[70px]"
            value={form.briefing ?? ''}
            onChange={(e) => set('briefing', e.target.value)}
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

import { useState } from 'react';

import { Campo, MultiCampo, SelectCampo } from '@/components/crm/_crmShared';
import { SidePanel } from '@/components/shared/SidePanel';
import { useFetch } from '@/hooks/useFetch';
import { api } from '@/lib/api';
import type { NegocioListItem, NegocioUpsert } from '@/lib/types';

function vazio(): NegocioUpsert {
  return {
    nome: '',
    estagio: '⚪ Lead novo',
    valor_estimado: null,
    probabilidade: '',
    origem: '',
    tipo_servico: [],
    notas: '',
    motivo_perda: '',
    previsao_fechamento: '',
    proxima_acao: '',
    empresa_id: '',
    contato_id: '',
  };
}

function deItem(n: NegocioListItem): NegocioUpsert {
  return {
    nome: n.nome,
    estagio: n.estagio ?? '',
    valor_estimado: n.valor_estimado ?? null,
    probabilidade: n.probabilidade ?? '',
    origem: n.origem ?? '',
    tipo_servico: n.tipo_servico ?? [],
    notas: n.notas ?? '',
    motivo_perda: '',
    previsao_fechamento: n.previsao_fechamento ?? '',
    proxima_acao: n.proxima_acao ?? '',
    empresa_id: n.empresa_id ?? '',
    contato_id: '',
  };
}

export function NegocioForm({
  negocio,
  inicial,
  onClose,
  onSaved,
}: {
  negocio?: NegocioListItem | null;
  inicial?: Partial<NegocioUpsert>;
  onClose: () => void;
  onSaved: () => void;
}) {
  const editando = !!negocio;
  const [form, setForm] = useState<NegocioUpsert>(
    negocio ? deItem(negocio) : { ...vazio(), ...inicial },
  );
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  const { data: empresasResp } = useFetch(
    () => api.crmEmpresas({ limit: 500, ordenar_por: 'nome' }),
    [],
  );
  const { data: contatosResp } = useFetch(() => api.crmContatos({ limit: 500 }), []);
  const { data: opcoes } = useFetch(() => api.crmOpcoes(), []);
  const empresas = empresasResp?.items ?? [];
  const contatos = contatosResp?.items ?? [];

  function set<K extends keyof NegocioUpsert>(k: K, v: NegocioUpsert[K]) {
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
      if (editando && negocio) await api.crmNegocioSalvar(negocio.id, form);
      else await api.crmNegocioCriar(form);
      onSaved();
      onClose();
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Falha ao salvar.');
    } finally {
      setSalvando(false);
    }
  }

  return (
    <SidePanel open onClose={onClose} title={editando ? 'Editar negócio' : 'Novo negócio'}>
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
            label="Estágio"
            value={form.estagio}
            opcoes={opcoes?.estagio}
            onChange={(v) => set('estagio', v)}
          />
          <Campo label="Valor estimado (R$)">
            <input
              className="input"
              type="number"
              value={form.valor_estimado ?? ''}
              onChange={(e) =>
                set('valor_estimado', e.target.value ? Number(e.target.value) : null)
              }
            />
          </Campo>
          <SelectCampo
            label="Probabilidade"
            value={form.probabilidade}
            opcoes={opcoes?.probabilidade}
            onChange={(v) => set('probabilidade', v)}
          />
          <SelectCampo
            label="Origem"
            value={form.origem}
            opcoes={opcoes?.origem_negocio}
            onChange={(v) => set('origem', v)}
          />
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
          <Campo label="Contato principal">
            <select
              className="input"
              value={form.contato_id ?? ''}
              onChange={(e) => set('contato_id', e.target.value)}
            >
              <option value="">—</option>
              {contatos.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.nome}
                  {c.empresa_nome ? ` (${c.empresa_nome})` : ''}
                </option>
              ))}
            </select>
          </Campo>
          <Campo label="Previsão fechamento">
            <input
              className="input"
              type="date"
              value={form.previsao_fechamento ?? ''}
              onChange={(e) => set('previsao_fechamento', e.target.value)}
            />
          </Campo>
          <Campo label="Próxima ação">
            <input
              className="input"
              type="date"
              value={form.proxima_acao ?? ''}
              onChange={(e) => set('proxima_acao', e.target.value)}
            />
          </Campo>
        </div>
        <MultiCampo
          label="Tipo de serviço"
          valores={form.tipo_servico ?? []}
          opcoes={opcoes?.tipo_servico}
          onChange={(v) => set('tipo_servico', v)}
        />
        <Campo label="Notas">
          <textarea
            className="input resize-y min-h-[70px]"
            value={form.notas ?? ''}
            onChange={(e) => set('notas', e.target.value)}
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
    </SidePanel>
  );
}

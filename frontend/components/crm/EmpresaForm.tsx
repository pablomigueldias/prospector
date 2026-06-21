import { useState } from 'react';

import { Campo, SelectCampo } from '@/components/crm/_crmShared';
import { Modal } from '@/components/shared/Modal';
import { useFetch } from '@/hooks/useFetch';
import { api } from '@/lib/api';
import type { EmpresaDetalhe, EmpresaUpsert } from '@/lib/types';

const VAZIO: EmpresaUpsert = {
  nome: '',
  razao_social: '',
  cnpj: '',
  site: '',
  cidade: '',
  estado: '',
  setor: '',
  tamanho: '',
  status: '',
  como_conheceu: '',
  score: null,
  notas: '',
};

function deDetalhe(e: EmpresaDetalhe): EmpresaUpsert {
  return {
    nome: e.nome,
    razao_social: e.razao_social ?? '',
    cnpj: e.cnpj ?? '',
    site: e.site ?? '',
    cidade: e.cidade ?? '',
    estado: e.estado ?? '',
    setor: e.setor ?? '',
    tamanho: e.tamanho ?? '',
    status: e.status ?? '',
    como_conheceu: e.como_conheceu ?? '',
    score: e.score ?? null,
    notas: e.notas ?? '',
  };
}

export function EmpresaForm({
  empresa,
  onClose,
  onSaved,
}: {
  empresa?: EmpresaDetalhe | null;
  onClose: () => void;
  onSaved: () => void;
}) {
  const editando = !!empresa;
  const [form, setForm] = useState<EmpresaUpsert>(
    empresa ? deDetalhe(empresa) : VAZIO,
  );
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const { data: opcoes } = useFetch(() => api.crmOpcoes(), []);

  function set<K extends keyof EmpresaUpsert>(k: K, v: EmpresaUpsert[K]) {
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
      if (editando && empresa) {
        await api.crmEmpresaSalvar(empresa.id, form);
      } else {
        await api.crmEmpresaCriar(form);
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
    <Modal open onClose={onClose} title={editando ? 'Editar empresa' : 'Nova empresa'}>
      <div className="flex flex-col gap-4">
        <div className="grid md:grid-cols-2 gap-4">
          <Campo label="Nome *" span2>
            <input
              className="input"
              value={form.nome}
              onChange={(e) => set('nome', e.target.value)}
            />
          </Campo>
          <Campo label="Razão social">
            <input
              className="input"
              value={form.razao_social ?? ''}
              onChange={(e) => set('razao_social', e.target.value)}
            />
          </Campo>
          <Campo label="CNPJ">
            <input
              className="input"
              value={form.cnpj ?? ''}
              onChange={(e) => set('cnpj', e.target.value)}
            />
          </Campo>
          <Campo label="Site">
            <input
              className="input"
              value={form.site ?? ''}
              onChange={(e) => set('site', e.target.value)}
            />
          </Campo>
          <SelectCampo
            label="Status"
            value={form.status}
            opcoes={opcoes?.status}
            onChange={(v) => set('status', v)}
          />
          <SelectCampo
            label="Setor"
            value={form.setor}
            opcoes={opcoes?.setor}
            onChange={(v) => set('setor', v)}
          />
          <SelectCampo
            label="Tamanho"
            value={form.tamanho}
            opcoes={opcoes?.tamanho}
            onChange={(v) => set('tamanho', v)}
          />
          <Campo label="Cidade">
            <input
              className="input"
              value={form.cidade ?? ''}
              onChange={(e) => set('cidade', e.target.value)}
            />
          </Campo>
          <SelectCampo
            label="Estado"
            value={form.estado}
            opcoes={opcoes?.estado}
            onChange={(v) => set('estado', v)}
          />
          <SelectCampo
            label="Como conheceu"
            value={form.como_conheceu}
            opcoes={opcoes?.como_conheceu}
            onChange={(v) => set('como_conheceu', v)}
          />
          <Campo label="Score (0-100)">
            <input
              className="input"
              type="number"
              value={form.score ?? ''}
              onChange={(e) =>
                set('score', e.target.value ? Number(e.target.value) : null)
              }
            />
          </Campo>
        </div>
        <Campo label="Notas">
          <textarea
            className="input resize-y min-h-[80px]"
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
    </Modal>
  );
}

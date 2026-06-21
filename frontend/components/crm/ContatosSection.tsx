import { useState } from 'react';

import { ConfirmarExclusao } from '@/components/crm/_crmShared';
import { ContatoForm } from '@/components/crm/ContatoForm';
import { InlineCell } from '@/components/crm/InlineCell';
import { RecordModal } from '@/components/crm/RecordModal';
import { useFetch } from '@/hooks/useFetch';
import { api } from '@/lib/api';
import type {
  ContatoListItem,
  ContatosFiltro,
  EmpresaListItem,
} from '@/lib/types';

export function ContatosSection({ onChanged }: { onChanged: () => void }) {
  const [filtros, setFiltros] = useState<ContatosFiltro>({});
  const [versao, setVersao] = useState(0);
  const [novo, setNovo] = useState(false);
  const [editar, setEditar] = useState<ContatoListItem | null>(null);
  const [ver, setVer] = useState<ContatoListItem | null>(null);
  const [excluir, setExcluir] = useState<ContatoListItem | null>(null);
  const [excluindo, setExcluindo] = useState(false);

  const { data: empresasResp } = useFetch(
    () => api.crmEmpresas({ limit: 500, ordenar_por: 'nome' }),
    [],
  );
  const empresas: EmpresaListItem[] = empresasResp?.items ?? [];

  const filtroKey = JSON.stringify(filtros);
  const { data: lista, loading } = useFetch(
    () => api.crmContatos({ ...filtros, limit: 500 }),
    [filtroKey, versao],
  );
  const contatos = lista?.items ?? [];

  function setF<K extends keyof ContatosFiltro>(k: K, v: ContatosFiltro[K]) {
    setFiltros((f) => ({ ...f, [k]: v === '' || v === undefined ? undefined : v }));
  }

  function recarregar() {
    setVersao((v) => v + 1);
    onChanged();
  }

  async function confirmarExclusao() {
    if (!excluir) return;
    setExcluindo(true);
    try {
      await api.crmContatoExcluir(excluir.id);
      setExcluir(null);
      recarregar();
    } finally {
      setExcluindo(false);
    }
  }

  return (
    <div>
      <div className="flex flex-wrap items-end gap-2 mb-4">
        <input
          className="input max-w-[220px]"
          placeholder="Buscar nome/cargo/email…"
          value={filtros.busca ?? ''}
          onChange={(e) => setF('busca', e.target.value)}
        />
        <select
          className="input max-w-[220px]"
          value={filtros.empresa_id ?? ''}
          onChange={(e) => setF('empresa_id', e.target.value)}
        >
          <option value="">Empresa: todas</option>
          {empresas.map((e) => (
            <option key={e.id} value={e.id}>
              {e.nome}
            </option>
          ))}
        </select>
        <select
          className="input max-w-[160px]"
          value={filtros.decisor === undefined ? '' : String(filtros.decisor)}
          onChange={(e) =>
            setFiltros((f) => ({
              ...f,
              decisor: e.target.value === '' ? undefined : e.target.value === 'true',
            }))
          }
        >
          <option value="">Decisor: todos</option>
          <option value="true">Só decisores</option>
          <option value="false">Não-decisores</option>
        </select>
        {(filtros.busca || filtros.empresa_id || filtros.decisor !== undefined) && (
          <button
            type="button"
            className="text-[13px] text-ink-mute hover:text-ink underline px-1 py-2"
            onClick={() => setFiltros({})}
          >
            limpar
          </button>
        )}
        <button
          type="button"
          className="btn-primary !px-4 !py-2 !text-[13px] ml-auto"
          onClick={() => setNovo(true)}
        >
          + Novo contato
        </button>
      </div>

      {loading ? (
        <div className="card p-8 animate-pulse h-48" />
      ) : contatos.length === 0 ? (
        <div className="card p-8 text-center text-ink-soft">
          Nenhum contato bate com os filtros.
        </div>
      ) : (
        <div className="card overflow-x-auto p-0">
          <table className="w-full border-collapse text-[13px]">
            <thead>
              <tr className="border-b border-line text-left text-ink-mute">
                <th className="font-medium px-4 py-2.5">Nome</th>
                <th className="font-medium px-4 py-2.5">Cargo</th>
                <th className="font-medium px-4 py-2.5">Empresa</th>
                <th className="font-medium px-4 py-2.5">E-mail</th>
                <th className="font-medium px-4 py-2.5">WhatsApp</th>
                <th className="font-medium px-4 py-2.5 text-right">Ações</th>
              </tr>
            </thead>
            <tbody>
              {contatos.map((c) => (
                <tr
                  key={c.id}
                  onClick={() => setVer(c)}
                  className="border-b border-line/60 last:border-0 hover:bg-bg-alt cursor-pointer"
                >
                  <td className="px-4 py-2.5 font-medium text-ink">
                    {c.nome}
                    {c.decisor && (
                      <span className="ml-2 text-[10px] uppercase tracking-wide bg-brand-soft text-brand px-1.5 py-0.5 rounded-sm">
                        decisor
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-2.5 text-ink-soft">
                    <InlineCell
                      tipo="contato"
                      id={c.id}
                      campo="cargo"
                      valor={c.cargo}
                      onSaved={recarregar}
                    />
                  </td>
                  <td className="px-4 py-2.5 text-ink-soft">
                    {c.empresa_nome ?? '—'}
                  </td>
                  <td className="px-4 py-2.5 text-ink-mute font-mono text-[12px]">
                    <InlineCell
                      tipo="contato"
                      id={c.id}
                      campo="email"
                      valor={c.email}
                      onSaved={recarregar}
                    />
                  </td>
                  <td className="px-4 py-2.5 text-ink-soft">
                    <InlineCell
                      tipo="contato"
                      id={c.id}
                      campo="whatsapp"
                      valor={c.whatsapp}
                      onSaved={recarregar}
                    />
                  </td>
                  <td className="px-4 py-2.5 text-right whitespace-nowrap">
                    <button
                      type="button"
                      className="text-ink-mute hover:text-red-600 text-[12px]"
                      onClick={(ev) => {
                        ev.stopPropagation();
                        setExcluir(c);
                      }}
                    >
                      excluir
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <p className="text-[12px] text-ink-mute mt-3">
        {contatos.length} contato(s){lista ? ` · ${lista.total} no total` : ''}
      </p>

      {ver && (
        <RecordModal
          tipo="contato"
          id={ver.id}
          onClose={() => setVer(null)}
          onChanged={recarregar}
          onEditar={() => {
            const c = ver;
            setVer(null);
            setEditar(c);
          }}
        />
      )}
      {(novo || editar) && (
        <ContatoForm
          contato={editar}
          empresas={empresas}
          onClose={() => {
            setNovo(false);
            setEditar(null);
          }}
          onSaved={recarregar}
        />
      )}
      {excluir && (
        <ConfirmarExclusao
          titulo="Excluir contato"
          alvo={excluir.nome}
          carregando={excluindo}
          onConfirmar={confirmarExclusao}
          onCancelar={() => setExcluir(null)}
        />
      )}
    </div>
  );
}

import { useState } from 'react';

import {
  ConfirmarExclusao,
  KanbanGenerico,
  VistaToggle,
} from '@/components/crm/_crmShared';
import { InlineCell } from '@/components/crm/InlineCell';
import { ProjetoForm } from '@/components/crm/ProjetoForm';
import { RecordModal } from '@/components/crm/RecordModal';
import { useFetch } from '@/hooks/useFetch';
import { api } from '@/lib/api';
import type { ProjetoListItem, ProjetoListResponse } from '@/lib/types';

function brl(v?: number | null): string {
  if (v == null) return '—';
  return v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}

export function ProjetosSection() {
  const [versao, setVersao] = useState(0);
  const [novo, setNovo] = useState(false);
  const [editar, setEditar] = useState<ProjetoListItem | null>(null);
  const [ver, setVer] = useState<ProjetoListItem | null>(null);
  const [excluir, setExcluir] = useState<ProjetoListItem | null>(null);
  const [excluindo, setExcluindo] = useState(false);
  const [vista, setVista] = useState<'lista' | 'kanban'>('lista');

  const { data, loading } = useFetch<ProjetoListResponse>(
    () => api.crmProjetos(),
    [versao],
  );
  const { data: opcoes } = useFetch(() => api.crmOpcoes(), []);
  const { data: cores } = useFetch(() => api.crmOpcoesCores(), []);

  function recarregar() {
    setVersao((v) => v + 1);
  }

  async function confirmarExclusao() {
    if (!excluir) return;
    setExcluindo(true);
    try {
      await api.crmProjetoExcluir(excluir.id);
      setExcluir(null);
      recarregar();
    } finally {
      setExcluindo(false);
    }
  }

  const cabecalho = (
    <div className="flex items-center justify-end gap-2 mb-4">
      <VistaToggle
        vista={vista}
        vistas={[
          { id: 'lista', label: 'Lista' },
          { id: 'kanban', label: 'Kanban' },
        ]}
        onChange={setVista}
      />
      <button
        type="button"
        className="btn-primary !px-4 !py-2 !text-[13px]"
        onClick={() => setNovo(true)}
      >
        + Novo projeto
      </button>
    </div>
  );

  const modais = (
    <>
      {ver && (
        <RecordModal
          tipo="projeto"
          id={ver.id}
          onClose={() => setVer(null)}
          onChanged={recarregar}
          onEditar={() => {
            const p = ver;
            setVer(null);
            setEditar(p);
          }}
        />
      )}
      {(novo || editar) && (
        <ProjetoForm
          projeto={editar}
          onClose={() => {
            setNovo(false);
            setEditar(null);
          }}
          onSaved={recarregar}
        />
      )}
      {excluir && (
        <ConfirmarExclusao
          titulo="Excluir projeto"
          alvo={excluir.nome}
          carregando={excluindo}
          onConfirmar={confirmarExclusao}
          onCancelar={() => setExcluir(null)}
        />
      )}
    </>
  );

  if (loading) return <div className="card p-8 animate-pulse h-48" />;
  if (!data || data.items.length === 0) {
    return (
      <div>
        {cabecalho}
        <div className="card p-8 text-center text-ink-soft">
          Nenhum projeto cadastrado ainda.
        </div>
        {modais}
      </div>
    );
  }

  if (vista === 'kanban') {
    return (
      <div>
        {cabecalho}
        <KanbanGenerico
          itens={data.items}
          ordem={opcoes?.projeto_status ?? []}
          statusDe={(p) => p.status}
          cores={cores?.projeto_status}
          semLabel="(sem status)"
          onMover={(p, status) =>
            api.crmRecordPatch('projeto', p.id, { status }).then(recarregar)
          }
          onAbrir={(p) => setVer(p)}
          renderCard={(p) => (
            <>
              <div className="font-medium text-[13.5px] text-ink leading-snug mb-1">
                {p.nome}
              </div>
              {p.empresa_nome && (
                <div className="text-[12px] text-ink-soft truncate">
                  {p.empresa_nome}
                </div>
              )}
              <div className="text-[12px] text-ink-mute mt-1">
                a receber {brl(p.a_receber)}
              </div>
            </>
          )}
        />
        {modais}
      </div>
    );
  }

  return (
    <div>
      {cabecalho}
      <div className="card overflow-x-auto p-0">
        <table className="w-full border-collapse text-[13px]">
          <thead>
            <tr className="border-b border-line text-left text-ink-mute">
              <th className="font-medium px-4 py-2.5">Projeto</th>
              <th className="font-medium px-4 py-2.5">Status</th>
              <th className="font-medium px-4 py-2.5">Empresa</th>
              <th className="font-medium px-4 py-2.5 text-right">Total</th>
              <th className="font-medium px-4 py-2.5 text-right">Recebido</th>
              <th className="font-medium px-4 py-2.5 text-right">A receber</th>
              <th className="font-medium px-4 py-2.5">Prazo</th>
              <th className="font-medium px-4 py-2.5">Links</th>
              <th className="font-medium px-4 py-2.5 text-right">Ações</th>
            </tr>
          </thead>
          <tbody>
            {data.items.map((p) => (
              <tr
                key={p.id}
                onClick={() => setVer(p)}
                className="border-b border-line/60 last:border-0 hover:bg-bg-alt cursor-pointer"
              >
                <td className="px-4 py-2.5 font-medium text-ink">{p.nome}</td>
                <td className="px-4 py-2.5">
                  <InlineCell
                    tipo="projeto"
                    id={p.id}
                    campo="status"
                    valor={p.status}
                    kind="select"
                    opcoes={opcoes?.projeto_status}
                    coresPorValor={cores?.projeto_status}
                    onSaved={recarregar}
                  />
                </td>
                <td className="px-4 py-2.5 text-ink-soft">{p.empresa_nome ?? '—'}</td>
                <td className="px-4 py-2.5 text-right text-ink-soft">
                  <InlineCell
                    tipo="projeto"
                    id={p.id}
                    campo="valor_total"
                    valor={p.valor_total}
                    display={brl(p.valor_total)}
                    kind="num"
                    onSaved={recarregar}
                  />
                </td>
                <td className="px-4 py-2.5 text-right text-ink-soft">
                  <InlineCell
                    tipo="projeto"
                    id={p.id}
                    campo="valor_recebido"
                    valor={p.valor_recebido}
                    display={brl(p.valor_recebido)}
                    kind="num"
                    onSaved={recarregar}
                  />
                </td>
                <td className="px-4 py-2.5 text-right font-medium text-ink">
                  {brl(p.a_receber)}
                </td>
                <td className="px-4 py-2.5 text-ink-soft whitespace-nowrap">
                  <InlineCell
                    tipo="projeto"
                    id={p.id}
                    campo="prazo_entrega"
                    valor={p.prazo_entrega}
                    kind="date"
                    onSaved={recarregar}
                  />
                </td>
                <td
                  className="px-4 py-2.5 whitespace-nowrap"
                  onClick={(ev) => ev.stopPropagation()}
                >
                  {p.link_producao && (
                    <a
                      href={p.link_producao}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-brand hover:underline mr-2"
                    >
                      prod ↗
                    </a>
                  )}
                  {p.repo_github && (
                    <a
                      href={p.repo_github}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-brand hover:underline"
                    >
                      repo ↗
                    </a>
                  )}
                  {!p.link_producao && !p.repo_github && '—'}
                </td>
                <td className="px-4 py-2.5 text-right whitespace-nowrap">
                  <button
                    type="button"
                    className="text-ink-mute hover:text-red-600 text-[12px]"
                    onClick={(ev) => {
                      ev.stopPropagation();
                      setExcluir(p);
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
      {modais}
    </div>
  );
}

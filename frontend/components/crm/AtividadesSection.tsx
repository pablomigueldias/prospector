import { useState } from 'react';

import {
  ConfirmarExclusao,
  KanbanGenerico,
  VistaToggle,
} from '@/components/crm/_crmShared';
import { AtividadeForm } from '@/components/crm/AtividadeForm';
import { InlineCell } from '@/components/crm/InlineCell';
import { RecordModal } from '@/components/crm/RecordModal';
import { useFetch } from '@/hooks/useFetch';
import { api } from '@/lib/api';
import type { AtividadeListItem, AtividadeListResponse } from '@/lib/types';

function fmtData(iso?: string | null): string {
  if (!iso) return '—';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function concluida(status?: string | null): boolean {
  if (!status) return false;
  const s = status.toLowerCase();
  return status.includes('✅') || s.includes('feita') || s.includes('conclu') ||
    s.includes('realizada');
}

function atrasada(a: { data?: string | null; status?: string | null }): boolean {
  if (concluida(a.status) || !a.data) return false;
  const d = new Date(a.data);
  return !Number.isNaN(d.getTime()) && d.getTime() < Date.now();
}

type FiltroAtv = 'todas' | 'pendentes' | 'atrasadas';

export function AtividadesSection() {
  const [versao, setVersao] = useState(0);
  const [novo, setNovo] = useState(false);
  const [editar, setEditar] = useState<AtividadeListItem | null>(null);
  const [ver, setVer] = useState<AtividadeListItem | null>(null);
  const [excluir, setExcluir] = useState<AtividadeListItem | null>(null);
  const [excluindo, setExcluindo] = useState(false);

  const [filtro, setFiltro] = useState<FiltroAtv>('todas');
  const [vista, setVista] = useState<'lista' | 'kanban'>('lista');
  const { data, loading } = useFetch<AtividadeListResponse>(
    () => api.crmAtividades(),
    [versao],
  );
  const { data: opcoes } = useFetch(() => api.crmOpcoes(), []);
  const { data: cores } = useFetch(() => api.crmOpcoesCores(), []);

  function recarregar() {
    setVersao((v) => v + 1);
  }

  const itens = (data?.items ?? []).filter((a) => {
    if (filtro === 'pendentes') return !concluida(a.status);
    if (filtro === 'atrasadas') return atrasada(a);
    return true;
  });
  const nAtrasadas = (data?.items ?? []).filter(atrasada).length;

  async function confirmarExclusao() {
    if (!excluir) return;
    setExcluindo(true);
    try {
      await api.crmAtividadeExcluir(excluir.id);
      setExcluir(null);
      recarregar();
    } finally {
      setExcluindo(false);
    }
  }

  const cabecalho = (
    <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
      <div className="inline-flex rounded-md border border-line overflow-hidden text-[13px]">
        {(
          [
            ['todas', 'Todas'],
            ['pendentes', 'Pendentes'],
            ['atrasadas', `Atrasadas${nAtrasadas ? ` (${nAtrasadas})` : ''}`],
          ] as [FiltroAtv, string][]
        ).map(([v, label]) => (
          <button
            key={v}
            type="button"
            onClick={() => setFiltro(v)}
            className={`px-3 py-1.5 font-medium transition-colors ${
              filtro === v
                ? 'bg-brand text-white'
                : 'bg-surface text-ink-soft hover:text-ink'
            }`}
          >
            {label}
          </button>
        ))}
      </div>
      <div className="flex items-center gap-2 ml-auto">
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
          + Nova atividade
        </button>
      </div>
    </div>
  );

  const modais = (
    <>
      {ver && (
        <RecordModal
          tipo="atividade"
          id={ver.id}
          onClose={() => setVer(null)}
          onChanged={recarregar}
          onEditar={() => {
            const a = ver;
            setVer(null);
            setEditar(a);
          }}
        />
      )}
      {(novo || editar) && (
        <AtividadeForm
          atividade={editar}
          onClose={() => {
            setNovo(false);
            setEditar(null);
          }}
          onSaved={recarregar}
        />
      )}
      {excluir && (
        <ConfirmarExclusao
          titulo="Excluir atividade"
          alvo={excluir.titulo}
          carregando={excluindo}
          onConfirmar={confirmarExclusao}
          onCancelar={() => setExcluir(null)}
        />
      )}
    </>
  );

  if (loading) return <div className="card p-8 animate-pulse h-48" />;
  if (itens.length === 0) {
    return (
      <div>
        {cabecalho}
        <div className="card p-8 text-center text-ink-soft">
          {filtro === 'todas'
            ? 'Nenhuma atividade registrada ainda.'
            : 'Nenhuma atividade nesse filtro.'}
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
          itens={itens}
          ordem={opcoes?.atividade_status ?? []}
          statusDe={(a) => a.status}
          cores={cores?.atividade_status}
          semLabel="(sem status)"
          onMover={(a, status) =>
            api.crmRecordPatch('atividade', a.id, { status }).then(recarregar)
          }
          onAbrir={(a) => setVer(a)}
          renderCard={(a) => (
            <>
              <div className="font-medium text-[13.5px] text-ink leading-snug mb-1">
                {a.titulo}
              </div>
              <div className="text-[12px] text-ink-soft">
                {a.tipo ? `${a.tipo} · ` : ''}
                {fmtData(a.data)}
              </div>
              {a.negocio_nome && (
                <div className="text-[12px] text-ink-mute truncate mt-1">
                  {a.negocio_nome}
                </div>
              )}
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
              <th className="font-medium px-4 py-2.5">Atividade</th>
              <th className="font-medium px-4 py-2.5">Tipo</th>
              <th className="font-medium px-4 py-2.5">Status</th>
              <th className="font-medium px-4 py-2.5">Quando</th>
              <th className="font-medium px-4 py-2.5">Negócio</th>
              <th className="font-medium px-4 py-2.5">Próximos passos</th>
              <th className="font-medium px-4 py-2.5 text-right">Ações</th>
            </tr>
          </thead>
          <tbody>
            {itens.map((a) => (
              <tr
                key={a.id}
                onClick={() => setVer(a)}
                className={`border-b border-line/60 last:border-0 hover:bg-bg-alt cursor-pointer ${
                  atrasada(a) ? 'bg-red-50/60' : ''
                }`}
              >
                <td className="px-4 py-2.5 font-medium text-ink">
                  {atrasada(a) && (
                    <span className="text-red-500 mr-1.5" title="atrasada">
                      ●
                    </span>
                  )}
                  {a.titulo}
                </td>
                <td className="px-4 py-2.5 text-ink-soft whitespace-nowrap">
                  <InlineCell
                    tipo="atividade"
                    id={a.id}
                    campo="tipo"
                    valor={a.tipo}
                    kind="select"
                    opcoes={opcoes?.atividade_tipo}
                    coresPorValor={cores?.atividade_tipo}
                    onSaved={recarregar}
                  />
                </td>
                <td className="px-4 py-2.5">
                  <InlineCell
                    tipo="atividade"
                    id={a.id}
                    campo="status"
                    valor={a.status}
                    kind="select"
                    opcoes={opcoes?.atividade_status}
                    coresPorValor={cores?.atividade_status}
                    onSaved={recarregar}
                  />
                </td>
                <td className="px-4 py-2.5 text-ink-soft whitespace-nowrap">
                  {fmtData(a.data)}
                </td>
                <td className="px-4 py-2.5 text-ink-soft">{a.negocio_nome ?? '—'}</td>
                <td className="px-4 py-2.5 text-ink-mute max-w-[280px]">
                  <InlineCell
                    tipo="atividade"
                    id={a.id}
                    campo="proximos_passos"
                    valor={a.proximos_passos}
                    onSaved={recarregar}
                  />
                </td>
                <td className="px-4 py-2.5 text-right whitespace-nowrap">
                  <button
                    type="button"
                    className="text-ink-mute hover:text-red-600 text-[12px]"
                    onClick={(ev) => {
                      ev.stopPropagation();
                      setExcluir(a);
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

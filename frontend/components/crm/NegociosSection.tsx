import { useState } from 'react';

import { ConfirmarExclusao, VistaToggle } from '@/components/crm/_crmShared';
import { InlineCell } from '@/components/crm/InlineCell';
import { NegocioForm } from '@/components/crm/NegocioForm';
import { RecordModal } from '@/components/crm/RecordModal';
import { StatCard } from '@/components/shared/StatCard';
import { useFetch } from '@/hooks/useFetch';
import { api } from '@/lib/api';
import type { CrmFacetas, NegocioListItem, NegociosPipeline } from '@/lib/types';

function brl(v?: number | null): string {
  if (v == null) return '—';
  return v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}

export function NegociosSection() {
  const [versao, setVersao] = useState(0);
  const [novo, setNovo] = useState(false);
  const [editar, setEditar] = useState<NegocioListItem | null>(null);
  const [excluir, setExcluir] = useState<NegocioListItem | null>(null);
  const [excluindo, setExcluindo] = useState(false);
  const [ver, setVer] = useState<NegocioListItem | null>(null);
  const [arrastando, setArrastando] = useState<string | null>(null);
  const [hoverCol, setHoverCol] = useState<string | null>(null);
  const [vista, setVista] = useState<'kanban' | 'lista'>('kanban');

  const { data, loading } = useFetch<NegociosPipeline>(
    () => api.crmNegociosPipeline(),
    [versao],
  );
  const { data: opcoes } = useFetch(() => api.crmOpcoes(), []);
  const { data: cores } = useFetch(() => api.crmOpcoesCores(), []);

  function recarregar() {
    setVersao((v) => v + 1);
  }

  async function soltarEm(estagio: string) {
    const id = arrastando;
    setArrastando(null);
    setHoverCol(null);
    if (!id) return;
    const atual = data?.colunas
      .flatMap((c) => c.negocios)
      .find((n) => n.id === id);
    if (!atual || atual.estagio === estagio) return;
    try {
      await api.crmNegocioMoverEstagio(id, estagio);
      recarregar();
    } catch {
      /* silencioso: recarrega no próximo ciclo */
    }
  }

  async function confirmarExclusao() {
    if (!excluir) return;
    setExcluindo(true);
    try {
      await api.crmNegocioExcluir(excluir.id);
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
          { id: 'kanban', label: 'Kanban' },
          { id: 'lista', label: 'Lista' },
        ]}
        onChange={setVista}
      />
      <button
        type="button"
        className="btn-primary !px-4 !py-2 !text-[13px]"
        onClick={() => setNovo(true)}
      >
        + Novo negócio
      </button>
    </div>
  );

  const modais = (
    <>
      {ver && (
        <RecordModal
          tipo="negocio"
          id={ver.id}
          onClose={() => setVer(null)}
          onChanged={recarregar}
          onEditar={() => {
            const n = ver;
            setVer(null);
            setEditar(n);
          }}
        />
      )}
      {(novo || editar) && (
        <NegocioForm
          negocio={editar}
          onClose={() => {
            setNovo(false);
            setEditar(null);
          }}
          onSaved={recarregar}
        />
      )}
      {excluir && (
        <ConfirmarExclusao
          titulo="Excluir negócio"
          alvo={excluir.nome}
          carregando={excluindo}
          onConfirmar={confirmarExclusao}
          onCancelar={() => setExcluir(null)}
        />
      )}
    </>
  );

  if (loading) return <div className="card p-8 animate-pulse h-48" />;
  if (!data || data.colunas.length === 0) {
    return (
      <div>
        {cabecalho}
        <div className="card p-8 text-center text-ink-soft">
          Nenhum negócio no pipeline ainda.
        </div>
        {modais}
      </div>
    );
  }

  return (
    <div>
      {cabecalho}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-5">
        <StatCard label="Valor no pipeline" value={brl(data.valor_total)} />
        <StatCard
          label="Forecast ponderado"
          value={brl(data.valor_ponderado)}
          trend="valor × probabilidade"
        />
        <StatCard
          label="Negócios"
          value={data.colunas.reduce((s, c) => s + c.total, 0)}
        />
      </div>

      {vista === 'lista' ? (
        <ListaNegocios
          negocios={data.colunas.flatMap((c) => c.negocios)}
          opcoes={opcoes ?? undefined}
          cores={cores ?? undefined}
          onAbrir={(n) => setVer(n)}
          onExcluir={(n) => setExcluir(n)}
          onSaved={recarregar}
        />
      ) : (
      <div className="flex gap-4 overflow-x-auto pb-4">
        {data.colunas.map((col) => (
          <section
            key={col.estagio}
            onDragOver={(e) => {
              e.preventDefault();
              setHoverCol(col.estagio);
            }}
            onDragLeave={() => setHoverCol((c) => (c === col.estagio ? null : c))}
            onDrop={() => soltarEm(col.estagio)}
            className={`min-w-[290px] w-[290px] shrink-0 rounded-lg transition-colors ${
              hoverCol === col.estagio ? 'bg-brand-soft/40' : ''
            }`}
          >
            <div className="flex items-center justify-between mb-1 px-1">
              <h3 className="font-display font-semibold text-[14px] text-ink m-0">
                {col.estagio}
              </h3>
              <span className="text-[12px] text-ink-mute font-mono">
                {col.total}
              </span>
            </div>
            <div className="text-[12px] text-ink-mute mb-3 px-1">
              {brl(col.valor_total)} · pond. {brl(col.valor_ponderado)}
            </div>
            <div className="flex flex-col gap-2.5">
              {col.negocios.map((n) => (
                <div
                  key={n.id}
                  draggable
                  onDragStart={() => setArrastando(n.id)}
                  onDragEnd={() => setArrastando(null)}
                  onClick={() => setVer(n)}
                  className={`card p-3.5 cursor-pointer hover:border-brand/40 ${
                    arrastando === n.id ? 'opacity-40' : ''
                  }`}
                >
                  <div className="flex items-start justify-between gap-2 mb-1.5">
                    <div className="font-medium text-[13.5px] text-ink leading-snug">
                      {n.nome}
                    </div>
                    <button
                      type="button"
                      className="text-ink-faint hover:text-red-600 text-[11px] shrink-0"
                      onClick={(ev) => {
                        ev.stopPropagation();
                        setExcluir(n);
                      }}
                    >
                      ✕
                    </button>
                  </div>
                  <div className="flex items-center justify-between text-[12.5px] mb-1">
                    <span className="font-semibold text-ink">
                      <InlineCell
                        tipo="negocio"
                        id={n.id}
                        campo="valor_estimado"
                        valor={n.valor_estimado}
                        display={brl(n.valor_estimado)}
                        kind="num"
                        onSaved={recarregar}
                      />
                    </span>
                    <InlineCell
                      tipo="negocio"
                      id={n.id}
                      campo="probabilidade"
                      valor={n.probabilidade}
                      kind="select"
                      opcoes={opcoes?.probabilidade}
                      className="text-ink-mute"
                      onSaved={recarregar}
                    />
                  </div>
                  {n.empresa_nome && (
                    <div className="text-[12px] text-ink-soft truncate">
                      {n.empresa_nome}
                    </div>
                  )}
                  {n.tipo_servico.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {n.tipo_servico.map((t) => (
                        <span
                          key={t}
                          className="text-[10.5px] bg-bg-alt text-ink-soft px-1.5 py-0.5 rounded-sm"
                        >
                          {t}
                        </span>
                      ))}
                    </div>
                  )}
                  {n.proxima_acao && (
                    <div className="text-[11.5px] text-ink-mute mt-2">
                      próxima ação: {n.proxima_acao}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </section>
        ))}
      </div>
      )}
    </div>
  );
}

function ListaNegocios({
  negocios,
  opcoes,
  cores,
  onAbrir,
  onExcluir,
  onSaved,
}: {
  negocios: NegocioListItem[];
  opcoes?: CrmFacetas;
  cores?: Record<string, Record<string, string>>;
  onAbrir: (n: NegocioListItem) => void;
  onExcluir: (n: NegocioListItem) => void;
  onSaved: () => void;
}) {
  return (
    <div className="card overflow-x-auto p-0">
      <table className="w-full border-collapse text-[13px]">
        <thead>
          <tr className="border-b border-line text-left text-ink-mute">
            <th className="font-medium px-4 py-2.5">Negócio</th>
            <th className="font-medium px-4 py-2.5">Estágio</th>
            <th className="font-medium px-4 py-2.5">Empresa</th>
            <th className="font-medium px-4 py-2.5 text-right">Valor</th>
            <th className="font-medium px-4 py-2.5">Probab.</th>
            <th className="font-medium px-4 py-2.5 text-right">Ações</th>
          </tr>
        </thead>
        <tbody>
          {negocios.map((n) => (
            <tr
              key={n.id}
              onClick={() => onAbrir(n)}
              className="border-b border-line/60 last:border-0 hover:bg-bg-alt cursor-pointer"
            >
              <td className="px-4 py-2.5 font-medium text-ink">{n.nome}</td>
              <td className="px-4 py-2.5">
                <InlineCell
                  tipo="negocio"
                  id={n.id}
                  campo="estagio"
                  valor={n.estagio}
                  kind="select"
                  opcoes={opcoes?.estagio}
                  coresPorValor={cores?.estagio}
                  onSaved={onSaved}
                />
              </td>
              <td className="px-4 py-2.5 text-ink-soft">{n.empresa_nome ?? '—'}</td>
              <td className="px-4 py-2.5 text-right text-ink-soft">
                <InlineCell
                  tipo="negocio"
                  id={n.id}
                  campo="valor_estimado"
                  valor={n.valor_estimado}
                  display={
                    n.valor_estimado == null
                      ? '—'
                      : n.valor_estimado.toLocaleString('pt-BR', {
                          style: 'currency',
                          currency: 'BRL',
                        })
                  }
                  kind="num"
                  onSaved={onSaved}
                />
              </td>
              <td className="px-4 py-2.5">
                <InlineCell
                  tipo="negocio"
                  id={n.id}
                  campo="probabilidade"
                  valor={n.probabilidade}
                  kind="select"
                  opcoes={opcoes?.probabilidade}
                  coresPorValor={cores?.probabilidade}
                  onSaved={onSaved}
                />
              </td>
              <td className="px-4 py-2.5 text-right whitespace-nowrap">
                <button
                  type="button"
                  className="text-ink-mute hover:text-red-600 text-[12px]"
                  onClick={(ev) => {
                    ev.stopPropagation();
                    onExcluir(n);
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
  );
}

import { useMemo, useState } from 'react';

import {
  Bloco,
  ConfirmarExclusao,
  Info,
  LinkExt,
} from '@/components/crm/_crmShared';
import { EmpresaForm } from '@/components/crm/EmpresaForm';
import { InlineCell } from '@/components/crm/InlineCell';
import { RecordModal } from '@/components/crm/RecordModal';
import { SidePanel } from '@/components/shared/SidePanel';
import { useFetch } from '@/hooks/useFetch';
import { api } from '@/lib/api';
import type {
  CrmFacetas,
  EmpresaDetalhe,
  EmpresaListItem,
  EmpresasFiltro,
  KanbanResponse,
  RecordTipo,
} from '@/lib/types';

type Ref = { tipo: RecordTipo; id: string };

export function EmpresasSection({ onChanged }: { onChanged: () => void }) {
  const [filtros, setFiltros] = useState<EmpresasFiltro>({});
  const [vista, setVista] = useState<'tabela' | 'kanban'>('tabela');
  const [versao, setVersao] = useState(0);
  const [detId, setDetId] = useState<string | null>(null);
  const [ver, setVer] = useState<Ref | null>(null);
  const [editar, setEditar] = useState<EmpresaDetalhe | null | undefined>(undefined);
  const [novo, setNovo] = useState(false);
  const [excluir, setExcluir] = useState<EmpresaListItem | null>(null);
  const [excluindo, setExcluindo] = useState(false);

  const { data: facetas } = useFetch<CrmFacetas>(() => api.crmFacetas(), []);
  const { data: opcoes } = useFetch<CrmFacetas>(() => api.crmOpcoes(), []);
  const { data: cores } = useFetch(() => api.crmOpcoesCores(), []);
  const filtroKey = JSON.stringify(filtros);
  const { data: lista, loading } = useFetch(
    () => api.crmEmpresas({ ...filtros, limit: 500 }),
    [filtroKey, versao],
  );
  const { data: kanban } = useFetch<KanbanResponse>(
    () => api.crmKanban(),
    [versao],
  );

  const empresas = lista?.items ?? [];

  function setF<K extends keyof EmpresasFiltro>(k: K, v: EmpresasFiltro[K]) {
    setFiltros((f) => ({ ...f, [k]: v || undefined }));
  }

  function recarregar() {
    setVersao((v) => v + 1);
    onChanged();
  }

  async function confirmarExclusao() {
    if (!excluir) return;
    setExcluindo(true);
    try {
      await api.crmEmpresaExcluir(excluir.id);
      setExcluir(null);
      recarregar();
    } finally {
      setExcluindo(false);
    }
  }

  const colunasKanban = useMemo(() => {
    if (!kanban) return [];
    const termo = (filtros.busca ?? '').trim().toLowerCase();
    if (!termo) return kanban.colunas;
    return kanban.colunas
      .map((c) => ({
        ...c,
        empresas: c.empresas.filter((e) =>
          e.nome.toLowerCase().includes(termo),
        ),
      }))
      .map((c) => ({ ...c, total: c.empresas.length }));
  }, [kanban, filtros.busca]);

  return (
    <div>
      {/* Barra de filtros */}
      <div className="flex flex-wrap items-end gap-2 mb-4">
        <input
          className="input max-w-[220px]"
          placeholder="Buscar…"
          value={filtros.busca ?? ''}
          onChange={(e) => setF('busca', e.target.value)}
        />
        <FiltroSelect
          label="Status"
          valor={filtros.status}
          opcoes={facetas?.status}
          onChange={(v) => setF('status', v)}
        />
        <FiltroSelect
          label="Setor"
          valor={filtros.setor}
          opcoes={facetas?.setor}
          onChange={(v) => setF('setor', v)}
        />
        <FiltroSelect
          label="Estado"
          valor={filtros.estado}
          opcoes={facetas?.estado}
          onChange={(v) => setF('estado', v)}
        />
        <FiltroSelect
          label="Tamanho"
          valor={filtros.tamanho}
          opcoes={facetas?.tamanho}
          onChange={(v) => setF('tamanho', v)}
        />
        {(filtros.status ||
          filtros.setor ||
          filtros.estado ||
          filtros.tamanho ||
          filtros.busca) && (
          <button
            type="button"
            className="text-[13px] text-ink-mute hover:text-ink underline px-1 py-2"
            onClick={() => setFiltros({})}
          >
            limpar
          </button>
        )}

        <div className="ml-auto flex items-center gap-2">
          <div className="inline-flex rounded-md border border-line overflow-hidden text-[13px]">
            {(['tabela', 'kanban'] as const).map((v) => (
              <button
                key={v}
                type="button"
                onClick={() => setVista(v)}
                className={`px-3 py-1.5 font-medium transition-colors ${
                  vista === v
                    ? 'bg-brand text-white'
                    : 'bg-surface text-ink-soft hover:text-ink'
                }`}
              >
                {v === 'tabela' ? 'Tabela' : 'Kanban'}
              </button>
            ))}
          </div>
          <button
            type="button"
            className="btn-primary !px-4 !py-2 !text-[13px]"
            onClick={() => setNovo(true)}
          >
            + Nova empresa
          </button>
        </div>
      </div>

      {loading ? (
        <div className="card p-8 animate-pulse h-48" />
      ) : empresas.length === 0 ? (
        <div className="card p-8 text-center text-ink-soft">
          Nenhuma empresa bate com os filtros.
        </div>
      ) : vista === 'tabela' ? (
        <Tabela
          empresas={empresas}
          opcoes={opcoes ?? undefined}
          cores={cores ?? undefined}
          onAbrir={setDetId}
          onExcluir={setExcluir}
          onSaved={recarregar}
        />
      ) : (
        <div className="flex gap-4 overflow-x-auto pb-4">
          {colunasKanban.map((col) => (
            <section key={col.status} className="min-w-[280px] w-[280px] shrink-0">
              <div className="flex items-center justify-between mb-3 px-1">
                <h3 className="font-display font-semibold text-[14px] text-ink m-0">
                  {col.status}
                </h3>
                <span className="text-[12px] text-ink-mute font-mono">
                  {col.total}
                </span>
              </div>
              <div className="flex flex-col gap-2.5">
                {col.empresas.map((e) => (
                  <button
                    key={e.id}
                    type="button"
                    onClick={() => setDetId(e.id)}
                    className="card p-3 text-left hover:border-brand/40 w-full"
                  >
                    <div className="font-medium text-[13.5px] text-ink mb-1 line-clamp-2">
                      {e.nome}
                    </div>
                    <div className="text-[12px] text-ink-soft">
                      {e.setor} · {e.n_contatos} contato(s)
                    </div>
                  </button>
                ))}
              </div>
            </section>
          ))}
        </div>
      )}

      <p className="text-[12px] text-ink-mute mt-3">
        {empresas.length} empresa(s){lista ? ` · ${lista.total} no total` : ''}
      </p>

      {detId && (
        <DetalheModal
          id={detId}
          onAbrir={setVer}
          onClose={() => setDetId(null)}
          onEditar={(e) => {
            setDetId(null);
            setEditar(e);
          }}
        />
      )}
      {ver && (
        <RecordModal
          tipo={ver.tipo}
          id={ver.id}
          onClose={() => setVer(null)}
          onChanged={recarregar}
        />
      )}
      {(novo || editar !== undefined) && (
        <EmpresaForm
          empresa={editar ?? undefined}
          onClose={() => {
            setNovo(false);
            setEditar(undefined);
          }}
          onSaved={recarregar}
        />
      )}
      {excluir && (
        <ConfirmarExclusao
          titulo="Excluir empresa"
          alvo={excluir.nome}
          carregando={excluindo}
          onConfirmar={confirmarExclusao}
          onCancelar={() => setExcluir(null)}
        />
      )}
    </div>
  );
}

function FiltroSelect({
  label,
  valor,
  opcoes,
  onChange,
}: {
  label: string;
  valor?: string;
  opcoes?: string[];
  onChange: (v: string) => void;
}) {
  return (
    <select
      className="input max-w-[160px]"
      value={valor ?? ''}
      onChange={(e) => onChange(e.target.value)}
    >
      <option value="">{label}: todos</option>
      {(opcoes ?? []).map((o) => (
        <option key={o} value={o}>
          {o}
        </option>
      ))}
    </select>
  );
}

function Tabela({
  empresas,
  opcoes,
  cores,
  onAbrir,
  onExcluir,
  onSaved,
}: {
  empresas: EmpresaListItem[];
  opcoes?: CrmFacetas;
  cores?: Record<string, Record<string, string>>;
  onAbrir: (id: string) => void;
  onExcluir: (e: EmpresaListItem) => void;
  onSaved: () => void;
}) {
  return (
    <div className="card overflow-x-auto p-0">
      <table className="w-full border-collapse text-[13px]">
        <thead>
          <tr className="border-b border-line text-left text-ink-mute">
            <th className="font-medium px-4 py-2.5">Nome</th>
            <th className="font-medium px-4 py-2.5">Setor</th>
            <th className="font-medium px-4 py-2.5">Cidade</th>
            <th className="font-medium px-4 py-2.5">Tamanho</th>
            <th className="font-medium px-4 py-2.5">Status</th>
            <th className="font-medium px-4 py-2.5">Contatos</th>
            <th className="font-medium px-4 py-2.5 text-right">Ações</th>
          </tr>
        </thead>
        <tbody>
          {empresas.map((e) => (
            <tr
              key={e.id}
              onClick={() => onAbrir(e.id)}
              className="border-b border-line/60 last:border-0 hover:bg-bg-alt cursor-pointer"
            >
              <td className="px-4 py-2.5 font-medium text-ink">{e.nome}</td>
              <td className="px-4 py-2.5 text-ink-soft">
                <InlineCell
                  tipo="empresa"
                  id={e.id}
                  campo="setor"
                  valor={e.setor}
                  kind="select"
                  opcoes={opcoes?.setor}
                  coresPorValor={cores?.setor}
                  onSaved={onSaved}
                />
              </td>
              <td className="px-4 py-2.5 text-ink-soft">
                <InlineCell
                  tipo="empresa"
                  id={e.id}
                  campo="cidade"
                  valor={e.cidade}
                  onSaved={onSaved}
                />
                {e.estado ? (
                  <span className="text-ink-mute">/{e.estado}</span>
                ) : null}
              </td>
              <td className="px-4 py-2.5 text-ink-soft">
                <InlineCell
                  tipo="empresa"
                  id={e.id}
                  campo="tamanho"
                  valor={e.tamanho}
                  kind="select"
                  opcoes={opcoes?.tamanho}
                  coresPorValor={cores?.tamanho}
                  onSaved={onSaved}
                />
              </td>
              <td className="px-4 py-2.5">
                <InlineCell
                  tipo="empresa"
                  id={e.id}
                  campo="status"
                  valor={e.status}
                  kind="select"
                  opcoes={opcoes?.status}
                  coresPorValor={cores?.status}
                  onSaved={onSaved}
                />
              </td>
              <td className="px-4 py-2.5 text-ink-soft">{e.n_contatos}</td>
              <td className="px-4 py-2.5 text-right whitespace-nowrap">
                <button
                  type="button"
                  className="text-ink-mute hover:text-red-600 text-[12px]"
                  onClick={(ev) => {
                    ev.stopPropagation();
                    onExcluir(e);
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

function DetalheModal({
  id,
  onAbrir,
  onClose,
  onEditar,
}: {
  id: string;
  onAbrir: (r: Ref) => void;
  onClose: () => void;
  onEditar: (e: EmpresaDetalhe) => void;
}) {
  const { data: e, loading } = useFetch<EmpresaDetalhe>(
    () => api.crmEmpresa(id),
    [id],
  );
  const { data: rel } = useFetch(() => api.crmEmpresaRelacionados(id), [id]);
  const brl = (v?: number | null) =>
    v == null ? '—' : v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

  return (
    <SidePanel
      open
      onClose={onClose}
      title={e?.nome ?? 'Empresa'}
      acoes={
        e ? (
          <button
            type="button"
            className="btn-primary !px-3 !py-1.5 !text-[12px]"
            onClick={() => onEditar(e)}
          >
            Editar
          </button>
        ) : undefined
      }
    >
      {loading || !e ? (
        <div className="animate-pulse h-40" />
      ) : (
        <div className="flex flex-col gap-5">
          <div className="flex flex-wrap gap-x-5 gap-y-1.5 text-[13px] text-ink-soft">
            {e.cnpj && <Info rotulo="CNPJ" valor={e.cnpj} />}
            {e.status && <Info rotulo="Status" valor={e.status} />}
            {e.setor && <Info rotulo="Setor" valor={e.setor} />}
            {e.tamanho && <Info rotulo="Tamanho" valor={e.tamanho} />}
            {(e.cidade || e.estado) && (
              <Info
                rotulo="Local"
                valor={`${e.cidade ?? ''}${e.estado ? `/${e.estado}` : ''}`}
              />
            )}
            {e.como_conheceu && <Info rotulo="Origem" valor={e.como_conheceu} />}
          </div>

          {(e.site || e.instagram || e.facebook) && (
            <div className="flex flex-wrap gap-3 text-[13px]">
              {e.site && <LinkExt href={e.site} label="Site" />}
              {e.instagram && <LinkExt href={e.instagram} label="Instagram" />}
              {e.facebook && <LinkExt href={e.facebook} label="Facebook" />}
            </div>
          )}

          <Bloco titulo={`Contatos (${e.contatos.length})`}>
            {e.contatos.length === 0 ? (
              <p className="text-[13px] text-ink-mute m-0">Sem contatos.</p>
            ) : (
              <ul className="flex flex-col gap-1.5 m-0 p-0 list-none">
                {e.contatos.map((c) => (
                  <li key={c.id}>
                    <button
                      type="button"
                      onClick={() => onAbrir({ tipo: 'contato', id: c.id })}
                      className="flex flex-wrap items-baseline gap-x-2 text-[13px] text-left card px-3 py-2 w-full hover:border-brand/40 transition-colors"
                    >
                      <span className="font-medium text-ink">{c.nome}</span>
                      {c.cargo && <span className="text-ink-soft">{c.cargo}</span>}
                      {c.decisor && (
                        <span className="text-[10px] uppercase tracking-wide bg-brand-soft text-brand px-1.5 py-0.5 rounded-sm">
                          decisor
                        </span>
                      )}
                      {c.email && (
                        <span className="text-ink-mute font-mono text-[12px]">
                          {c.email}
                        </span>
                      )}
                      <span className="ml-auto text-ink-mute">›</span>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </Bloco>

          {e.socios.length > 0 && (
            <Bloco titulo={`Sócios (${e.socios.length})`}>
              <p className="text-[13px] text-ink-soft m-0">
                {e.socios.map((s) => s.nome).join(', ')}
              </p>
            </Bloco>
          )}

          {rel && rel.negocios.length > 0 && (
            <Bloco titulo={`Negócios (${rel.negocios.length})`}>
              <ul className="flex flex-col gap-1.5 m-0 p-0 list-none">
                {rel.negocios.map((n) => (
                  <li key={n.id}>
                    <button
                      type="button"
                      onClick={() => onAbrir({ tipo: 'negocio', id: n.id })}
                      className="flex justify-between gap-2 text-[13px] text-left card px-3 py-2 w-full hover:border-brand/40 transition-colors"
                    >
                      <span className="text-ink">
                        {n.nome}
                        {n.estagio && (
                          <span className="text-ink-mute"> · {n.estagio}</span>
                        )}
                      </span>
                      <span className="text-ink-soft shrink-0">
                        {brl(n.valor_estimado)} ›
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            </Bloco>
          )}

          {rel && rel.projetos.length > 0 && (
            <Bloco titulo={`Projetos (${rel.projetos.length})`}>
              <ul className="flex flex-col gap-1.5 m-0 p-0 list-none">
                {rel.projetos.map((p) => (
                  <li key={p.id}>
                    <button
                      type="button"
                      onClick={() => onAbrir({ tipo: 'projeto', id: p.id })}
                      className="flex justify-between gap-2 text-[13px] text-left card px-3 py-2 w-full hover:border-brand/40 transition-colors"
                    >
                      <span className="text-ink">
                        {p.nome}
                        {p.status && (
                          <span className="text-ink-mute"> · {p.status}</span>
                        )}
                      </span>
                      <span className="text-ink-soft shrink-0">
                        a receber {brl(p.a_receber)} ›
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            </Bloco>
          )}

          {rel && rel.atividades.length > 0 && (
            <Bloco titulo={`Atividades (${rel.atividades.length})`}>
              <ul className="flex flex-col gap-1.5 m-0 p-0 list-none">
                {rel.atividades.map((a) => (
                  <li key={a.id}>
                    <button
                      type="button"
                      onClick={() => onAbrir({ tipo: 'atividade', id: a.id })}
                      className="flex justify-between gap-2 text-[13px] text-ink-soft text-left card px-3 py-2 w-full hover:border-brand/40 transition-colors"
                    >
                      <span>
                        <span className="text-ink">{a.titulo}</span>
                        {a.tipo && <span> · {a.tipo}</span>}
                        {a.status && <span> · {a.status}</span>}
                      </span>
                      <span className="text-ink-mute shrink-0">›</span>
                    </button>
                  </li>
                ))}
              </ul>
            </Bloco>
          )}

          {e.notas && (
            <Bloco titulo="Notas / Análise">
              <pre className="text-[12.5px] text-ink-soft whitespace-pre-wrap font-sans m-0 leading-relaxed">
                {e.notas}
              </pre>
            </Bloco>
          )}
        </div>
      )}
    </SidePanel>
  );
}

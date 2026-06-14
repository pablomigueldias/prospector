import { useState } from 'react';

import { StatCard } from './StatCard';
import { formatBRL } from '@/lib/format';
import {
  useFreelaActions,
  useFreelaClientes,
  useFreelaKanban,
  useFreelaMetricas,
  useFreelaPlataformas,
  useFreelaProjetos,
} from '@/hooks/useFreela';
import {
  FREELA_STATUS,
  type FreelaAnalise,
  type FreelaKanbanColuna,
  type FreelaPrecificarResponse,
  type FreelaProjetoListItem,
  type FreelaStatus,
} from '@/lib/types';

const STATUS_LABEL: Record<FreelaStatus, string> = {
  rascunho: 'Rascunho',
  enviada: 'Enviada',
  visualizada: 'Visualizada',
  respondida: 'Respondida',
  negociando: 'Negociando',
  fechada: 'Fechada',
  perdida: 'Perdida',
};

export default function FreelaScreen() {
  const kanban = useFreelaKanban();
  const metricas = useFreelaMetricas();
  const projetos = useFreelaProjetos();
  const plataformas = useFreelaPlataformas();
  const clientes = useFreelaClientes();
  const acoes = useFreelaActions();

  const [mostrarForm, setMostrarForm] = useState(false);

  function refetchTudo() {
    void kanban.refetch();
    void metricas.refetch();
    void projetos.refetch();
  }

  const m = metricas.data;

  return (
    <div className="max-w-[1200px] mx-auto pb-16">
      <header className="mb-7">
        <div className="eyebrow mb-3">Pessoal · Copiloto de propostas</div>
        <h1 className="font-display font-semibold text-[38px] leading-[1.05] tracking-tighter text-ink m-0 mb-2.5">
          Freela
        </h1>
        <p className="text-[15px] text-ink-soft max-w-[64ch] leading-relaxed m-0">
          Cola o projeto da Workana, descobre onde vale gastar proposta,
          precifica pra receber o que você quer e acompanha tudo num Kanban. A
          IA não toca na Workana — você revisa, envia na mão e marca o status.
        </p>
      </header>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-7">
        <StatCard
          label="Propostas"
          value={m?.total_propostas ?? 0}
          loading={metricas.loading}
        />
        <StatCard
          label="Taxa de resposta"
          value={m ? `${Math.round(m.taxa_resposta * 100)}%` : '—'}
          loading={metricas.loading}
        />
        <StatCard
          label="Taxa de fechamento"
          value={m ? `${Math.round(m.taxa_fechamento * 100)}%` : '—'}
          loading={metricas.loading}
        />
        <StatCard
          label="Líquido fechado"
          value={formatBRL(m?.liquido_total_fechado ?? 0)}
          loading={metricas.loading}
        />
      </div>

      <Precificador
        plataformaId={plataformas.items[0]?.id ?? null}
        clientes={clientes.items.map((c) => ({ id: c.id, nome: c.nome }))}
      />

      {/* Fila de oportunidades */}
      <div className="flex items-center justify-between mt-8 mb-4">
        <h2 className="font-display font-semibold text-lg tracking-tight text-ink m-0">
          Fila de oportunidades
        </h2>
        <button
          type="button"
          className="btn-primary"
          onClick={() => setMostrarForm((v) => !v)}
        >
          {mostrarForm ? 'Fechar' : '+ Colar projeto'}
        </button>
      </div>

      {mostrarForm && (
        <NovoProjetoForm
          loading={acoes.loading}
          erro={acoes.error?.message ?? null}
          clientes={clientes.items.map((c) => ({ id: c.id, nome: c.nome }))}
          onSubmit={async (body) => {
            const p = await acoes.criarProjeto(body);
            if (p) {
              setMostrarForm(false);
              projetos.refetch();
            }
          }}
        />
      )}

      <FilaProjetos
        items={projetos.items}
        loading={projetos.loading}
        onCriarProposta={async (projetoId, valorCotado, liquido, horas, prazo) => {
          const p = await acoes.criarProposta({
            projeto_id: projetoId,
            valor_cotado: valorCotado,
            valor_liquido_estimado: liquido,
            horas_estimadas: horas,
            prazo_proposto: prazo,
          });
          if (p) refetchTudo();
        }}
        onAnalisar={async (id) => {
          const r = await acoes.analisarProjeto(id);
          if (r) void projetos.refetch();
          return r?.analise ?? null;
        }}
        onRemover={async (id) => {
          if (confirm('Remover este projeto e suas propostas?')) {
            await acoes.removerProjeto(id);
            refetchTudo();
          }
        }}
      />

      {/* Kanban */}
      <h2 className="font-display font-semibold text-lg tracking-tight text-ink mt-10 mb-4">
        Kanban de propostas
      </h2>
      <Kanban
        colunas={kanban.colunas}
        loading={kanban.loading}
        onMover={async (id, status) => {
          let motivo: string | null = null;
          if (status === 'perdida') {
            motivo = window.prompt('Motivo da perda (opcional):') || null;
          }
          await acoes.mudarStatus(id, status, motivo);
          refetchTudo();
        }}
        onRemover={async (id) => {
          if (confirm('Remover esta proposta?')) {
            await acoes.removerProposta(id);
            refetchTudo();
          }
        }}
      />
    </div>
  );
}

// ── Precificador ──────────────────────────────────────────────────

function Precificador({
  plataformaId,
  clientes,
}: {
  plataformaId: string | null;
  clientes: { id: string; nome: string }[];
}) {
  const acoes = useFreelaActions();
  const [aberto, setAberto] = useState(false);
  const [liquido, setLiquido] = useState('1400');
  const [clienteId, setClienteId] = useState('');
  const [jaPagou, setJaPagou] = useState('0');
  const [horas, setHoras] = useState('');
  const [valorHora, setValorHora] = useState('');
  const [res, setRes] = useState<FreelaPrecificarResponse | null>(null);

  async function calcular() {
    const r = await acoes.precificar({
      liquido_desejado: Number(liquido) || 0,
      cliente_id: clienteId || null,
      ja_me_pagou_usd: clienteId ? null : Number(jaPagou) || 0,
      plataforma_id: plataformaId,
      horas_estimadas: horas ? Number(horas) : null,
      valor_hora_alvo: valorHora ? Number(valorHora) : null,
    });
    if (r) setRes(r);
  }

  return (
    <div className="card p-5">
      <button
        type="button"
        className="flex items-center justify-between w-full text-left"
        onClick={() => setAberto((v) => !v)}
      >
        <span className="font-display font-semibold text-[15px] text-ink">
          💰 Precificador — quanto cotar pra receber o que você quer
        </span>
        <span className="text-ink-mute text-sm">{aberto ? '▲' : '▼'}</span>
      </button>

      {aberto && (
        <div className="mt-4">
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            <label className="text-[13px] text-ink-soft">
              Quero receber (R$)
              <input
                className="input mt-1"
                type="number"
                value={liquido}
                onChange={(e) => setLiquido(e.target.value)}
              />
            </label>
            <label className="text-[13px] text-ink-soft">
              Cliente
              <select
                className="input mt-1"
                value={clienteId}
                onChange={(e) => setClienteId(e.target.value)}
              >
                <option value="">Novo (informo abaixo)</option>
                {clientes.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.nome}
                  </option>
                ))}
              </select>
            </label>
            {!clienteId && (
              <label className="text-[13px] text-ink-soft">
                Já me pagou (US$)
                <input
                  className="input mt-1"
                  type="number"
                  value={jaPagou}
                  onChange={(e) => setJaPagou(e.target.value)}
                />
              </label>
            )}
            <label className="text-[13px] text-ink-soft">
              Horas estimadas
              <input
                className="input mt-1"
                type="number"
                value={horas}
                onChange={(e) => setHoras(e.target.value)}
              />
            </label>
            <label className="text-[13px] text-ink-soft">
              Valor-hora alvo (R$)
              <input
                className="input mt-1"
                type="number"
                value={valorHora}
                onChange={(e) => setValorHora(e.target.value)}
              />
            </label>
            <div className="flex items-end">
              <button
                type="button"
                className="btn-primary w-full"
                onClick={calcular}
                disabled={acoes.loading}
              >
                {acoes.loading ? 'Calculando…' : 'Calcular'}
              </button>
            </div>
          </div>

          {res && (
            <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-3">
              <ResultBox titulo="Comissão" valor={`${Math.round(res.pct_comissao * 100)}%`} />
              <ResultBox titulo="Cotar (valor total)" valor={formatBRL(res.valor_a_cotar)} forte />
              <ResultBox titulo="Cliente paga" valor={formatBRL(res.cliente_paga)} />
              <ResultBox
                titulo="Líquido / hora"
                valor={res.liquido_por_hora != null ? formatBRL(res.liquido_por_hora) : '—'}
              />
              {res.alerta && (
                <div className="col-span-2 md:col-span-4 text-[13px] text-amber-700 bg-amber-50 border border-amber-200 rounded p-2.5">
                  ⚠️ {res.alerta}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function ResultBox({ titulo, valor, forte }: { titulo: string; valor: string; forte?: boolean }) {
  return (
    <div className={`rounded border p-3 ${forte ? 'bg-brand-soft/50 border-brand/30' : 'bg-bg-alt border-transparent'}`}>
      <div className="text-[11px] uppercase tracking-wide text-ink-mute">{titulo}</div>
      <div className={`mt-0.5 ${forte ? 'text-ink font-display font-semibold text-lg' : 'text-ink text-[15px]'}`}>
        {valor}
      </div>
    </div>
  );
}

// ── Fila de projetos ──────────────────────────────────────────────

function FilaProjetos({
  items,
  loading,
  onCriarProposta,
  onAnalisar,
  onRemover,
}: {
  items: FreelaProjetoListItem[];
  loading: boolean;
  onCriarProposta: (
    projetoId: string,
    valorCotado: number | null,
    liquido: number | null,
    horas: number | null,
    prazo: string | null,
  ) => void;
  onAnalisar: (id: string) => Promise<FreelaAnalise | null>;
  onRemover: (id: string) => void;
}) {
  if (loading) {
    return (
      <div className="flex flex-col gap-2">
        {[0, 1].map((i) => (
          <div key={i} className="card p-4 h-[80px] animate-pulse" />
        ))}
      </div>
    );
  }
  if (items.length === 0) {
    return (
      <div className="card p-6 text-center text-sm text-ink-mute">
        Nenhum projeto na fila. Clique em "Colar projeto".
      </div>
    );
  }
  return (
    <div className="flex flex-col gap-2">
      {items.map((p) => (
        <ProjetoCard
          key={p.id}
          p={p}
          onCriarProposta={onCriarProposta}
          onAnalisar={onAnalisar}
          onRemover={onRemover}
        />
      ))}
    </div>
  );
}

const RECOMENDACAO_COR: Record<string, string> = {
  vale: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  talvez: 'bg-amber-50 text-amber-700 border-amber-200',
  evite: 'bg-red-50 text-red-700 border-red-200',
};

function ProjetoCard({
  p,
  onCriarProposta,
  onAnalisar,
  onRemover,
}: {
  p: FreelaProjetoListItem;
  onCriarProposta: (
    projetoId: string,
    valorCotado: number | null,
    liquido: number | null,
    horas: number | null,
    prazo: string | null,
  ) => void;
  onAnalisar: (id: string) => Promise<FreelaAnalise | null>;
  onRemover: (id: string) => void;
}) {
  const [abrir, setAbrir] = useState(false);
  const [valor, setValor] = useState('');
  const [liquido, setLiquido] = useState('');
  const [horas, setHoras] = useState('');
  const [prazo, setPrazo] = useState('');
  const [analise, setAnalise] = useState<FreelaAnalise | null>(null);
  const [analisando, setAnalisando] = useState(false);

  const orcamento =
    p.faixa_orcamento_min != null || p.faixa_orcamento_max != null
      ? `${formatBRL(p.faixa_orcamento_min ?? 0)} – ${formatBRL(p.faixa_orcamento_max ?? 0)}`
      : null;

  async function analisar() {
    setAnalisando(true);
    const a = await onAnalisar(p.id);
    if (a) setAnalise(a);
    setAnalisando(false);
  }

  return (
    <div className="card p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="font-medium text-ink text-[15px] truncate">{p.titulo}</div>
          <div className="mt-1 flex flex-wrap items-center gap-2 text-[12px] text-ink-mute">
            {p.cliente_nome && <span>{p.cliente_nome}</span>}
            {orcamento && <span>· {orcamento}</span>}
            {p.n_propostas_concorrentes != null && (
              <span>· {p.n_propostas_concorrentes} propostas</span>
            )}
            <span>· {p.qtd_propostas} sua(s)</span>
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {p.tem_analise && p.fit_score != null ? (
            <span className="text-[12px] font-medium px-2 py-0.5 rounded bg-brand-soft text-brand-ink">
              fit {p.fit_score}
            </span>
          ) : null}
          <button
            type="button"
            className="btn-ghost text-[13px]"
            onClick={analisar}
            disabled={analisando}
          >
            {analisando ? 'Analisando…' : p.tem_analise ? 'Reanalisar' : '🔎 Analisar'}
          </button>
          <button
            type="button"
            className="btn-ghost text-[13px]"
            onClick={() => setAbrir((v) => !v)}
          >
            {abrir ? 'Fechar' : '+ Proposta'}
          </button>
          <button
            type="button"
            className="text-ink-faint hover:text-red-500 text-sm"
            title="Remover projeto"
            onClick={() => onRemover(p.id)}
          >
            ✕
          </button>
        </div>
      </div>

      {analise && (
        <div className="mt-3 border-t border-line pt-3 text-[13px]">
          <div className="flex items-center gap-2 mb-1.5">
            {analise.recomendacao && (
              <span
                className={`text-[12px] font-medium px-2 py-0.5 rounded border ${
                  RECOMENDACAO_COR[analise.recomendacao] ?? 'bg-bg-alt text-ink-soft border-line'
                }`}
              >
                {analise.recomendacao} · fit {analise.fit_score}
              </span>
            )}
          </div>
          {analise.veredito && <p className="text-ink-soft m-0 mb-2">{analise.veredito}</p>}
          {analise.red_flags.length > 0 && (
            <div className="mb-1.5">
              <span className="text-[12px] font-medium text-red-600">Red flags:</span>
              <ul className="list-disc ml-5 text-ink-soft">
                {analise.red_flags.map((r, i) => (
                  <li key={i}>{r}</li>
                ))}
              </ul>
            </div>
          )}
          {analise.ganchos.length > 0 && (
            <div>
              <span className="text-[12px] font-medium text-emerald-700">Ganchos (seu perfil):</span>
              <ul className="list-disc ml-5 text-ink-soft">
                {analise.ganchos.map((g, i) => (
                  <li key={i}>{g}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {abrir && (
        <div className="mt-3 grid grid-cols-2 md:grid-cols-5 gap-2 items-end border-t border-line pt-3">
          <label className="text-[12px] text-ink-soft">
            Cotar (R$)
            <input className="input mt-1" type="number" value={valor} onChange={(e) => setValor(e.target.value)} />
          </label>
          <label className="text-[12px] text-ink-soft">
            Líquido (R$)
            <input className="input mt-1" type="number" value={liquido} onChange={(e) => setLiquido(e.target.value)} />
          </label>
          <label className="text-[12px] text-ink-soft">
            Horas
            <input className="input mt-1" type="number" value={horas} onChange={(e) => setHoras(e.target.value)} />
          </label>
          <label className="text-[12px] text-ink-soft">
            Prazo
            <input className="input mt-1" value={prazo} onChange={(e) => setPrazo(e.target.value)} placeholder="ex: 7 dias" />
          </label>
          <button
            type="button"
            className="btn-primary"
            onClick={() => {
              onCriarProposta(
                p.id,
                valor ? Number(valor) : null,
                liquido ? Number(liquido) : null,
                horas ? Number(horas) : null,
                prazo || null,
              );
              setAbrir(false);
              setValor('');
              setLiquido('');
              setHoras('');
              setPrazo('');
            }}
          >
            Criar
          </button>
        </div>
      )}
    </div>
  );
}

// ── Kanban ────────────────────────────────────────────────────────

function Kanban({
  colunas,
  loading,
  onMover,
  onRemover,
}: {
  colunas: FreelaKanbanColuna[];
  loading: boolean;
  onMover: (id: string, status: FreelaStatus) => void;
  onRemover: (id: string) => void;
}) {
  if (loading) {
    return <div className="card p-6 text-sm text-ink-mute">Carregando board…</div>;
  }
  const total = colunas.reduce((acc, c) => acc + c.items.length, 0);
  if (total === 0) {
    return (
      <div className="card p-6 text-center text-sm text-ink-mute">
        Nenhuma proposta ainda. Crie uma a partir de um projeto na fila.
      </div>
    );
  }
  return (
    <div className="flex gap-3 overflow-x-auto pb-2">
      {colunas.map((col) => (
        <div key={col.status} className="min-w-[230px] w-[230px] shrink-0">
          <div className="flex items-center justify-between mb-2 px-1">
            <span className="text-[13px] font-medium text-ink-soft">
              {STATUS_LABEL[col.status]}
            </span>
            <span className="text-[12px] text-ink-faint">{col.items.length}</span>
          </div>
          <div className="flex flex-col gap-2">
            {col.items.map((it) => (
              <div key={it.id} className="card p-3">
                <div className="text-[13px] font-medium text-ink truncate" title={it.projeto_titulo}>
                  {it.projeto_titulo}
                </div>
                {it.cliente_nome && (
                  <div className="text-[11px] text-ink-mute truncate">{it.cliente_nome}</div>
                )}
                <div className="mt-1.5 flex items-center justify-between text-[12px]">
                  <span className="text-ink-soft">
                    {it.valor_cotado != null ? formatBRL(it.valor_cotado) : '—'}
                  </span>
                  {it.dias_desde_envio != null && (
                    <span className="text-ink-faint">{it.dias_desde_envio}d</span>
                  )}
                </div>
                <div className="mt-2 flex items-center gap-1.5">
                  <select
                    className="input text-[12px] py-1 flex-1"
                    value={it.status}
                    onChange={(e) => onMover(it.id, e.target.value as FreelaStatus)}
                  >
                    {FREELA_STATUS.map((s) => (
                      <option key={s} value={s}>
                        {STATUS_LABEL[s]}
                      </option>
                    ))}
                  </select>
                  <button
                    type="button"
                    className="text-ink-faint hover:text-red-500 text-sm px-1"
                    title="Remover"
                    onClick={() => onRemover(it.id)}
                  >
                    ✕
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

// ── Form de novo projeto ──────────────────────────────────────────

function NovoProjetoForm({
  loading,
  erro,
  clientes,
  onSubmit,
}: {
  loading: boolean;
  erro: string | null;
  clientes: { id: string; nome: string }[];
  onSubmit: (body: {
    titulo: string;
    descricao: string;
    cliente_id?: string | null;
    faixa_orcamento_min?: number | null;
    faixa_orcamento_max?: number | null;
    n_propostas_concorrentes?: number | null;
  }) => void;
}) {
  const [titulo, setTitulo] = useState('');
  const [descricao, setDescricao] = useState('');
  const [clienteId, setClienteId] = useState('');
  const [min, setMin] = useState('');
  const [max, setMax] = useState('');
  const [nProp, setNProp] = useState('');

  return (
    <div className="card p-5 mb-4">
      <div className="grid gap-3">
        <label className="text-[13px] text-ink-soft">
          Título do projeto
          <input className="input mt-1" value={titulo} onChange={(e) => setTitulo(e.target.value)} />
        </label>
        <label className="text-[13px] text-ink-soft">
          Descrição (cole o texto do projeto)
          <textarea
            className="input mt-1 min-h-[120px]"
            value={descricao}
            onChange={(e) => setDescricao(e.target.value)}
          />
        </label>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <label className="text-[13px] text-ink-soft">
            Cliente
            <select className="input mt-1" value={clienteId} onChange={(e) => setClienteId(e.target.value)}>
              <option value="">—</option>
              {clientes.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.nome}
                </option>
              ))}
            </select>
          </label>
          <label className="text-[13px] text-ink-soft">
            Orçamento mín
            <input className="input mt-1" type="number" value={min} onChange={(e) => setMin(e.target.value)} />
          </label>
          <label className="text-[13px] text-ink-soft">
            Orçamento máx
            <input className="input mt-1" type="number" value={max} onChange={(e) => setMax(e.target.value)} />
          </label>
          <label className="text-[13px] text-ink-soft">
            Nº propostas
            <input className="input mt-1" type="number" value={nProp} onChange={(e) => setNProp(e.target.value)} />
          </label>
        </div>
        {erro && <div className="text-[13px] text-red-600">{erro}</div>}
        <div>
          <button
            type="button"
            className="btn-primary"
            disabled={loading || !titulo.trim() || !descricao.trim()}
            onClick={() =>
              onSubmit({
                titulo: titulo.trim(),
                descricao: descricao.trim(),
                cliente_id: clienteId || null,
                faixa_orcamento_min: min ? Number(min) : null,
                faixa_orcamento_max: max ? Number(max) : null,
                n_propostas_concorrentes: nProp ? Number(nProp) : null,
              })
            }
          >
            {loading ? 'Salvando…' : 'Salvar projeto'}
          </button>
        </div>
      </div>
    </div>
  );
}

import { useEffect, useState } from 'react';

import { StatCard } from './StatCard';
import { formatBRL } from '@/lib/format';
import {
  useFreelaActions,
  useFreelaClientes,
  useFreelaKanban,
  useFreelaMetricas,
  useFreelaPlataformas,
  useFreelaProjetos,
  useFreelaProposta,
} from '@/hooks/useFreela';
import {
  FREELA_STATUS,
  type FreelaAnalise,
  type FreelaChecklist,
  type FreelaExtrairProjeto,
  type FreelaKanbanColuna,
  type FreelaKanbanItem,
  type FreelaMetricas,
  type FreelaPrecificarResponse,
  type FreelaProjetoListItem,
  type FreelaStatus,
} from '@/lib/types';

/** Horas médias → "—" / "8h" / "2d 3h". */
function formatHoras(h?: number | null): string {
  if (h == null) return '—';
  const horas = Math.round(h);
  if (horas < 24) return `${horas}h`;
  const d = Math.floor(horas / 24);
  const r = horas % 24;
  return r ? `${d}d ${r}h` : `${d}d`;
}

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
  const [propostaAberta, setPropostaAberta] = useState<FreelaKanbanItem | null>(null);

  function refetchTudo() {
    void kanban.refetch();
    void metricas.refetch();
    void projetos.refetch();
  }

  const m = metricas.data;
  // Cold start: ainda sem nenhuma fechada → o foco é RESPOSTA, não fechamento.
  const coldStart = (m?.fechadas ?? 0) === 0;

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
          trend={m ? `${m.enviadas} enviadas` : undefined}
          loading={metricas.loading}
        />
        <StatCard
          label="Taxa de resposta"
          value={m ? `${Math.round(m.taxa_resposta * 100)}%` : '—'}
          trend={m ? `${m.respondidas} responderam` : undefined}
          trendDirection={m && m.taxa_resposta >= 0.15 ? 'up' : 'neutral'}
          loading={metricas.loading}
        />
        {coldStart ? (
          <>
            <StatCard
              label="Em conversa"
              value={m?.respondidas ?? 0}
              trend="responderam ou negociando"
              loading={metricas.loading}
            />
            <StatCard
              label="Tempo até resposta"
              value={formatHoras(m?.tempo_medio_resposta_horas)}
              trend="quanto antes, melhor"
              loading={metricas.loading}
            />
          </>
        ) : (
          <>
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
          </>
        )}
      </div>

      {!coldStart && <MetaForecast m={m} loading={metricas.loading} />}

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
          onExtrair={acoes.extrairProjeto}
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
        onAbrir={setPropostaAberta}
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

      {propostaAberta && (
        <PropostaModal
          item={propostaAberta}
          onClose={() => setPropostaAberta(null)}
          onMudou={refetchTudo}
        />
      )}
    </div>
  );
}

// ── Modal de detalhe/edição da proposta (+ redator IA) ────────────

function PropostaModal({
  item,
  onClose,
  onMudou,
}: {
  item: FreelaKanbanItem;
  onClose: () => void;
  onMudou: () => void;
}) {
  const { proposta, loading, refetch } = useFreelaProposta(item.id);
  const acoes = useFreelaActions();

  const [texto, setTexto] = useState<string | null>(null);
  const [prazo, setPrazo] = useState<string | null>(null);
  const [valor, setValor] = useState<string | null>(null);
  const [liquido, setLiquido] = useState<string | null>(null);
  const [horas, setHoras] = useState<string | null>(null);
  const [instrucoes, setInstrucoes] = useState('');
  const [copiado, setCopiado] = useState(false);
  const [variacoes, setVariacoes] = useState<string[]>([]);
  const [objecao, setObjecao] = useState('');
  const [negOpcoes, setNegOpcoes] = useState<string[]>([]);
  const [checklist, setChecklist] = useState<FreelaChecklist | null>(null);

  // valores efetivos: o que foi editado, senão o que veio do servidor
  const textoEf = texto ?? proposta?.texto_enviado ?? '';
  const prazoEf = prazo ?? proposta?.prazo_proposto ?? '';
  const valorEf = valor ?? (proposta?.valor_cotado != null ? String(proposta.valor_cotado) : '');
  const liquidoEf = liquido ?? (proposta?.valor_liquido_estimado != null ? String(proposta.valor_liquido_estimado) : '');
  const horasEf = horas ?? (proposta?.horas_estimadas != null ? String(proposta.horas_estimadas) : '');

  async function redigir() {
    const r = await acoes.redigirProposta(item.id, instrucoes || null);
    if (r) {
      setTexto(r.redacao.texto);
      setPrazo(r.redacao.prazo_sugerido ?? prazoEf);
      setVariacoes(r.redacao.variacoes_abertura || []);
      void refetch();
    }
  }

  function usarAbertura(ab: string) {
    const base = textoEf;
    const idx = base.indexOf('\n\n');
    const corpo = idx >= 0 ? base.slice(idx) : base ? `\n\n${base}` : '';
    setTexto(`${ab.trim()}${corpo}`);
  }

  async function negociar() {
    if (!objecao.trim()) return;
    const r = await acoes.negociarProposta(item.id, objecao.trim());
    if (r) setNegOpcoes(r.opcoes);
  }

  async function conferir() {
    if (!textoEf.trim()) return;
    // salva o texto atual antes (a avaliação lê o que está persistido)
    await acoes.atualizarProposta(item.id, {
      texto_enviado: textoEf,
      prazo_proposto: prazoEf || null,
    });
    const r = await acoes.avaliarProposta(item.id);
    if (r) setChecklist(r);
  }

  async function corrigir() {
    if (!checklist) return;
    const correcoes = [
      ...checklist.itens
        .filter((i) => !i.ok)
        .map((i) => (i.nota ? `${i.criterio}: ${i.nota}` : i.criterio)),
      ...checklist.sugestoes,
      ...(checklist.alerta_conformidade
        ? ['Remova qualquer e-mail, telefone, WhatsApp ou link do texto.']
        : []),
    ];
    const r = await acoes.corrigirProposta(item.id, correcoes);
    if (r) {
      setTexto(r.redacao.texto);
      setPrazo(r.redacao.prazo_sugerido ?? prazoEf);
      setVariacoes(r.redacao.variacoes_abertura || []);
      setChecklist(null); // limpa pra você reconferir o texto corrigido
      void refetch();
    }
  }

  async function salvar() {
    await acoes.atualizarProposta(item.id, {
      texto_enviado: textoEf,
      prazo_proposto: prazoEf || null,
      valor_cotado: valorEf ? Number(valorEf) : null,
      valor_liquido_estimado: liquidoEf ? Number(liquidoEf) : null,
      horas_estimadas: horasEf ? Number(horasEf) : null,
    });
    onMudou();
    onClose();
  }

  async function copiar() {
    try {
      await navigator.clipboard.writeText(textoEf);
      setCopiado(true);
      setTimeout(() => setCopiado(false), 1500);
    } catch {
      /* clipboard pode falhar em http; ignora */
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 bg-black/40 flex items-start justify-center overflow-y-auto p-4"
      onClick={onClose}
    >
      <div
        className="card w-full max-w-[680px] my-8 p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-3 mb-4">
          <div className="min-w-0">
            <div className="eyebrow mb-1">Proposta</div>
            <h3 className="font-display font-semibold text-lg text-ink m-0 truncate">
              {item.projeto_titulo}
            </h3>
            {item.cliente_nome && (
              <div className="text-[13px] text-ink-mute">{item.cliente_nome}</div>
            )}
          </div>
          <button type="button" className="text-ink-mute hover:text-ink text-xl leading-none" onClick={onClose}>
            ×
          </button>
        </div>

        {loading && !proposta ? (
          <div className="text-sm text-ink-mute">Carregando…</div>
        ) : (
          <>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4 text-[13px]">
              <label className="text-ink-soft">
                Cotar (R$)
                <input className="input mt-1" type="number" value={valorEf} onChange={(e) => setValor(e.target.value)} />
              </label>
              <label className="text-ink-soft">
                Líquido (R$)
                <input className="input mt-1" type="number" value={liquidoEf} onChange={(e) => setLiquido(e.target.value)} />
              </label>
              <label className="text-ink-soft">
                Horas
                <input className="input mt-1" type="number" value={horasEf} onChange={(e) => setHoras(e.target.value)} />
              </label>
              <label className="text-ink-soft">
                Prazo
                <input className="input mt-1" value={prazoEf} onChange={(e) => setPrazo(e.target.value)} />
              </label>
            </div>

            {item.status === 'fechada' && (
              <PedirAvaliacao projeto={item.projeto_titulo} />
            )}

            {/* Destaques do seletor */}
            {(proposta?.projetos_destacados?.length || proposta?.habilidades_destacadas?.length) ? (
              <div className="mb-4 flex flex-wrap gap-1.5">
                {proposta?.projetos_destacados?.map((p) => (
                  <span key={p} className="text-[11px] px-2 py-0.5 rounded bg-brand-soft text-brand-ink">{p}</span>
                ))}
                {proposta?.habilidades_destacadas?.map((h) => (
                  <span key={h} className="text-[11px] px-2 py-0.5 rounded bg-bg-alt text-ink-soft border border-line">{h}</span>
                ))}
              </div>
            ) : null}

            {/* Redator IA */}
            <div className="rounded border border-line bg-bg-alt/50 p-3 mb-3">
              <div className="text-[13px] font-medium text-ink mb-1.5">✍️ Rascunhar com IA</div>
              <input
                className="input mb-2"
                placeholder="Instruções extra (opcional) — ex: cita teste no Safari iOS"
                value={instrucoes}
                onChange={(e) => setInstrucoes(e.target.value)}
              />
              <button type="button" className="btn-primary" onClick={redigir} disabled={acoes.loading}>
                {acoes.loading ? 'Gerando…' : proposta?.texto_enviado ? 'Regerar rascunho' : 'Gerar rascunho'}
              </button>
              {acoes.error && <div className="text-[12px] text-red-600 mt-1.5">{acoes.error.message}</div>}
            </div>

            {variacoes.length > 0 && (
              <div className="mb-3">
                <div className="text-[12px] font-medium text-ink-soft mb-1.5">
                  Aberturas alternativas (A/B) — clique pra usar
                </div>
                <div className="flex flex-col gap-1.5">
                  {variacoes.map((ab, i) => (
                    <button
                      key={i}
                      type="button"
                      className="text-left text-[13px] text-ink-soft border border-line rounded p-2 hover:border-brand hover:bg-brand-soft/30"
                      onClick={() => usarAbertura(ab)}
                    >
                      {ab}
                    </button>
                  ))}
                </div>
              </div>
            )}

            <label className="text-[13px] text-ink-soft">
              Texto da proposta (revise antes de enviar na Workana)
              <textarea
                className="input mt-1 min-h-[260px] font-mono text-[13px]"
                value={textoEf}
                onChange={(e) => setTexto(e.target.value)}
                placeholder="Gere com a IA ou escreva aqui…"
              />
            </label>

            {/* Gate anti-genérico */}
            <div className="rounded border border-line bg-bg-alt/50 p-3 mt-3">
              <div className="flex items-center justify-between gap-2">
                <div className="text-[13px] font-medium text-ink">
                  ✅ Conferir antes de enviar (anti-genérico)
                </div>
                <button
                  type="button"
                  className="btn-ghost text-[12px] px-2 py-1"
                  onClick={conferir}
                  disabled={acoes.loading || !textoEf.trim()}
                >
                  {acoes.loading ? 'Conferindo…' : 'Conferir proposta'}
                </button>
              </div>
              {checklist && <ChecklistView c={checklist} />}
              {checklist && checklist.selo !== 'pronta' && (
                <button
                  type="button"
                  className="btn-primary text-[12px] mt-2"
                  onClick={corrigir}
                  disabled={acoes.loading}
                >
                  {acoes.loading ? 'Corrigindo…' : '🔧 Corrigir proposta com IA'}
                </button>
              )}
            </div>

            {/* Assistente de negociação */}
            <div className="rounded border border-line bg-bg-alt/50 p-3 mt-3">
              <div className="text-[13px] font-medium text-ink mb-1.5">
                🤝 Cliente pediu desconto? Defenda o valor
              </div>
              <div className="flex gap-2">
                <input
                  className="input flex-1"
                  placeholder='O que o cliente falou — ex: "tá caro, faz por R$3000?"'
                  value={objecao}
                  onChange={(e) => setObjecao(e.target.value)}
                />
                <button type="button" className="btn-primary" onClick={negociar} disabled={acoes.loading || !objecao.trim()}>
                  {acoes.loading ? '…' : 'Sugerir'}
                </button>
              </div>
              {negOpcoes.length > 0 && (
                <div className="flex flex-col gap-1.5 mt-2">
                  {negOpcoes.map((o, i) => (
                    <button
                      key={i}
                      type="button"
                      className="text-left text-[13px] text-ink-soft border border-line rounded p-2 hover:border-brand hover:bg-brand-soft/30"
                      title="Clique pra copiar"
                      onClick={() => navigator.clipboard?.writeText(o)}
                    >
                      {o}
                    </button>
                  ))}
                </div>
              )}
            </div>

            <div className="flex items-center justify-between mt-4">
              <button type="button" className="btn-ghost text-[13px]" onClick={copiar} disabled={!textoEf}>
                {copiado ? '✓ Copiado' : 'Copiar texto'}
              </button>
              <div className="flex gap-2">
                <button type="button" className="btn-ghost" onClick={onClose}>
                  Fechar
                </button>
                <button type="button" className="btn-primary" onClick={salvar} disabled={acoes.loading}>
                  Salvar
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function ChecklistView({ c }: { c: FreelaChecklist }) {
  const cor =
    c.selo === 'pronta'
      ? 'bg-success-soft text-success-ink'
      : c.selo === 'ajustar'
        ? 'bg-brand-soft text-brand-ink'
        : 'bg-red-100 text-red-700';
  const rotulo =
    c.selo === 'pronta' ? 'Pronta' : c.selo === 'ajustar' ? 'Dá pra melhorar' : 'Fraca';

  return (
    <div className="mt-2.5">
      <div className="flex items-center gap-2 mb-2">
        <span className={`text-[12px] font-medium px-2 py-0.5 rounded ${cor}`}>
          {rotulo}
        </span>
        <span className="font-mono text-[12px] text-ink-mute">{c.score}/100</span>
      </div>

      {c.alerta_conformidade && (
        <div className="text-[12px] text-red-700 bg-red-50 border border-red-200 rounded p-2 mb-2">
          ⚠️ {c.alerta_conformidade}
        </div>
      )}

      <ul className="flex flex-col gap-1 mb-2">
        {c.itens.map((it, i) => (
          <li key={i} className="text-[12px] flex gap-1.5">
            <span className={it.ok ? 'text-success' : 'text-red-600'}>
              {it.ok ? '✓' : '✗'}
            </span>
            <span className="text-ink-soft">
              <span className="text-ink">{it.criterio}.</span>
              {it.nota ? ` ${it.nota}` : ''}
            </span>
          </li>
        ))}
      </ul>

      {c.sugestoes.length > 0 && (
        <div className="text-[12px] text-ink-soft">
          <div className="font-medium text-ink-mute mb-0.5">Pra melhorar:</div>
          <ul className="list-disc pl-4 flex flex-col gap-0.5">
            {c.sugestoes.map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function PedirAvaliacao({ projeto }: { projeto: string }) {
  const [copiado, setCopiado] = useState(false);
  const msg =
    `Foi um prazer trabalhar no projeto "${projeto}"! 🙌 ` +
    `Se você ficou satisfeito com a entrega, uma avaliação aqui na Workana me ` +
    `ajudaria muito e leva só um minuto. Qualquer ajuste, é só me chamar.`;
  async function copiar() {
    try {
      await navigator.clipboard.writeText(msg);
      setCopiado(true);
      setTimeout(() => setCopiado(false), 1500);
    } catch {
      /* ignora */
    }
  }
  return (
    <div className="rounded border border-emerald-200 bg-emerald-50 p-3 mb-4">
      <div className="text-[13px] font-medium text-emerald-800 mb-1">
        ⭐ Fechou! Peça a avaliação 5★ (a 1ª é a mais valiosa)
      </div>
      <p className="text-[13px] text-ink-soft m-0 mb-2">{msg}</p>
      <button type="button" className="btn-ghost text-[13px]" onClick={copiar}>
        {copiado ? '✓ Copiado' : 'Copiar mensagem'}
      </button>
    </div>
  );
}

// ── Forecast de pipeline + meta mensal ────────────────────────────

const META_KEY = 'freela_meta_mensal';

function MetaForecast({ m, loading }: { m: FreelaMetricas | null; loading: boolean }) {
  const [meta, setMeta] = useState<number>(0);

  useEffect(() => {
    const v = Number(localStorage.getItem(META_KEY) || '0');
    if (!Number.isNaN(v)) setMeta(v);
  }, []);

  function salvarMeta(v: number) {
    setMeta(v);
    localStorage.setItem(META_KEY, String(v || 0));
  }

  const fechado = m?.liquido_total_fechado ?? 0;
  const forecast = m?.forecast_liquido ?? 0;
  const projetado = fechado + forecast; // o que já entrou + o provável
  const pctFechado = meta > 0 ? Math.min(100, (fechado / meta) * 100) : 0;
  const pctProjetado = meta > 0 ? Math.min(100, (projetado / meta) * 100) : 0;
  const falta = Math.max(0, meta - projetado);

  return (
    <div className="card p-5 mb-3">
      <div className="grid md:grid-cols-[1fr_1fr_1.4fr] gap-5 items-center">
        <div>
          <div className="text-[11px] uppercase tracking-wide text-ink-mute">Pipeline em aberto</div>
          <div className="font-display font-semibold text-lg text-ink mt-0.5">
            {loading ? '…' : formatBRL(m?.pipeline_aberto_liquido ?? 0)}
          </div>
          <div className="text-[12px] text-ink-faint">{m?.em_aberto ?? 0} proposta(s) aguardando</div>
        </div>
        <div>
          <div className="text-[11px] uppercase tracking-wide text-ink-mute">Previsão (ponderada)</div>
          <div className="font-display font-semibold text-lg text-brand-ink mt-0.5">
            {loading ? '…' : formatBRL(forecast)}
          </div>
          <div className="text-[12px] text-ink-faint">
            pipeline × {Math.round((m?.taxa_fechamento ?? 0) * 100)}% de fechamento
          </div>
        </div>
        <div>
          <div className="flex items-center justify-between mb-1">
            <span className="text-[11px] uppercase tracking-wide text-ink-mute">Meta</span>
            <label className="text-[12px] text-ink-soft flex items-center gap-1">
              R$
              <input
                type="number"
                className="input py-1 w-28 text-[13px]"
                value={meta || ''}
                placeholder="0"
                onChange={(e) => salvarMeta(Number(e.target.value))}
              />
            </label>
          </div>
          {meta > 0 ? (
            <>
              <div className="h-2.5 rounded-full bg-bg-alt overflow-hidden relative">
                {/* projetado (mais claro) + fechado (forte) */}
                <div className="absolute inset-y-0 left-0 bg-brand/30" style={{ width: `${pctProjetado}%` }} />
                <div className="absolute inset-y-0 left-0 bg-brand" style={{ width: `${pctFechado}%` }} />
              </div>
              <div className="text-[12px] text-ink-soft mt-1">
                {falta > 0 ? (
                  <>Faltam <strong>{formatBRL(falta)}</strong> (fechado + previsto = {formatBRL(projetado)}).</>
                ) : (
                  <>🎉 Meta coberta pelo fechado + previsto ({formatBRL(projetado)}).</>
                )}
              </div>
            </>
          ) : (
            <div className="text-[12px] text-ink-faint">Defina uma meta pra ver quanto falta.</div>
          )}
        </div>
      </div>

      {(m?.tempo_medio_resposta_horas != null || m?.valor_hora_real != null) && (
        <div className="mt-3 pt-3 border-t border-line flex flex-wrap gap-x-6 gap-y-1 text-[12px] text-ink-soft">
          {m?.tempo_medio_resposta_horas != null && (
            <span>⏱ Resposta média do cliente: <strong>{m.tempo_medio_resposta_horas}h</strong></span>
          )}
          {m?.valor_hora_real != null && (
            <span>💵 Seu valor-hora real (fechadas): <strong>{formatBRL(m.valor_hora_real)}/h</strong></span>
          )}
        </div>
      )}
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
  ) => Promise<void> | void;
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
  ) => Promise<void> | void;
  onAnalisar: (id: string) => Promise<FreelaAnalise | null>;
  onRemover: (id: string) => void;
}) {
  const [analise, setAnalise] = useState<FreelaAnalise | null>(null);
  const [analisando, setAnalisando] = useState(false);
  const [criando, setCriando] = useState(false);
  const [aviso, setAviso] = useState<string | null>(null);

  const orcamento =
    p.faixa_orcamento_min != null || p.faixa_orcamento_max != null
      ? `${formatBRL(p.faixa_orcamento_min ?? 0)} – ${formatBRL(p.faixa_orcamento_max ?? 0)}`
      : null;

  async function analisar() {
    setAnalisando(true);
    const a = await onAnalisar(p.id);
    if (a) setAnalise(a);
    setAnalisando(false);
    return a;
  }

  // "+ Proposta": um clique já CRIA o card. Analisa se preciso e usa a
  // estimativa de mercado (valor sugerido, horas, dias). Você ajusta no card.
  async function criarProposta() {
    setAviso(null);
    setCriando(true);
    let est = analise?.estimativa ?? p.estimativa ?? null;
    if (!est) {
      const a = await analisar();
      if (!a) {
        // Análise falhou (IA indisponível/limite) — não cria card vazio.
        setCriando(false);
        setAviso('Não consegui analisar agora (IA indisponível). Tente de novo em instantes.');
        return;
      }
      est = a.estimativa ?? null;
    }
    const valor = est?.valor_sugerido ?? null;
    await onCriarProposta(
      p.id,
      valor,
      null,
      est?.horas_estimadas ?? null,
      est?.prazo_dias != null ? `${est.prazo_dias} dias` : null,
    );
    setCriando(false);
    setAviso(
      valor != null
        ? 'Proposta criada no Kanban com o orçamento de mercado — abra o card pra ajustar e rascunhar.'
        : 'Proposta criada, mas o escopo não deu pra estimar a cotação — abra o card e defina o valor.',
    );
  }

  return (
    <div className="card p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="font-medium text-ink text-[15px] truncate">{p.titulo}</div>
          <div className="mt-1 flex flex-wrap items-center gap-2 text-[12px] text-ink-mute">
            {p.cliente_nome && <span>{p.cliente_nome}</span>}
            {p.cliente_recorrente && (
              <span
                className="text-[11px] font-medium px-1.5 py-0.5 rounded bg-amber-100 text-amber-800"
                title={`Cliente recorrente — já te pagou US$ ${p.cliente_pago_usd.toFixed(0)} (comissão menor)`}
              >
                ★ recorrente
              </span>
            )}
            {orcamento && <span>· {orcamento}</span>}
            {p.n_propostas_concorrentes != null && (
              <span>· {p.n_propostas_concorrentes} propostas</span>
            )}
            <span>· {p.qtd_propostas} sua(s)</span>
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {p.risco && p.risco !== 'baixo' && (
            <span
              className={`text-[12px] font-medium px-2 py-0.5 rounded ${
                p.risco === 'alto'
                  ? 'bg-red-100 text-red-700'
                  : 'bg-amber-100 text-amber-800'
              }`}
              title="Risco detectado pela análise (cliente/escopo)"
            >
              ⚠️ risco {p.risco}
            </span>
          )}
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
            className="btn-primary text-[13px] disabled:opacity-40"
            onClick={criarProposta}
            disabled={analisando || criando}
            title="Analisa o projeto e cria a proposta no Kanban com orçamento de mercado, horas e dias"
          >
            {analisando ? 'Analisando…' : criando ? 'Criando…' : '+ Proposta'}
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
            {analise.risco && analise.risco !== 'baixo' && (
              <span
                className={`text-[12px] font-medium px-2 py-0.5 rounded ${
                  analise.risco === 'alto' ? 'bg-red-100 text-red-700' : 'bg-amber-100 text-amber-800'
                }`}
              >
                ⚠️ risco {analise.risco}
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

      {aviso && (
        <div className="mt-3 border-t border-line pt-3 text-[12px] text-emerald-700">
          ✓ {aviso}
        </div>
      )}
    </div>
  );
}

// ── Kanban ────────────────────────────────────────────────────────

function Kanban({
  colunas,
  loading,
  onAbrir,
  onMover,
  onRemover,
}: {
  colunas: FreelaKanbanColuna[];
  loading: boolean;
  onAbrir: (item: FreelaKanbanItem) => void;
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
                <button
                  type="button"
                  className="text-[13px] font-medium text-ink truncate text-left w-full hover:text-brand"
                  title="Abrir proposta"
                  onClick={() => onAbrir(it)}
                >
                  {it.projeto_titulo}
                </button>
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
  onExtrair,
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
  onExtrair: (texto: string) => Promise<FreelaExtrairProjeto | null>;
}) {
  const [titulo, setTitulo] = useState('');
  const [descricao, setDescricao] = useState('');
  const [clienteId, setClienteId] = useState('');
  const [min, setMin] = useState('');
  const [max, setMax] = useState('');
  const [nProp, setNProp] = useState('');
  const [extraindo, setExtraindo] = useState(false);

  async function autoPreencher() {
    if (!descricao.trim()) return;
    setExtraindo(true);
    const r = await onExtrair(descricao.trim());
    setExtraindo(false);
    if (!r) return;
    if (r.titulo && !titulo.trim()) setTitulo(r.titulo);
    if (r.faixa_orcamento_min != null) setMin(String(r.faixa_orcamento_min));
    if (r.faixa_orcamento_max != null) setMax(String(r.faixa_orcamento_max));
    if (r.n_propostas_concorrentes != null) setNProp(String(r.n_propostas_concorrentes));
  }

  return (
    <div className="card p-5 mb-4">
      <div className="grid gap-3">
        <label className="text-[13px] text-ink-soft">
          Título do projeto
          <input className="input mt-1" value={titulo} onChange={(e) => setTitulo(e.target.value)} />
        </label>
        <div>
          <div className="flex items-center justify-between gap-2 mb-1">
            <span className="text-[13px] text-ink-soft">
              Descrição (cole o texto do projeto)
            </span>
            <button
              type="button"
              className="btn-ghost text-[12px] px-2 py-1 disabled:opacity-40"
              onClick={autoPreencher}
              disabled={extraindo || !descricao.trim()}
              title="A IA lê o texto e preenche título, orçamento e nº de propostas"
            >
              {extraindo ? 'Lendo…' : '✨ Auto-preencher do texto'}
            </button>
          </div>
          <textarea
            className="input min-h-[120px]"
            value={descricao}
            onChange={(e) => setDescricao(e.target.value)}
          />
        </div>
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

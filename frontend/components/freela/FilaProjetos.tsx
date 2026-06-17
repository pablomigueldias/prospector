import { useState } from 'react';

import { formatBRL } from '@/lib/format';
import { type FreelaAnalise, type FreelaProjetoListItem } from '@/lib/types';

// ── Fila de projetos ──────────────────────────────────────────────

export function FilaProjetos({
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
        Nenhum projeto na fila. Clique em &quot;Colar projeto&quot;.
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

// Quadrante dificuldade × esforço (vem do analise_json, calculado no backend).
const QUADRANTE_META: Record<string, { label: string; cls: string; title: string }> = {
  quick_win: {
    label: '⚡ quick win',
    cls: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    title: 'Rápido e fácil — ótimo pra cravar reputação no começo',
  },
  dificil_longo: {
    label: '🏔️ difícil & longo',
    cls: 'bg-violet-50 text-violet-700 border-violet-200',
    title: 'Técnico e demorado — ticket alto, mais risco; cote com folga',
  },
  escopo_vago: {
    label: '⚠️ escopo vago',
    cls: 'bg-amber-50 text-amber-800 border-amber-200',
    title: 'Cliente descreveu pouco — risco de scope creep; pergunte antes de cotar',
  },
  padrao: {
    label: '◑ padrão',
    cls: 'bg-bg-alt text-ink-soft border-line',
    title: 'Dificuldade/esforço medianos',
  },
};

// Veredito de preço (orçamento do cliente × mercado, determinístico no backend).
const PRECO_META: Record<string, { label: string; cls: string }> = {
  subcotado: { label: '🔴 subcotado', cls: 'bg-red-50 text-red-700 border-red-200' },
  justo: { label: '🟢 preço justo', cls: 'bg-emerald-50 text-emerald-700 border-emerald-200' },
  acima: { label: '💎 paga acima', cls: 'bg-sky-50 text-sky-700 border-sky-200' },
  sem_orcamento: { label: '❔ sem orçamento', cls: 'bg-bg-alt text-ink-soft border-line' },
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
          {p.quadrante && QUADRANTE_META[p.quadrante] && (
            <span
              className={`text-[12px] font-medium px-2 py-0.5 rounded border ${QUADRANTE_META[p.quadrante].cls}`}
              title={QUADRANTE_META[p.quadrante].title}
            >
              {QUADRANTE_META[p.quadrante].label}
            </span>
          )}
          {p.preco_status && p.preco_status !== 'sem_orcamento' && PRECO_META[p.preco_status] && (
            <span
              className={`text-[12px] font-medium px-2 py-0.5 rounded border ${PRECO_META[p.preco_status].cls}`}
              title="Orçamento do cliente vs faixa de mercado"
            >
              {PRECO_META[p.preco_status].label}
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
            {analise.quadrante && QUADRANTE_META[analise.quadrante] && (
              <span
                className={`text-[12px] font-medium px-2 py-0.5 rounded border ${QUADRANTE_META[analise.quadrante].cls}`}
                title={QUADRANTE_META[analise.quadrante].title}
              >
                {QUADRANTE_META[analise.quadrante].label}
              </span>
            )}
            {analise.veredito_preco?.status && PRECO_META[analise.veredito_preco.status] && (
              <span
                className={`text-[12px] font-medium px-2 py-0.5 rounded border ${PRECO_META[analise.veredito_preco.status].cls}`}
              >
                {PRECO_META[analise.veredito_preco.status].label}
              </span>
            )}
          </div>
          {analise.veredito && <p className="text-ink-soft m-0 mb-2">{analise.veredito}</p>}
          {analise.veredito_preco?.gap_texto && (
            <p className="text-[12px] text-ink-soft m-0 mb-2">
              💰 {analise.veredito_preco.gap_texto}
              {analise.veredito_preco.rh_orcamento != null && (
                <> · orçamento ≈ <strong>{formatBRL(analise.veredito_preco.rh_orcamento)}/h</strong></>
              )}
            </p>
          )}
          {analise.tarefas?.length > 0 && (
            <div className="mb-2">
              <span className="text-[12px] font-medium text-ink">🧩 Escopo em tarefas:</span>
              <ul className="mt-0.5 text-ink-soft">
                {analise.tarefas.map((t, i) => (
                  <li key={i} className="flex justify-between gap-3 border-b border-line/50 py-0.5">
                    <span>{t.nome}</span>
                    {t.horas != null && (
                      <span className="text-ink-faint shrink-0 tabular-nums">{t.horas}h</span>
                    )}
                  </li>
                ))}
                {(() => {
                  const total = analise.tarefas.reduce((s, t) => s + (t.horas ?? 0), 0);
                  return total > 0 ? (
                    <li className="flex justify-between gap-3 py-0.5 font-medium text-ink">
                      <span>Total</span>
                      <span className="tabular-nums">{total}h</span>
                    </li>
                  ) : null;
                })()}
              </ul>
            </div>
          )}
          {analise.perguntas_cliente?.length > 0 && (
            <div className="mb-2">
              <span className="text-[12px] font-medium text-sky-700">
                ❓ Perguntar ao cliente antes de cotar:
              </span>
              <ul className="list-disc ml-5 text-ink-soft">
                {analise.perguntas_cliente.map((q, i) => (
                  <li key={i}>{q}</li>
                ))}
              </ul>
            </div>
          )}
          {analise.skills_faltando?.length > 0 && (
            <div className="mb-1.5">
              <span className="text-[12px] font-medium text-amber-700">
                ⚠️ Gap de skill (o projeto pede e não vi no seu perfil):
              </span>
              <div className="flex flex-wrap gap-1 mt-1">
                {analise.skills_faltando.map((s, i) => (
                  <span
                    key={i}
                    className="text-[12px] px-2 py-0.5 rounded border bg-amber-50 text-amber-800 border-amber-200"
                  >
                    {s}
                  </span>
                ))}
              </div>
            </div>
          )}
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


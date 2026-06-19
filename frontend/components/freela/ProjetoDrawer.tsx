import { useState } from 'react';

import { SidePanel } from '@/components/shared/SidePanel';
import { useFetch } from '@/hooks/useFetch';
import { api } from '@/lib/api';
import { formatBRL } from '@/lib/format';
import {
  type FreelaAnalise,
  type FreelaProjeto,
  type FreelaProjetoListItem,
} from '@/lib/types';

const MOMENTO: Record<string, { label: string; cls: string }> = {
  agora: { label: '✅ É o momento', cls: 'bg-emerald-100 text-emerald-800 border-emerald-300' },
  espere: { label: '⏳ Pode esperar', cls: 'bg-amber-50 text-amber-800 border-amber-200' },
  passe: { label: '⏭️ Passe', cls: 'bg-bg-alt text-ink-mute border-line' },
};
const QUADRANTE: Record<string, string> = {
  quick_win: '⚡ quick win — rápido e fácil, ótimo pra cravar reputação',
  dificil_longo: '🏔️ difícil & longo — ticket alto, mais risco; cote com folga',
  escopo_vago: '⚠️ escopo vago — risco de scope creep; pergunte antes de cotar',
  padrao: '◑ padrão — dificuldade/esforço medianos',
};
const PRECO: Record<string, string> = {
  subcotado: '🔴 subcotado',
  justo: '🟢 preço justo',
  acima: '💎 paga acima',
  sem_orcamento: '❔ sem orçamento',
};

function Pill({ children, cls = 'bg-bg-alt text-ink-soft border-line' }: { children: React.ReactNode; cls?: string }) {
  return <span className={`text-[12px] font-medium px-2 py-0.5 rounded border ${cls}`}>{children}</span>;
}

/**
 * Drawer 360 do projeto da fila: explica o PORQUÊ da decisão (momento, fit,
 * risco, quadrante, preço, frescor, concorrência, "bom 1º projeto") e deixa
 * editar todos os campos. Reusa o SidePanel padrão; busca o detalhe (descrição
 * + análise completa) ao abrir.
 */
export function ProjetoDrawer({
  projeto,
  clientes,
  plataformas,
  salvando,
  onClose,
  onAtualizar,
  onAnalisar,
  onMudou,
}: {
  projeto: FreelaProjetoListItem;
  clientes: { id: string; nome: string }[];
  plataformas: { id: string; nome: string }[];
  salvando: boolean;
  onClose: () => void;
  onAtualizar: (id: string, patch: Partial<FreelaProjeto>) => Promise<void>;
  onAnalisar: (id: string) => Promise<unknown>;
  onMudou: () => void;
}) {
  const { data: detalhe, loading, refetch } = useFetch(
    () => api.freelaProjetoDetalhe(projeto.id),
    [projeto.id],
  );
  const [analisando, setAnalisando] = useState(false);

  const analise = (detalhe?.analise_json ?? null) as FreelaAnalise | null;
  const est = projeto.estimativa;
  const p = projeto;

  // Bullets do "porquê" — só os sinais presentes.
  const porques: string[] = [];
  if (p.fit_score != null)
    porques.push(`Fit ${p.fit_score} — ${p.fit_score >= 70 ? 'dentro do seu núcleo' : p.fit_score >= 40 ? 'parcial' : 'fora do núcleo'}.`);
  if (p.risco && p.risco !== 'baixo') porques.push(`Risco ${p.risco} (cliente/escopo).`);
  if (p.quadrante && QUADRANTE[p.quadrante]) porques.push(QUADRANTE[p.quadrante]);
  if (p.preco_status && PRECO[p.preco_status]) porques.push(`Preço: ${PRECO[p.preco_status]}${analise?.veredito_preco?.gap_texto ? ` — ${analise.veredito_preco.gap_texto}` : ''}.`);
  if (p.dias_desde_publicacao != null)
    porques.push(`Publicado há ${p.dias_desde_publicacao}d${p.dias_desde_publicacao <= 3 ? ' — fresco, responder cedo é vantagem' : ''}.`);
  if (p.n_propostas_concorrentes != null) porques.push(`${p.n_propostas_concorrentes} concorrentes.`);
  if (p.bom_primeiro) porques.push(`🌱 Bom 1º projeto: ${p.bom_primeiro_motivos.join(', ')}.`);
  if (p.cliente_recorrente) porques.push(`Cliente recorrente — já te pagou US$ ${p.cliente_pago_usd.toFixed(0)}.`);

  async function analisar() {
    setAnalisando(true);
    await onAnalisar(projeto.id);
    setAnalisando(false);
    void refetch();
    onMudou();
  }

  return (
    <SidePanel
      open
      onClose={onClose}
      title={p.titulo}
      acoes={
        <button
          type="button"
          className="btn-ghost text-[13px]"
          onClick={analisar}
          disabled={analisando}
        >
          {analisando ? 'Analisando…' : p.tem_analise ? 'Reanalisar' : '🔎 Analisar'}
        </button>
      }
    >
      {/* Veredito */}
      <div className="flex flex-wrap items-center gap-2 mb-3">
        {p.momento && MOMENTO[p.momento] && <Pill cls={MOMENTO[p.momento].cls}>{MOMENTO[p.momento].label}</Pill>}
        {p.bom_primeiro && <Pill cls="bg-emerald-50 text-emerald-700 border-emerald-200">🌱 bom 1º projeto</Pill>}
        {p.dias_desde_publicacao != null && p.dias_desde_publicacao <= 3 && (
          <Pill cls="bg-sky-50 text-sky-700 border-sky-200">🆕 {p.dias_desde_publicacao === 0 ? 'hoje' : `${p.dias_desde_publicacao}d`}</Pill>
        )}
      </div>
      {p.momento_motivo && <p className="text-[13.5px] text-ink-soft mt-0 mb-4">{p.momento_motivo}</p>}

      {/* Por quê — detalhamento da decisão */}
      <Secao titulo="Por que essa decisão">
        {porques.length ? (
          <ul className="list-disc ml-5 text-[13px] text-ink-soft flex flex-col gap-0.5">
            {porques.map((q, i) => <li key={i}>{q}</li>)}
          </ul>
        ) : (
          <p className="text-[13px] text-ink-mute m-0">Analise o projeto pra ver o veredito detalhado.</p>
        )}
        {est && (
          <p className="text-[12.5px] text-ink-mute mt-2 mb-0">
            Estimativa: {est.horas_estimadas != null ? `${est.horas_estimadas}h` : '—'}
            {est.valor_sugerido != null && <> · sugerido {formatBRL(est.valor_sugerido)}</>}
            {est.prazo_dias != null && <> · {est.prazo_dias} dias</>}
          </p>
        )}
      </Secao>

      {/* Editáveis */}
      {loading && !detalhe ? (
        <div className="animate-pulse h-40 mt-4" />
      ) : detalhe ? (
        <EditForm
          key={detalhe.id}
          detalhe={detalhe}
          clientes={clientes}
          plataformas={plataformas}
          salvando={salvando}
          onSalvar={async (patch) => {
            await onAtualizar(projeto.id, patch);
            await refetch();
            onMudou();
          }}
        />
      ) : null}

      {/* Análise detalhada */}
      {analise && (
        <Secao titulo="Análise">
          {analise.veredito && <p className="text-[13px] text-ink-soft mt-0 mb-2">{analise.veredito}</p>}
          {analise.tarefas?.length > 0 && (
            <Bloco titulo="🧩 Escopo em tarefas">
              <ul className="text-[13px] text-ink-soft">
                {analise.tarefas.map((t, i) => (
                  <li key={i} className="flex justify-between gap-3 border-b border-line/50 py-0.5">
                    <span>{t.nome}</span>
                    {t.horas != null && <span className="text-ink-faint tabular-nums shrink-0">{t.horas}h</span>}
                  </li>
                ))}
              </ul>
            </Bloco>
          )}
          {analise.perguntas_cliente?.length > 0 && (
            <Bloco titulo="❓ Perguntar antes de cotar" cor="text-sky-700">
              <ul className="list-disc ml-5 text-[13px] text-ink-soft">
                {analise.perguntas_cliente.map((q, i) => <li key={i}>{q}</li>)}
              </ul>
            </Bloco>
          )}
          {analise.skills_faltando?.length > 0 && (
            <Bloco titulo="⚠️ Gap de skill" cor="text-amber-700">
              <div className="flex flex-wrap gap-1">
                {analise.skills_faltando.map((s, i) => (
                  <span key={i} className="text-[12px] px-2 py-0.5 rounded border bg-amber-50 text-amber-800 border-amber-200">{s}</span>
                ))}
              </div>
            </Bloco>
          )}
          {analise.red_flags?.length > 0 && (
            <Bloco titulo="Red flags" cor="text-red-600">
              <ul className="list-disc ml-5 text-[13px] text-ink-soft">
                {analise.red_flags.map((r, i) => <li key={i}>{r}</li>)}
              </ul>
            </Bloco>
          )}
          {analise.ganchos?.length > 0 && (
            <Bloco titulo="Ganchos (seu perfil)" cor="text-emerald-700">
              <ul className="list-disc ml-5 text-[13px] text-ink-soft">
                {analise.ganchos.map((g, i) => <li key={i}>{g}</li>)}
              </ul>
            </Bloco>
          )}
        </Secao>
      )}
    </SidePanel>
  );
}

function Secao({ titulo, children }: { titulo: string; children: React.ReactNode }) {
  return (
    <section className="border-t border-line pt-4 mt-4">
      <h4 className="font-display font-semibold text-[13.5px] tracking-tight text-ink m-0 mb-2.5">{titulo}</h4>
      {children}
    </section>
  );
}

function Bloco({ titulo, cor = 'text-ink', children }: { titulo: string; cor?: string; children: React.ReactNode }) {
  return (
    <div className="mb-3">
      <span className={`text-[12px] font-medium ${cor}`}>{titulo}</span>
      <div className="mt-1">{children}</div>
    </div>
  );
}

function EditForm({
  detalhe,
  clientes,
  plataformas,
  salvando,
  onSalvar,
}: {
  detalhe: FreelaProjeto;
  clientes: { id: string; nome: string }[];
  plataformas: { id: string; nome: string }[];
  salvando: boolean;
  onSalvar: (patch: Partial<FreelaProjeto>) => void;
}) {
  const [titulo, setTitulo] = useState(detalhe.titulo);
  const [clienteId, setClienteId] = useState(detalhe.cliente_id ?? '');
  const [plataformaId, setPlataformaId] = useState(detalhe.plataforma_id ?? '');
  const [min, setMin] = useState(detalhe.faixa_orcamento_min != null ? String(detalhe.faixa_orcamento_min) : '');
  const [max, setMax] = useState(detalhe.faixa_orcamento_max != null ? String(detalhe.faixa_orcamento_max) : '');
  const [nProp, setNProp] = useState(detalhe.n_propostas_concorrentes != null ? String(detalhe.n_propostas_concorrentes) : '');
  const [nInteress, setNInteress] = useState(detalhe.n_interessados != null ? String(detalhe.n_interessados) : '');
  const [pubEm, setPubEm] = useState(detalhe.publicado_em ?? '');
  const [prazo, setPrazo] = useState(detalhe.prazo_estimado ?? '');
  const [status, setStatus] = useState(detalhe.status_no_site ?? '');
  const [habilidades, setHabilidades] = useState((detalhe.habilidades ?? []).join(', '));
  const [descricao, setDescricao] = useState(detalhe.descricao);

  const num = (s: string): number | null => (s.trim() ? Number(s) : null);

  return (
    <Secao titulo="Editar campos">
      <div className="grid gap-3">
        <label className="text-[13px] text-ink-soft">
          Título
          <input className="input mt-1" value={titulo} onChange={(e) => setTitulo(e.target.value)} />
        </label>
        <div className="grid grid-cols-2 gap-3">
          <label className="text-[13px] text-ink-soft">
            Cliente
            <select className="input mt-1" value={clienteId} onChange={(e) => setClienteId(e.target.value)}>
              <option value="">—</option>
              {clientes.map((c) => <option key={c.id} value={c.id}>{c.nome}</option>)}
            </select>
          </label>
          <label className="text-[13px] text-ink-soft">
            Plataforma
            <select className="input mt-1" value={plataformaId} onChange={(e) => setPlataformaId(e.target.value)}>
              <option value="">—</option>
              {plataformas.map((pl) => <option key={pl.id} value={pl.id}>{pl.nome}</option>)}
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
            Nº concorrentes
            <input className="input mt-1" type="number" value={nProp} onChange={(e) => setNProp(e.target.value)} />
          </label>
          <label className="text-[13px] text-ink-soft">
            Nº interessados
            <input className="input mt-1" type="number" value={nInteress} onChange={(e) => setNInteress(e.target.value)} />
          </label>
          <label className="text-[13px] text-ink-soft">
            Publicado em
            <input className="input mt-1" type="date" value={pubEm} onChange={(e) => setPubEm(e.target.value)} />
          </label>
          <label className="text-[13px] text-ink-soft">
            Prazo estimado
            <input className="input mt-1" value={prazo} onChange={(e) => setPrazo(e.target.value)} />
          </label>
        </div>
        <label className="text-[13px] text-ink-soft">
          Status no site
          <input className="input mt-1" value={status} onChange={(e) => setStatus(e.target.value)} />
        </label>
        <label className="text-[13px] text-ink-soft">
          Habilidades <span className="text-ink-faint">(vírgula)</span>
          <input className="input mt-1" value={habilidades} onChange={(e) => setHabilidades(e.target.value)} />
        </label>
        <label className="text-[13px] text-ink-soft">
          Descrição
          <textarea className="input mt-1 min-h-[120px]" value={descricao} onChange={(e) => setDescricao(e.target.value)} />
        </label>
        <div className="flex justify-end">
          <button
            type="button"
            className="btn-primary"
            disabled={salvando || !titulo.trim()}
            onClick={() =>
              onSalvar({
                titulo: titulo.trim(),
                cliente_id: clienteId || null,
                plataforma_id: plataformaId || null,
                faixa_orcamento_min: num(min),
                faixa_orcamento_max: num(max),
                n_propostas_concorrentes: num(nProp),
                n_interessados: num(nInteress),
                publicado_em: pubEm || null,
                prazo_estimado: prazo.trim() || null,
                status_no_site: status.trim() || null,
                habilidades: habilidades.split(',').map((s) => s.trim()).filter(Boolean),
                descricao: descricao.trim(),
              })
            }
          >
            {salvando ? 'Salvando…' : 'Salvar alterações'}
          </button>
        </div>
      </div>
    </Secao>
  );
}

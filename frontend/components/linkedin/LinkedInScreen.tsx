import { useMemo, useState } from 'react';

import { SidePanel } from '@/components/shared/SidePanel';
import { useLinkedinActions, useLinkedinPosts } from '@/hooks/useLinkedin';
import type {
  LinkedinConta,
  LinkedinFormato,
  LinkedinPost,
  LinkedinPostCreate,
  LinkedinStatus,
} from '@/lib/types';

const STATUS_TABS: { key: LinkedinStatus | 'todos'; label: string }[] = [
  { key: 'todos', label: 'Todos' },
  { key: 'rascunho', label: 'Rascunhos' },
  { key: 'aprovado', label: 'Aprovados' },
  { key: 'publicado', label: 'Publicados' },
  { key: 'arquivado', label: 'Arquivados' },
];

const STATUS_BADGE: Record<LinkedinStatus, string> = {
  rascunho: 'bg-bg-alt text-ink-mute',
  aprovado: 'bg-blue-100 text-blue-700',
  publicado: 'bg-green-100 text-green-700',
  arquivado: 'bg-amber-100 text-amber-700',
};

const CONTA_LABEL: Record<LinkedinConta, string> = {
  reative: 'Página Reative',
  pessoal: 'Perfil pessoal',
};

const CONTA_BADGE: Record<LinkedinConta, string> = {
  reative: 'bg-brand-soft text-brand',
  pessoal: 'bg-violet-100 text-violet-700',
};

const FORMATOS: LinkedinFormato[] = ['post', 'carrossel', 'artigo'];

type FormState = LinkedinPostCreate & { hashtagsText?: string };

const FORM_VAZIO: FormState = {
  titulo: '',
  conta: 'reative',
  formato: 'post',
  hook: '',
  body: '',
  cta: '',
  hashtagsText: '',
  notas: '',
  scheduled_for: null,
};

/** Junta as partes na ordem em que vão pro LinkedIn (o que o Pablo copia). */
function textoFinal(p: {
  hook?: string | null;
  body?: string | null;
  cta?: string | null;
  hashtags?: string[] | null;
}): string {
  const partes = [p.hook, p.body, p.cta]
    .map((s) => (s || '').trim())
    .filter(Boolean);
  let txt = partes.join('\n\n');
  if (p.hashtags && p.hashtags.length) {
    txt += `\n\n${p.hashtags.map((h) => `#${h}`).join(' ')}`;
  }
  return txt;
}

function parseHashtags(texto?: string): string[] {
  if (!texto) return [];
  return [
    ...new Set(
      texto
        .split(/[\s,]+/)
        .map((t) => t.replace(/^#/, '').trim())
        .filter(Boolean),
    ),
  ];
}

/** ISO → valor do input datetime-local (sem timezone, minutos). */
function isoParaInput(iso?: string | null): string {
  if (!iso) return '';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '';
  const off = d.getTimezoneOffset();
  return new Date(d.getTime() - off * 60_000).toISOString().slice(0, 16);
}

export default function LinkedInScreen() {
  const [aba, setAba] = useState<LinkedinStatus | 'todos'>('todos');
  const [contaFiltro, setContaFiltro] = useState<LinkedinConta | 'todas'>('todas');
  const [busca, setBusca] = useState('');
  const [view, setView] = useState<'lista' | 'calendario'>('lista');
  const { posts, loading, refetch } = useLinkedinPosts(
    aba === 'todos' ? undefined : aba,
    contaFiltro === 'todas' ? undefined : contaFiltro,
  );
  const acoes = useLinkedinActions();

  const [aberto, setAberto] = useState(false);
  const [editId, setEditId] = useState<string | null>(null);
  const [form, setForm] = useState<FormState>(FORM_VAZIO);
  const [copiado, setCopiado] = useState(false);
  // Post salvo (pra mídia/imagens, que vivem no servidor). Null em "novo".
  const [postAtual, setPostAtual] = useState<LinkedinPost | null>(null);
  const [previewFeed, setPreviewFeed] = useState(true);
  const [midiaLoading, setMidiaLoading] = useState(false);

  // Brief do "Escrever com IA" (a conta/formato vêm dos selects do form).
  const [briefTema, setBriefTema] = useState('');
  const [briefPublico, setBriefPublico] = useState('');
  const [briefAngulo, setBriefAngulo] = useState('');
  const [gerando, setGerando] = useState(false);
  const [erroIA, setErroIA] = useState<string | null>(null);

  // Coordenador (L2): gerar a fila de rascunhos autonomamente.
  const [filaAberta, setFilaAberta] = useState(false);
  const [filaFonte, setFilaFonte] = useState<'projeto' | 'tendencia'>('tendencia');
  const [filaConta, setFilaConta] = useState<LinkedinConta>('reative');
  const [filaQtd, setFilaQtd] = useState(3);
  const [filaPublico, setFilaPublico] = useState('');
  const [filaGerando, setFilaGerando] = useState(false);
  const [filaMsg, setFilaMsg] = useState<string | null>(null);

  const filtrados = useMemo(() => {
    const q = busca.trim().toLowerCase();
    if (!q) return posts;
    return posts.filter((p) =>
      [p.titulo, p.hook, p.body].some((c) => (c || '').toLowerCase().includes(q)),
    );
  }, [posts, busca]);

  function limparBrief() {
    setBriefTema('');
    setBriefPublico('');
    setBriefAngulo('');
    setErroIA(null);
  }

  function abrirNovo() {
    setEditId(null);
    setPostAtual(null);
    setForm({
      ...FORM_VAZIO,
      conta: contaFiltro === 'todas' ? 'reative' : contaFiltro,
    });
    setCopiado(false);
    limparBrief();
    setAberto(true);
  }

  function abrirEdicao(p: LinkedinPost) {
    setEditId(p.id);
    setPostAtual(p);
    setForm({
      titulo: p.titulo ?? '',
      conta: p.conta,
      formato: p.formato,
      hook: p.hook ?? '',
      body: p.body ?? '',
      cta: p.cta ?? '',
      hashtagsText: (p.hashtags ?? []).join(' '),
      notas: p.notas ?? '',
      scheduled_for: p.scheduled_for ?? null,
    });
    setCopiado(false);
    limparBrief();
    setAberto(true);
  }

  function set<K extends keyof FormState>(campo: K, valor: FormState[K]) {
    setForm((f) => ({ ...f, [campo]: valor }));
  }

  async function gerarComIA() {
    if (!briefTema.trim()) {
      setErroIA('Informe o tema pra IA escrever.');
      return;
    }
    setGerando(true);
    setErroIA(null);
    const r = await acoes.redigir({
      tema: briefTema.trim(),
      conta: form.conta ?? 'reative',
      formato: form.formato ?? 'post',
      publico: briefPublico || null,
      angulo: briefAngulo || null,
    });
    setGerando(false);
    if (r) {
      setForm((f) => ({
        ...f,
        titulo: f.titulo || r.titulo || briefTema.trim(),
        hook: r.hook,
        body: r.body,
        cta: r.cta ?? '',
        hashtagsText: (r.hashtags ?? []).join(' '),
      }));
    } else {
      setErroIA(acoes.error?.message ?? 'Não consegui gerar. Tente de novo.');
    }
  }

  async function salvar() {
    const payload: LinkedinPostCreate = {
      titulo: form.titulo || null,
      conta: form.conta,
      formato: form.formato,
      hook: form.hook || null,
      body: form.body || null,
      cta: form.cta || null,
      hashtags: parseHashtags(form.hashtagsText),
      notas: form.notas || null,
      scheduled_for: form.scheduled_for || null,
    };
    const r = editId
      ? await acoes.atualizar(editId, payload)
      : await acoes.criar(payload);
    if (r) {
      setAberto(false);
      refetch();
    }
  }

  async function gerarFila() {
    setFilaGerando(true);
    setFilaMsg(null);
    const r = await acoes.gerar({
      fonte: filaFonte,
      quantidade: filaQtd,
      conta: filaConta,
      publico: filaPublico || null,
    });
    setFilaGerando(false);
    if (r) {
      setFilaMsg(`✓ ${r.length} rascunho(s) gerado(s) na fila.`);
      refetch();
    } else {
      setFilaMsg(acoes.error?.message ?? 'Não consegui gerar. Tente de novo.');
    }
  }

  async function sugerirMidia() {
    if (!editId) return;
    setMidiaLoading(true);
    const r = await acoes.sugerirMidia(editId);
    setMidiaLoading(false);
    if (r) {
      setPostAtual(r);
      refetch();
    }
  }

  async function gerarImagem() {
    if (!editId) return;
    setMidiaLoading(true);
    const r = await acoes.gerarImagem(editId, {
      prompt: postAtual?.midia?.prompt_imagem ?? null,
      alt: postAtual?.midia?.alt ?? null,
      aspect_ratio: postAtual?.midia?.aspect_ratio ?? '1:1',
    });
    setMidiaLoading(false);
    if (r) {
      setPostAtual(r);
      refetch();
    }
  }

  async function mudarStatus(id: string, status: LinkedinStatus) {
    const r = await acoes.mudarStatus(id, status);
    if (r) refetch();
  }

  async function remover(id: string) {
    if (!confirm('Apagar este post? Não dá pra desfazer.')) return;
    const r = await acoes.remover(id);
    if (r !== null) {
      if (editId === id) setAberto(false);
      refetch();
    }
  }

  async function copiar() {
    const txt = textoFinal({
      hook: form.hook,
      body: form.body,
      cta: form.cta,
      hashtags: parseHashtags(form.hashtagsText),
    });
    try {
      await navigator.clipboard.writeText(txt);
      setCopiado(true);
      setTimeout(() => setCopiado(false), 2000);
    } catch {
      /* clipboard pode falhar sem https/permissão — ignora */
    }
  }

  const previewChars = textoFinal({
    hook: form.hook,
    body: form.body,
    cta: form.cta,
    hashtags: parseHashtags(form.hashtagsText),
  }).length;

  return (
    <div className="max-w-[1200px] mx-auto">
      <header className="mb-7">
        <div className="eyebrow mb-3">Reative Systems · Presença</div>
        <h1 className="font-display font-semibold text-[38px] leading-[1.05] tracking-tighter text-ink m-0 mb-2.5">
          LinkedIn
        </h1>
        <p className="text-[15px] text-ink-soft max-w-[60ch] leading-relaxed m-0">
          Rascunhos prontos de post pra <strong>Página da Reative</strong> e pro
          seu <strong>perfil pessoal</strong>, a partir do blog, projetos e
          tendências. Você revisa, copia e publica — o agente não posta sozinho.
        </p>
      </header>

      {/* Filtros */}
      <div className="flex flex-wrap items-center gap-3 mb-5">
        <div className="flex gap-1 border-b border-line">
          {STATUS_TABS.map((t) => (
            <button
              key={t.key}
              type="button"
              onClick={() => setAba(t.key)}
              className={`px-3.5 py-2 text-[13.5px] font-medium -mb-px border-b-2 transition-colors ${
                aba === t.key
                  ? 'border-brand text-brand'
                  : 'border-transparent text-ink-mute hover:text-ink'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
        <div className="flex gap-1 ml-auto">
          {(['todas', 'reative', 'pessoal'] as const).map((c) => (
            <button
              key={c}
              type="button"
              onClick={() => setContaFiltro(c)}
              className={`px-3 py-1.5 text-[12.5px] rounded-md border transition-colors ${
                contaFiltro === c
                  ? 'border-brand bg-brand-soft text-brand'
                  : 'border-line text-ink-mute hover:text-ink'
              }`}
            >
              {c === 'todas' ? 'Todas as contas' : CONTA_LABEL[c]}
            </button>
          ))}
        </div>
      </div>

      <div className="flex items-center gap-3 mb-5">
        <input
          value={busca}
          onChange={(e) => setBusca(e.target.value)}
          placeholder="Buscar por título ou texto…"
          className="flex-1 px-3.5 py-2 rounded-md border border-line bg-surface text-[14px] text-ink placeholder:text-ink-faint focus:outline-none focus:border-brand"
        />
        <button
          type="button"
          onClick={() => {
            setFilaMsg(null);
            setFilaConta(contaFiltro === 'todas' ? 'reative' : contaFiltro);
            setFilaAberta(true);
          }}
          className="px-4 py-2 rounded-md border border-brand text-brand text-[13.5px] font-medium hover:bg-brand-soft shrink-0"
        >
          ✨ Gerar com IA
        </button>
        <button
          type="button"
          onClick={abrirNovo}
          className="px-4 py-2 rounded-md bg-brand text-white text-[13.5px] font-medium hover:opacity-90 shrink-0"
        >
          + Novo post
        </button>
      </div>

      {/* Alternância Lista / Calendário */}
      <div className="flex gap-1 mb-4">
        {(['lista', 'calendario'] as const).map((v) => (
          <button
            key={v}
            type="button"
            onClick={() => setView(v)}
            className={`px-3 py-1.5 text-[12.5px] rounded-md border transition-colors ${
              view === v
                ? 'border-brand bg-brand-soft text-brand'
                : 'border-line text-ink-mute hover:text-ink'
            }`}
          >
            {v === 'lista' ? 'Lista' : '📅 Calendário'}
          </button>
        ))}
      </div>

      {/* Lista / Calendário */}
      {loading ? (
        <div className="text-ink-mute py-12 text-center">Carregando…</div>
      ) : filtrados.length === 0 ? (
        <div className="text-ink-mute py-12 text-center">
          Nenhum post ainda. Crie o primeiro ou gere com IA.
        </div>
      ) : view === 'lista' ? (
        <div className="grid gap-3">
          {filtrados.map((p) => (
            <PostCard key={p.id} p={p} onClick={() => abrirEdicao(p)} />
          ))}
        </div>
      ) : (
        <div className="flex flex-col gap-6">
          {agruparPorData(filtrados).map(([rotulo, itens]) => (
            <div key={rotulo}>
              <div className="text-[12.5px] font-semibold text-ink-mute uppercase tracking-wide mb-2 sticky top-0 bg-bg py-1">
                {rotulo}
              </div>
              <div className="grid gap-3">
                {itens.map((p) => (
                  <PostCard key={p.id} p={p} onClick={() => abrirEdicao(p)} />
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Drawer: gerar a fila autonomamente (L2) */}
      <SidePanel
        open={filaAberta}
        onClose={() => setFilaAberta(false)}
        title="✨ Gerar rascunhos com IA"
        width="max-w-lg"
      >
        <div className="flex flex-col gap-4">
          <p className="text-[13.5px] text-ink-soft leading-relaxed m-0">
            O agente escreve posts prontos e coloca na fila como{' '}
            <strong>rascunho</strong> — você revisa, copia e publica. Não posta
            sozinho.
          </p>

          <div className="grid grid-cols-2 gap-3">
            <Campo label="Conta">
              <select
                value={filaConta}
                onChange={(e) => setFilaConta(e.target.value as LinkedinConta)}
                className="input"
              >
                <option value="reative">Página Reative</option>
                <option value="pessoal">Perfil pessoal</option>
              </select>
            </Campo>
            <Campo label="Quantidade">
              <input
                type="number"
                min={1}
                max={8}
                value={filaQtd}
                onChange={(e) =>
                  setFilaQtd(Math.max(1, Math.min(8, Number(e.target.value) || 1)))
                }
                className="input"
              />
            </Campo>
          </div>

          <Campo label="Fonte do conteúdo">
            <div className="flex gap-2">
              {(['tendencia', 'projeto'] as const).map((f) => (
                <button
                  key={f}
                  type="button"
                  onClick={() => setFilaFonte(f)}
                  className={`flex-1 px-3 py-2 rounded-md border text-[13px] transition-colors ${
                    filaFonte === f
                      ? 'border-brand bg-brand-soft text-brand'
                      : 'border-line text-ink-mute hover:text-ink'
                  }`}
                >
                  {f === 'tendencia' ? 'Tendências do setor' : 'Meus projetos'}
                </button>
              ))}
            </div>
          </Campo>

          <Campo label="Público que quer atrair (opcional)">
            <input
              value={filaPublico}
              onChange={(e) => setFilaPublico(e.target.value)}
              className="input"
              placeholder="recrutador / cliente"
            />
          </Campo>

          <div className="flex items-center gap-3 border-t border-line pt-4">
            <button
              type="button"
              onClick={gerarFila}
              disabled={filaGerando}
              className="px-4 py-2 rounded-md bg-brand text-white text-[13.5px] font-medium hover:opacity-90 disabled:opacity-50"
            >
              {filaGerando ? 'Gerando… (pode levar 1-2 min)' : 'Gerar rascunhos'}
            </button>
            {filaMsg && (
              <span
                className={`text-[13px] ${
                  filaMsg.startsWith('✓') ? 'text-green-700' : 'text-red-600'
                }`}
              >
                {filaMsg}
              </span>
            )}
          </div>
        </div>
      </SidePanel>

      {/* Drawer de criar/editar */}
      <SidePanel
        open={aberto}
        onClose={() => setAberto(false)}
        title={editId ? 'Editar post' : 'Novo post'}
        acoes={
          <button
            type="button"
            onClick={salvar}
            disabled={acoes.loading}
            className="px-3.5 py-1.5 rounded-md bg-brand text-white text-[13px] font-medium hover:opacity-90 disabled:opacity-50"
          >
            {acoes.loading ? 'Salvando…' : 'Salvar'}
          </button>
        }
      >
        <div className="flex flex-col gap-4">
          <div className="grid grid-cols-2 gap-3">
            <Campo label="Conta">
              <select
                value={form.conta ?? 'reative'}
                onChange={(e) => set('conta', e.target.value as LinkedinConta)}
                className="input"
              >
                <option value="reative">Página Reative</option>
                <option value="pessoal">Perfil pessoal</option>
              </select>
            </Campo>
            <Campo label="Formato">
              <select
                value={form.formato ?? 'post'}
                onChange={(e) => set('formato', e.target.value as LinkedinFormato)}
                className="input"
              >
                {FORMATOS.map((f) => (
                  <option key={f} value={f}>
                    {f}
                  </option>
                ))}
              </select>
            </Campo>
          </div>

          {/* Escrever com IA */}
          <div className="rounded-lg border border-brand/30 bg-brand-soft/40 p-3.5 flex flex-col gap-2.5">
            <div className="flex items-center gap-2">
              <span className="text-[13px] font-semibold text-brand">
                ✍️ Escrever com IA
              </span>
              <span className="text-[11px] text-ink-mute">
                usa a conta/formato selecionados acima
              </span>
            </div>
            <input
              value={briefTema}
              onChange={(e) => setBriefTema(e.target.value)}
              className="input"
              placeholder="Tema (ex.: como automatizei minhas finanças com um bot)"
            />
            <div className="grid grid-cols-2 gap-2">
              <input
                value={briefPublico}
                onChange={(e) => setBriefPublico(e.target.value)}
                className="input"
                placeholder="Público (recrutador / cliente)"
              />
              <input
                value={briefAngulo}
                onChange={(e) => setBriefAngulo(e.target.value)}
                className="input"
                placeholder="Ângulo/pontos (opcional)"
              />
            </div>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={gerarComIA}
                disabled={gerando}
                className="px-3.5 py-1.5 rounded-md bg-brand text-white text-[13px] font-medium hover:opacity-90 disabled:opacity-50"
              >
                {gerando ? 'Gerando…' : 'Gerar rascunho'}
              </button>
              {erroIA && <span className="text-[12px] text-red-600">{erroIA}</span>}
              <span className="text-[11px] text-ink-mute ml-auto">
                preenche os campos abaixo — você revisa antes de salvar
              </span>
            </div>
          </div>

          <Campo label="Título interno (organização — não vai pro post)">
            <input
              value={form.titulo ?? ''}
              onChange={(e) => set('titulo', e.target.value)}
              className="input"
              placeholder="Ex.: Case do organizador financeiro"
            />
          </Campo>

          <Campo label="Hook (1ª linha — o que prende)">
            <textarea
              value={form.hook ?? ''}
              onChange={(e) => set('hook', e.target.value)}
              className="input min-h-[60px]"
              placeholder="A primeira linha que aparece no feed…"
            />
          </Campo>

          <Campo label="Corpo">
            <textarea
              value={form.body ?? ''}
              onChange={(e) => set('body', e.target.value)}
              className="input min-h-[180px]"
              placeholder="O conteúdo do post, em parágrafos curtos…"
            />
          </Campo>

          <Campo label="CTA (chamada pra ação)">
            <textarea
              value={form.cta ?? ''}
              onChange={(e) => set('cta', e.target.value)}
              className="input min-h-[50px]"
              placeholder="Ex.: Bora trocar uma ideia? Comenta aí 👇"
            />
          </Campo>

          <Campo label="Hashtags (separe por espaço ou vírgula)">
            <input
              value={form.hashtagsText ?? ''}
              onChange={(e) => set('hashtagsText', e.target.value)}
              className="input"
              placeholder="ia python fastapi"
            />
          </Campo>

          <Campo label="Agendar no calendário (opcional)">
            <input
              type="datetime-local"
              value={isoParaInput(form.scheduled_for)}
              onChange={(e) =>
                set(
                  'scheduled_for',
                  e.target.value ? new Date(e.target.value).toISOString() : null,
                )
              }
              className="input"
            />
          </Campo>

          <Campo label="Notas (suas — não vão pro post)">
            <textarea
              value={form.notas ?? ''}
              onChange={(e) => set('notas', e.target.value)}
              className="input min-h-[50px]"
            />
          </Campo>

          {/* Direção de arte (L5) — precisa do post salvo (mídia/imagens) */}
          {editId ? (
            <DirecaoArte
              post={postAtual}
              loading={midiaLoading}
              onSugerir={sugerirMidia}
              onGerarImagem={gerarImagem}
            />
          ) : (
            <div className="border-t border-line pt-4 text-[12.5px] text-ink-mute">
              🎨 Salve o post pra pedir a <strong>direção de arte</strong> (mídia
              ideal + gerar imagem por IA).
            </div>
          )}

          {/* Preview / copiar */}
          <div className="border-t border-line pt-4">
            <div className="flex items-center justify-between mb-2 gap-2">
              <span className="text-[12px] font-medium text-ink-mute uppercase tracking-wide">
                Preview ({previewChars} car.)
              </span>
              <div className="flex items-center gap-2">
                <div className="flex rounded-md border border-line overflow-hidden text-[12px]">
                  <button
                    type="button"
                    onClick={() => setPreviewFeed(true)}
                    className={`px-2.5 py-1 ${previewFeed ? 'bg-brand text-white' : 'text-ink-mute'}`}
                  >
                    Feed
                  </button>
                  <button
                    type="button"
                    onClick={() => setPreviewFeed(false)}
                    className={`px-2.5 py-1 ${!previewFeed ? 'bg-brand text-white' : 'text-ink-mute'}`}
                  >
                    Texto
                  </button>
                </div>
                <button
                  type="button"
                  onClick={copiar}
                  className="px-3 py-1.5 rounded-md border border-line text-[12.5px] text-ink hover:border-brand"
                >
                  {copiado ? '✓ Copiado' : 'Copiar'}
                </button>
              </div>
            </div>
            {previewFeed ? (
              <FeedPreview
                conta={(form.conta as LinkedinConta) ?? 'reative'}
                texto={textoFinal({
                  hook: form.hook,
                  body: form.body,
                  cta: form.cta,
                  hashtags: parseHashtags(form.hashtagsText),
                })}
                imagem={postAtual?.imagens?.[0]?.url ?? null}
              />
            ) : (
              <pre className="whitespace-pre-wrap text-[13.5px] text-ink-soft bg-bg-alt rounded-md p-3 font-sans">
                {textoFinal({
                  hook: form.hook,
                  body: form.body,
                  cta: form.cta,
                  hashtags: parseHashtags(form.hashtagsText),
                }) || '(vazio)'}
              </pre>
            )}
          </div>

          {/* Ações de status / remover (só ao editar) */}
          {editId && (
            <div className="flex flex-wrap items-center gap-2 border-t border-line pt-4">
              <button
                type="button"
                onClick={() => mudarStatus(editId, 'aprovado')}
                className="px-3 py-1.5 rounded-md border border-line text-[12.5px] hover:border-brand"
              >
                Aprovar
              </button>
              <button
                type="button"
                onClick={() => mudarStatus(editId, 'publicado')}
                className="px-3 py-1.5 rounded-md border border-line text-[12.5px] hover:border-brand"
              >
                Marcar publicado
              </button>
              <button
                type="button"
                onClick={() => mudarStatus(editId, 'arquivado')}
                className="px-3 py-1.5 rounded-md border border-line text-[12.5px] hover:border-brand"
              >
                Arquivar
              </button>
              <button
                type="button"
                onClick={() => remover(editId)}
                className="px-3 py-1.5 rounded-md border border-red-200 text-red-600 text-[12.5px] hover:bg-red-50 ml-auto"
              >
                Apagar
              </button>
            </div>
          )}

          {acoes.error && (
            <div className="text-[13px] text-red-600">{acoes.error.message}</div>
          )}
        </div>
      </SidePanel>
    </div>
  );
}

/** Agrupa por dia de `scheduled_for` (asc); sem data vai pro fim. */
function agruparPorData(posts: LinkedinPost[]): [string, LinkedinPost[]][] {
  const grupos = new Map<string, LinkedinPost[]>();
  const SEM = 'Sem agendamento';
  for (const p of posts) {
    const chave = p.scheduled_for
      ? new Date(p.scheduled_for).toLocaleDateString('pt-BR', {
          weekday: 'long',
          day: '2-digit',
          month: 'long',
        })
      : SEM;
    (grupos.get(chave) ?? grupos.set(chave, []).get(chave)!).push(p);
  }
  return [...grupos.entries()].sort(([a, ia], [b, ib]) => {
    if (a === SEM) return 1;
    if (b === SEM) return -1;
    const da = ia[0]?.scheduled_for ?? '';
    const db = ib[0]?.scheduled_for ?? '';
    return da.localeCompare(db);
  });
}

function PostCard({ p, onClick }: { p: LinkedinPost; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="card text-left p-4 hover:border-brand transition-colors"
    >
      <div className="flex items-start justify-between gap-3 mb-1.5">
        <div className="flex items-center gap-2 flex-wrap">
          <span
            className={`text-[11px] font-medium px-2 py-0.5 rounded-full ${CONTA_BADGE[p.conta]}`}
          >
            {CONTA_LABEL[p.conta]}
          </span>
          <span
            className={`text-[11px] font-medium px-2 py-0.5 rounded-full ${STATUS_BADGE[p.status]}`}
          >
            {p.status}
          </span>
          <span className="text-[11px] text-ink-faint uppercase tracking-wide">
            {p.formato} · {p.fonte}
          </span>
        </div>
        {typeof p.char_count === 'number' && (
          <span className="text-[11px] text-ink-faint shrink-0">
            {p.char_count} car.
          </span>
        )}
      </div>
      <div className="font-medium text-ink text-[15px] mb-0.5 truncate">
        {p.titulo || p.hook || '(sem título)'}
      </div>
      {p.hook && p.titulo && (
        <div className="text-[13px] text-ink-soft line-clamp-2">{p.hook}</div>
      )}
      {p.scheduled_for && (
        <div className="text-[11.5px] text-ink-mute mt-1.5">
          📅 {new Date(p.scheduled_for).toLocaleString('pt-BR')}
        </div>
      )}
    </button>
  );
}

const MIDIA_LABEL: Record<string, string> = {
  imagem_ia: '🖼️ Imagem por IA',
  foto: '📷 Foto',
  carrossel: '🎠 Carrossel',
  video_reel: '🎬 Vídeo / Reel',
  screenshot: '🖥️ Screenshot',
  grafico: '📊 Gráfico',
  sem_midia: '📝 Sem mídia (texto puro)',
};

function DirecaoArte({
  post,
  loading,
  onSugerir,
  onGerarImagem,
}: {
  post: LinkedinPost | null;
  loading: boolean;
  onSugerir: () => void;
  onGerarImagem: () => void;
}) {
  const midia = post?.midia ?? null;
  const imagens = post?.imagens ?? [];
  const podeGerarImg =
    !!midia && (midia.recomendacao === 'imagem_ia' || !!midia.prompt_imagem);

  return (
    <div className="border-t border-line pt-4 flex flex-col gap-3">
      <div className="flex items-center justify-between gap-2">
        <span className="text-[13px] font-semibold text-ink">
          🎨 Direção de arte
        </span>
        <button
          type="button"
          onClick={onSugerir}
          disabled={loading}
          className="px-3 py-1.5 rounded-md border border-brand text-brand text-[12.5px] font-medium hover:bg-brand-soft disabled:opacity-50"
        >
          {loading ? 'Pensando…' : midia ? 'Sugerir de novo' : 'Sugerir mídia (IA)'}
        </button>
      </div>

      {!midia && (
        <p className="text-[12.5px] text-ink-mute m-0">
          O agente recomenda a mídia ideal pro post (tipo + roteiro passo a passo)
          e pode gerar a imagem por IA.
        </p>
      )}

      {midia && (
        <div className="rounded-lg bg-bg-alt p-3.5 flex flex-col gap-2.5">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-[12.5px] font-semibold px-2 py-0.5 rounded-full bg-brand-soft text-brand">
              {MIDIA_LABEL[midia.recomendacao] ?? midia.recomendacao}
            </span>
            <span className="text-[11px] text-ink-mute">
              proporção {midia.aspect_ratio}
            </span>
          </div>
          {midia.justificativa && (
            <p className="text-[13px] text-ink-soft m-0 leading-relaxed">
              {midia.justificativa}
            </p>
          )}
          {midia.passos.length > 0 && (
            <div>
              <div className="text-[11.5px] font-semibold text-ink-mute uppercase tracking-wide mb-1">
                Passo a passo
              </div>
              <ol className="list-decimal ml-4 flex flex-col gap-1">
                {midia.passos.map((s, i) => (
                  <li key={i} className="text-[13px] text-ink-soft leading-snug">
                    {s}
                  </li>
                ))}
              </ol>
            </div>
          )}
          {midia.dicas.length > 0 && (
            <div>
              <div className="text-[11.5px] font-semibold text-ink-mute uppercase tracking-wide mb-1">
                Dicas
              </div>
              <ul className="list-disc ml-4 flex flex-col gap-0.5">
                {midia.dicas.map((d, i) => (
                  <li key={i} className="text-[12.5px] text-ink-mute leading-snug">
                    {d}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {podeGerarImg && (
            <div className="flex items-center gap-2 flex-wrap">
              <button
                type="button"
                onClick={onGerarImagem}
                disabled={loading}
                className="px-3 py-1.5 rounded-md bg-brand text-white text-[12.5px] font-medium hover:opacity-90 disabled:opacity-50"
              >
                {loading ? 'Gerando imagem…' : '🖼️ Gerar imagem com IA'}
              </button>
              {midia.prompt_imagem && (
                <span className="text-[11px] text-ink-faint italic truncate max-w-[60%]">
                  {midia.prompt_imagem}
                </span>
              )}
            </div>
          )}
        </div>
      )}

      {imagens.length > 0 && (
        <div className="flex gap-2 flex-wrap">
          {imagens.map((img, i) => (
            <a
              key={i}
              href={img.url}
              target="_blank"
              rel="noreferrer"
              className="block w-24 h-24 rounded-md overflow-hidden border border-line hover:border-brand"
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={img.url}
                alt={img.alt ?? 'imagem do post'}
                className="w-full h-full object-cover"
              />
            </a>
          ))}
        </div>
      )}
    </div>
  );
}

function FeedPreview({
  conta,
  texto,
  imagem,
}: {
  conta: LinkedinConta;
  texto: string;
  imagem: string | null;
}) {
  const nome = conta === 'pessoal' ? 'Pablo Dias' : 'Reative Systems';
  const sub =
    conta === 'pessoal'
      ? 'Desenvolvedor Full-Stack'
      : 'Automação e sistemas sob medida';
  const inicial = nome.charAt(0);

  return (
    <div className="rounded-lg border border-line bg-surface max-w-md mx-auto shadow-sm">
      <div className="flex items-center gap-2.5 p-3">
        <div
          className={`w-11 h-11 rounded-full flex items-center justify-center text-white font-semibold ${
            conta === 'pessoal' ? 'bg-violet-500' : 'bg-brand'
          }`}
        >
          {inicial}
        </div>
        <div className="leading-tight">
          <div className="text-[14px] font-semibold text-ink">{nome}</div>
          <div className="text-[11.5px] text-ink-mute">{sub}</div>
          <div className="text-[11px] text-ink-faint">Agora · 🌐</div>
        </div>
      </div>
      <div className="px-3 pb-2 text-[13.5px] text-ink whitespace-pre-wrap leading-relaxed">
        {texto || '(escreva o post pra ver o preview)'}
      </div>
      {imagem && (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={imagem} alt="mídia do post" className="w-full object-cover" />
      )}
      <div className="flex items-center justify-around border-t border-line px-2 py-1.5 text-[12.5px] text-ink-mute">
        <span>👍 Gostei</span>
        <span>💬 Comentar</span>
        <span>🔁 Compartilhar</span>
        <span>📤 Enviar</span>
      </div>
    </div>
  );
}

function Campo({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <label className="flex flex-col gap-1.5">
      <span className="text-[12.5px] font-medium text-ink-mute">{label}</span>
      {children}
    </label>
  );
}

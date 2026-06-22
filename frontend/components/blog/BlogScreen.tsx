import { useMemo, useState } from 'react';

import { Modal } from '@/components/shared/Modal';
import { PostPreview } from '@/components/blog/PostPreview';
import { useBlogActions, useBlogPautas, useBlogPosts } from '@/hooks/useBlog';
import type {
  BlogBriefRequest,
  BlogPauta,
  BlogPostAdmin,
  BlogPostCreate,
  BlogStatus,
  CapaSugestao,
  ChecklistSeo,
  ImagemConteudoSugestao,
} from '@/lib/types';

const STATUS_TABS: { key: BlogStatus | 'todos'; label: string }[] = [
  { key: 'todos', label: 'Todos' },
  { key: 'rascunho', label: 'Rascunhos' },
  { key: 'publicado', label: 'Publicados' },
  { key: 'arquivado', label: 'Arquivados' },
];

const STATUS_BADGE: Record<BlogStatus, string> = {
  rascunho: 'bg-bg-alt text-ink-mute',
  aprovado: 'bg-blue-100 text-blue-700',
  publicado: 'bg-green-100 text-green-700',
  arquivado: 'bg-amber-100 text-amber-700',
};

type FormState = BlogPostCreate & { tagsText?: string };

const FORM_VAZIO: FormState = {
  title: '',
  slug: '',
  category: '',
  excerpt: '',
  cover_url: '',
  tagsText: '',
  body_md: '',
  meta_description: '',
  keyword_alvo: '',
  og_title: '',
  og_description: '',
  noindex: false,
};

export default function BlogScreen() {
  const [view, setView] = useState<'posts' | 'pautas'>('posts');
  const [aba, setAba] = useState<BlogStatus | 'todos'>('todos');
  const [busca, setBusca] = useState('');
  const [catFiltro, setCatFiltro] = useState('');
  const { posts, loading, refetch } = useBlogPosts(
    aba === 'todos' ? undefined : aba,
  );
  const acoes = useBlogActions();

  // Categorias presentes (pro filtro) + lista filtrada por busca/categoria.
  const categorias = useMemo(
    () => [...new Set(posts.map((p) => p.category).filter(Boolean))] as string[],
    [posts],
  );
  const postsFiltrados = useMemo(() => {
    const termo = busca.trim().toLowerCase();
    return posts.filter((p) => {
      if (catFiltro && p.category !== catFiltro) return false;
      if (!termo) return true;
      return `${p.title} ${p.keyword_alvo ?? ''} ${p.slug}`
        .toLowerCase()
        .includes(termo);
    });
  }, [posts, busca, catFiltro]);

  const [editando, setEditando] = useState<BlogPostAdmin | null>(null);
  const [form, setForm] = useState<FormState | null>(null);

  function abrirNovo() {
    setEditando(null);
    setForm({ ...FORM_VAZIO });
  }

  // 1-clique (coordenador B4): a IA escreve o artigo completo e salva como
  // rascunho; abrimos o post gerado pra revisão (a pauta é marcada 'escrita' no
  // backend).
  async function escreverDaPauta(p: BlogPauta) {
    const post = await acoes.escreverPauta(p.id);
    if (post) {
      setView('posts');
      abrirEdicao(post);
      refetch();
    }
  }

  function abrirEdicao(p: BlogPostAdmin) {
    setEditando(p);
    setForm({
      title: p.title,
      slug: p.slug,
      category: p.category ?? '',
      excerpt: p.excerpt ?? '',
      cover_url: p.cover_url ?? '',
      tagsText: (p.tags ?? []).join(', '),
      body_md: p.body_md ?? '',
      meta_description: p.meta_description ?? '',
      keyword_alvo: p.keyword_alvo ?? '',
      og_title: p.og_title ?? '',
      og_description: p.og_description ?? '',
      noindex: p.noindex,
      published_at: p.published_at ?? undefined,
    });
  }

  function fechar() {
    setForm(null);
    setEditando(null);
  }

  async function salvar() {
    if (!form || !form.title.trim()) return;
    const { tagsText, ...rest } = form;
    const body: BlogPostCreate = {
      ...rest,
      tags: tagsText
        ? tagsText.split(',').map((t) => t.trim()).filter(Boolean)
        : [],
    };
    const salvo = editando
      ? await acoes.atualizar(editando.id, body)
      : await acoes.criar(body);
    if (salvo) {
      fechar();
      refetch();
    }
  }

  async function mudarStatus(p: BlogPostAdmin, status: BlogStatus) {
    if (await acoes.mudarStatus(p.id, status)) refetch();
  }

  async function apagar(p: BlogPostAdmin) {
    if (!confirm(`Apagar "${p.title}"? Não dá pra desfazer.`)) return;
    if (await acoes.remover(p.id)) refetch();
  }

  return (
    <div className="max-w-[1100px] mx-auto pb-16">
      <header className="mb-7">
        <div className="eyebrow mb-3">Reative Systems · Conteúdo</div>
        <h1 className="font-display font-semibold text-[38px] leading-[1.05] tracking-tighter text-ink m-0 mb-2.5">
          Blog
        </h1>
        <p className="text-[15px] text-ink-soft max-w-[62ch] leading-relaxed m-0">
          O cérebro de conteúdo do site. Escreva em Markdown, otimize pra SEO e
          publique — o site <strong>reativesystems.com.br</strong> consome por
          API. Rascunho fica fora do ar até você aprovar.
        </p>
      </header>

      <div className="flex gap-1.5 mb-5 border-b border-line">
        {(['posts', 'pautas'] as const).map((v) => (
          <button
            key={v}
            type="button"
            onClick={() => setView(v)}
            className={`text-[14px] px-3 py-2 -mb-px border-b-2 transition-colors ${
              view === v
                ? 'border-brand text-ink font-medium'
                : 'border-transparent text-ink-mute hover:text-ink'
            }`}
          >
            {v === 'posts' ? 'Posts' : 'Pautas'}
          </button>
        ))}
      </div>

      {acoes.error && (
        <div className="mb-4 text-[13px] text-red-700 bg-red-50 border border-red-200 rounded p-3">
          {acoes.error.message}
        </div>
      )}

      {view === 'pautas' ? (
        <PautasView acoes={acoes} onEscrever={escreverDaPauta} />
      ) : (
        <>
          <div className="flex items-center justify-between mb-5 gap-3 flex-wrap">
            <div className="flex gap-1.5">
              {STATUS_TABS.map((t) => (
                <button
                  key={t.key}
                  type="button"
                  onClick={() => setAba(t.key)}
                  className={`text-[13px] px-3 py-1.5 rounded-md transition-colors ${
                    aba === t.key
                      ? 'bg-ink text-white'
                      : 'bg-bg-alt text-ink-soft hover:text-ink'
                  }`}
                >
                  {t.label}
                </button>
              ))}
            </div>
            <button type="button" onClick={abrirNovo} className="btn btn-primary">
              + Novo post
            </button>
          </div>

          <div className="flex items-center gap-2 mb-4 flex-wrap">
            <input
              className="input max-w-xs"
              placeholder="Buscar por título, keyword ou slug…"
              value={busca}
              onChange={(e) => setBusca(e.target.value)}
            />
            {categorias.length > 0 && (
              <select
                className="input max-w-[200px]"
                value={catFiltro}
                onChange={(e) => setCatFiltro(e.target.value)}
              >
                <option value="">Todas as categorias</option>
                {categorias.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            )}
            {(busca || catFiltro) && (
              <span className="text-[12px] text-ink-mute">
                {postsFiltrados.length} de {posts.length}
              </span>
            )}
          </div>

          {loading ? (
            <p className="text-ink-mute text-sm">Carregando…</p>
          ) : posts.length === 0 ? (
            <p className="text-ink-mute text-sm">
              Nenhum post aqui ainda. Clique em <strong>Novo post</strong> pra
              começar.
            </p>
          ) : postsFiltrados.length === 0 ? (
            <p className="text-ink-mute text-sm">
              Nenhum post bate com o filtro. Limpe a busca ou a categoria.
            </p>
          ) : (
            <div className="flex flex-col gap-2">
              {postsFiltrados.map((p) => (
                <PostRow
                  key={p.id}
                  post={p}
                  onEdit={() => abrirEdicao(p)}
                  onStatus={(s) => mudarStatus(p, s)}
                  onDelete={() => apagar(p)}
                />
              ))}
            </div>
          )}
        </>
      )}

      {form && (
        <Editor
          form={form}
          setForm={setForm}
          editando={editando}
          acoes={acoes}
          onClose={fechar}
          onSave={salvar}
          onPostAtualizado={(p) => {
            setEditando(p);
            setForm((f) =>
              f
                ? { ...f, cover_url: p.cover_url ?? '', body_md: p.body_md ?? f.body_md }
                : f,
            );
          }}
        />
      )}
    </div>
  );
}

function PostRow({
  post,
  onEdit,
  onStatus,
  onDelete,
}: {
  post: BlogPostAdmin;
  onEdit: () => void;
  onStatus: (s: BlogStatus) => void;
  onDelete: () => void;
}) {
  return (
    <div className="card p-4 flex items-center gap-4">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span
            className={`text-[10px] uppercase tracking-wide px-1.5 py-0.5 rounded-sm font-mono ${STATUS_BADGE[post.status]}`}
          >
            {post.status}
          </span>
          {post.category && (
            <span className="text-[11px] text-ink-mute">{post.category}</span>
          )}
        </div>
        <h3 className="font-medium text-ink text-[15px] truncate m-0">
          {post.title}
        </h3>
        <div className="text-[12px] text-ink-mute font-mono truncate">
          /{post.slug}
          {post.reading_time ? ` · ${post.reading_time} min` : ''}
        </div>
      </div>
      <div className="flex items-center gap-1.5 shrink-0">
        <button type="button" onClick={onEdit} className="btn btn-ghost text-[13px]">
          Editar
        </button>
        {post.status === 'publicado' ? (
          <button
            type="button"
            onClick={() => onStatus('rascunho')}
            className="btn btn-ghost text-[13px]"
          >
            Despublicar
          </button>
        ) : (
          <button
            type="button"
            onClick={() => onStatus('publicado')}
            className="btn btn-primary text-[13px]"
          >
            Publicar
          </button>
        )}
        <button
          type="button"
          onClick={onDelete}
          className="text-ink-mute hover:text-red-600 text-lg px-1.5"
          aria-label="Apagar"
          title="Apagar"
        >
          ×
        </button>
      </div>
    </div>
  );
}

function Editor({
  form,
  setForm,
  editando,
  acoes,
  onClose,
  onSave,
  onPostAtualizado,
}: {
  form: FormState;
  setForm: (f: FormState) => void;
  editando: BlogPostAdmin | null;
  acoes: ReturnType<typeof useBlogActions>;
  onClose: () => void;
  onSave: () => void;
  onPostAtualizado: (p: BlogPostAdmin) => void;
}) {
  const set = (campo: keyof FormState, valor: unknown) =>
    setForm({ ...form, [campo]: valor });

  const metaLen = (form.meta_description ?? '').length;
  const metaOk = metaLen >= 120 && metaLen <= 160;

  const [briefAberto, setBriefAberto] = useState(false);
  const [gerando, setGerando] = useState(false);
  const [brief, setBrief] = useState<BlogBriefRequest>({ tema: '' });
  const [seo, setSeo] = useState<ChecklistSeo | null>(null);
  const [preview, setPreview] = useState(false);
  const [pendencias, setPendencias] = useState<string[]>([]);

  async function gerar() {
    const tema = brief.tema.trim() || form.title.trim();
    if (!tema) return;
    setGerando(true);
    const r = await acoes.redigir({ ...brief, tema });
    setGerando(false);
    if (r) {
      setForm({
        ...form,
        title: r.title,
        slug: r.slug ?? '',
        excerpt: r.excerpt ?? '',
        category: r.category ?? form.category,
        body_md: r.body_md,
        meta_description: r.meta_description ?? '',
        keyword_alvo: r.keyword_alvo ?? brief.keyword_alvo ?? '',
        og_title: r.og_title ?? '',
        og_description: r.og_description ?? '',
        tagsText: (r.tags ?? []).join(', '),
      });
      setBriefAberto(false);
      setSeo(null);
      setPendencias(r.pendencias ?? []);
    }
  }

  async function checarSeo() {
    const r = await acoes.checklist({
      title: form.title,
      slug: form.slug,
      body_md: form.body_md,
      excerpt: form.excerpt,
      meta_description: form.meta_description,
      keyword_alvo: form.keyword_alvo,
    });
    if (r) setSeo(r);
  }

  return (
    <Modal
      open
      onClose={onClose}
      title={editando ? 'Editar post' : 'Novo post'}
      maxWidth="max-w-3xl"
    >
      <div className="flex flex-col gap-3 max-h-[70vh] overflow-y-auto pr-1">
        <div className="flex items-center justify-between gap-2 -mb-1">
          <button
            type="button"
            onClick={() => setBriefAberto((v) => !v)}
            className="btn btn-ghost text-[13px]"
          >
            ✨ {briefAberto ? 'Fechar gerador' : 'Gerar com IA'}
          </button>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setPreview((v) => !v)}
              className="btn btn-ghost text-[13px]"
            >
              {preview ? '✏️ Editar' : '👁️ Visualizar'}
            </button>
            <button
              type="button"
              onClick={checarSeo}
              disabled={acoes.loading}
              className="btn btn-ghost text-[13px]"
            >
              Checar SEO
            </button>
          </div>
        </div>

        {preview ? (
          <PostPreview
            title={form.title}
            excerpt={form.excerpt}
            coverUrl={form.cover_url}
            bodyMd={form.body_md}
          />
        ) : (
        <>

        {briefAberto && (
          <BriefPanel
            brief={brief}
            setBrief={setBrief}
            gerando={gerando}
            onGerar={gerar}
            fallbackTitulo={form.title}
          />
        )}

        {pendencias.length > 0 && (
          <div className="rounded-md border border-amber-300 bg-amber-50 p-3">
            <div className="flex items-center justify-between gap-2">
              <strong className="text-[13px] text-amber-800">
                ⚠️ Pendências — o post menciona recursos que talvez você não tenha
              </strong>
              <button
                type="button"
                onClick={() => setPendencias([])}
                className="text-amber-700 hover:text-amber-900 text-xs"
              >
                dispensar
              </button>
            </div>
            <ul className="text-[12px] text-amber-800 mt-1 list-disc pl-5">
              {pendencias.map((p, i) => (
                <li key={i}>{p}</li>
              ))}
            </ul>
            <p className="text-[11px] text-amber-700 m-0 mt-1">
              Crie esses materiais/ofertas ou tire a menção do texto antes de publicar.
            </p>
          </div>
        )}

        {seo && <SeoPanel seo={seo} />}

        <Field label="Título">
          <input
            className="input"
            value={form.title}
            onChange={(e) => set('title', e.target.value)}
            placeholder="Título do post (vira o slug se você deixar em branco)"
          />
        </Field>

        <div className="grid grid-cols-2 gap-3">
          <Field label="Slug (opcional)">
            <input
              className="input font-mono text-[13px]"
              value={form.slug ?? ''}
              onChange={(e) => set('slug', e.target.value)}
              placeholder="gerado-do-titulo"
            />
          </Field>
          <Field label="Categoria">
            <input
              className="input"
              value={form.category ?? ''}
              onChange={(e) => set('category', e.target.value)}
              placeholder="Automação, Site…"
            />
          </Field>
        </div>

        <Field label="Resumo (excerpt)">
          <textarea
            className="input"
            rows={2}
            value={form.excerpt ?? ''}
            onChange={(e) => set('excerpt', e.target.value)}
          />
        </Field>

        <Field label="Corpo (Markdown)">
          <textarea
            className="input font-mono text-[13px] leading-relaxed"
            rows={14}
            value={form.body_md ?? ''}
            onChange={(e) => set('body_md', e.target.value)}
            placeholder={'# Título\n\nEscreva em Markdown: **negrito**, listas, ```código```, tabelas…'}
          />
        </Field>

        <div className="grid grid-cols-2 gap-3">
          <Field label="Capa (URL da imagem)">
            <input
              className="input text-[13px]"
              value={form.cover_url ?? ''}
              onChange={(e) => set('cover_url', e.target.value)}
              placeholder="https://…"
            />
          </Field>
          <Field label="Tags (separadas por vírgula)">
            <input
              className="input"
              value={form.tagsText ?? ''}
              onChange={(e) => set('tagsText', e.target.value)}
            />
          </Field>
        </div>

        <ImagensPanel
          editando={editando}
          acoes={acoes}
          onAtualizado={onPostAtualizado}
        />

        <div className="border-t border-line pt-3 mt-1">
          <div className="eyebrow mb-2">SEO</div>
          <Field
            label={`Meta description (${metaLen}/160${metaOk ? ' ✓' : ' — ideal 120–160'})`}
          >
            <textarea
              className={`input ${metaLen > 160 ? 'border-red-300' : ''}`}
              rows={2}
              value={form.meta_description ?? ''}
              onChange={(e) => set('meta_description', e.target.value)}
            />
          </Field>
          <div className="grid grid-cols-2 gap-3 mt-3">
            <Field label="Keyword alvo">
              <input
                className="input"
                value={form.keyword_alvo ?? ''}
                onChange={(e) => set('keyword_alvo', e.target.value)}
              />
            </Field>
            <Field label="OG title (opcional)">
              <input
                className="input"
                value={form.og_title ?? ''}
                onChange={(e) => set('og_title', e.target.value)}
              />
            </Field>
          </div>
          <label className="flex items-center gap-2 text-[13px] text-ink-soft mt-3">
            <input
              type="checkbox"
              checked={!!form.noindex}
              onChange={(e) => set('noindex', e.target.checked)}
            />
            noindex (tirar do Google — pra páginas finas/legais)
          </label>
        </div>

        <Field label="Agendar publicação (opcional — futuro fica fora do ar até a data)">
          <input
            type="datetime-local"
            className="input"
            value={toLocalInput(form.published_at)}
            onChange={(e) =>
              set(
                'published_at',
                e.target.value ? new Date(e.target.value).toISOString() : null,
              )
            }
          />
        </Field>
        </>
        )}
      </div>

      <div className="flex justify-end gap-2 mt-5 pt-4 border-t border-line">
        <button type="button" onClick={onClose} className="btn btn-ghost">
          Cancelar
        </button>
        <button
          type="button"
          onClick={onSave}
          disabled={acoes.loading || !form.title.trim()}
          className="btn btn-primary"
        >
          {acoes.loading ? 'Salvando…' : editando ? 'Salvar' : 'Criar rascunho'}
        </button>
      </div>
    </Modal>
  );
}

const PAUTA_FONTE_COR: Record<string, string> = {
  projeto: 'bg-blue-100 text-blue-700',
  seo: 'bg-green-100 text-green-700',
  tendencia: 'bg-purple-100 text-purple-700',
  manual: 'bg-bg-alt text-ink-mute',
};

function PautasView({
  acoes,
  onEscrever,
}: {
  acoes: ReturnType<typeof useBlogActions>;
  onEscrever: (p: BlogPauta) => void;
}) {
  const { pautas, loading, refetch } = useBlogPautas();
  const [gerando, setGerando] = useState(false);
  const [foco, setFoco] = useState('');
  const [sementes, setSementes] = useState('');

  async function gerar() {
    setGerando(true);
    const r = await acoes.gerarPautas({
      quantidade: 6,
      publico: foco || undefined,
      sementes: sementes || undefined,
    });
    setGerando(false);
    if (r) refetch();
  }

  async function descartar(p: BlogPauta) {
    if (await acoes.atualizarPauta(p.id, { status: 'descartada' })) refetch();
  }

  async function apagar(p: BlogPauta) {
    if (!confirm(`Apagar a pauta "${p.titulo}"?`)) return;
    if (await acoes.removerPauta(p.id)) refetch();
  }

  const ativas = pautas.filter((p) => p.status !== 'descartada');

  return (
    <div>
      <div className="card p-4 mb-5 flex flex-col gap-3">
        <div className="text-[13px] text-ink-soft">
          <strong>Motor de pauta.</strong> A IA propõe ideias de post de 3 fontes
          (seus projetos viram case, buscas de SEO e tendências do setor),
          ranqueadas por prioridade. Você escolhe e manda escrever.
        </div>
        <div className="flex gap-2 flex-wrap items-center">
          <select
            className="input max-w-[180px]"
            value={foco}
            onChange={(e) => setFoco(e.target.value)}
          >
            <option value="">Público (qualquer)</option>
            <option value="cliente">Foco cliente</option>
            <option value="recrutador">Foco recrutador</option>
          </select>
          <input
            className="input flex-1 min-w-[180px]"
            placeholder="Temas/keywords pra mirar (opcional)"
            value={sementes}
            onChange={(e) => setSementes(e.target.value)}
          />
          <button
            type="button"
            onClick={gerar}
            disabled={gerando}
            className="btn btn-primary"
          >
            {gerando ? 'Gerando…' : '✨ Gerar pautas'}
          </button>
        </div>
      </div>

      {loading ? (
        <p className="text-ink-mute text-sm">Carregando…</p>
      ) : ativas.length === 0 ? (
        <p className="text-ink-mute text-sm">
          Backlog vazio. Clique em <strong>Gerar pautas</strong> pra a IA propor
          ideias.
        </p>
      ) : (
        <div className="flex flex-col gap-2">
          {ativas.map((p) => (
            <div key={p.id} className="card p-4 flex items-center gap-4">
              <div
                className="shrink-0 w-11 h-11 rounded-md bg-bg-alt flex items-center justify-center font-display font-semibold text-ink"
                title="Prioridade"
              >
                {p.score}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1 flex-wrap">
                  <span
                    className={`text-[10px] uppercase tracking-wide px-1.5 py-0.5 rounded-sm font-mono ${PAUTA_FONTE_COR[p.fonte] ?? PAUTA_FONTE_COR.manual}`}
                  >
                    {p.fonte}
                  </span>
                  {p.publico && (
                    <span className="text-[11px] text-ink-mute">{p.publico}</span>
                  )}
                  {p.status === 'escrita' && (
                    <span className="text-[11px] text-green-600">✓ escrita</span>
                  )}
                </div>
                <h3 className="font-medium text-ink text-[15px] m-0">
                  {p.titulo}
                </h3>
                {p.resumo && (
                  <p className="text-[12px] text-ink-mute m-0 mt-0.5 line-clamp-2">
                    {p.resumo}
                  </p>
                )}
                {p.keyword_alvo && (
                  <div className="text-[11px] text-ink-mute font-mono mt-0.5">
                    kw: {p.keyword_alvo}
                  </div>
                )}
              </div>
              <div className="flex items-center gap-1.5 shrink-0">
                <button
                  type="button"
                  onClick={() => onEscrever(p)}
                  disabled={acoes.loading}
                  className="btn btn-primary text-[13px]"
                  title="A IA escreve o rascunho completo (leva alguns segundos)"
                >
                  {acoes.loading ? 'Escrevendo…' : 'Escrever'}
                </button>
                <button
                  type="button"
                  onClick={() => descartar(p)}
                  className="btn btn-ghost text-[13px]"
                >
                  Descartar
                </button>
                <button
                  type="button"
                  onClick={() => apagar(p)}
                  className="text-ink-mute hover:text-red-600 text-lg px-1.5"
                  aria-label="Apagar"
                  title="Apagar"
                >
                  ×
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function BriefPanel({
  brief,
  setBrief,
  gerando,
  onGerar,
  fallbackTitulo,
}: {
  brief: BlogBriefRequest;
  setBrief: (b: BlogBriefRequest) => void;
  gerando: boolean;
  onGerar: () => void;
  fallbackTitulo: string;
}) {
  const set = (k: keyof BlogBriefRequest, v: string) =>
    setBrief({ ...brief, [k]: v });
  return (
    <div className="rounded-md border border-brand/30 bg-brand-soft/40 p-3 flex flex-col gap-2">
      <div className="text-[12px] text-ink-soft">
        Descreva o brief — a IA escreve o rascunho em Markdown (ancorado no seu
        Perfil Mestre, sem inventar números). Você revisa antes de publicar.
      </div>
      <input
        className="input"
        placeholder={`Tema do post${fallbackTitulo ? ` (ou usa "${fallbackTitulo}")` : ''}`}
        value={brief.tema}
        onChange={(e) => set('tema', e.target.value)}
      />
      <div className="grid grid-cols-2 gap-2">
        <input
          className="input"
          placeholder="Keyword-alvo"
          value={brief.keyword_alvo ?? ''}
          onChange={(e) => set('keyword_alvo', e.target.value)}
        />
        <select
          className="input"
          value={brief.publico ?? ''}
          onChange={(e) => set('publico', e.target.value)}
        >
          <option value="">Público (qualquer)</option>
          <option value="cliente">Cliente (PME)</option>
          <option value="recrutador">Recrutador</option>
        </select>
      </div>
      <textarea
        className="input"
        rows={2}
        placeholder="Pontos que o post deve cobrir (opcional)"
        value={brief.pontos ?? ''}
        onChange={(e) => set('pontos', e.target.value)}
      />
      <div className="flex justify-end">
        <button
          type="button"
          onClick={onGerar}
          disabled={gerando || (!brief.tema.trim() && !fallbackTitulo.trim())}
          className="btn btn-primary text-[13px]"
        >
          {gerando ? 'Escrevendo…' : 'Gerar rascunho'}
        </button>
      </div>
    </div>
  );
}

const SEO_COR: Record<ChecklistSeo['nivel'], string> = {
  ruim: 'text-red-700 bg-red-50 border-red-200',
  ok: 'text-amber-700 bg-amber-50 border-amber-200',
  bom: 'text-green-700 bg-green-50 border-green-200',
  otimo: 'text-green-700 bg-green-50 border-green-200',
};
const ITEM_ICON: Record<string, string> = { ok: '✓', warn: '!', fail: '×' };
const ITEM_COR: Record<string, string> = {
  ok: 'text-green-600',
  warn: 'text-amber-600',
  fail: 'text-red-600',
};

function SeoPanel({ seo }: { seo: ChecklistSeo }) {
  const pendentes = seo.itens.filter((i) => i.status !== 'ok');
  return (
    <div className={`rounded-md border p-3 ${SEO_COR[seo.nivel]}`}>
      <div className="flex items-center gap-2 mb-1">
        <strong className="text-[15px]">SEO {seo.score}/100</strong>
        <span className="text-[12px] uppercase tracking-wide">{seo.nivel}</span>
      </div>
      {pendentes.length === 0 ? (
        <div className="text-[13px]">Tudo certo no checklist on-page. ✓</div>
      ) : (
        <ul className="text-[12px] flex flex-col gap-0.5 mt-1">
          {pendentes.map((i) => (
            <li key={i.id}>
              <span className={`font-mono ${ITEM_COR[i.status]}`}>
                {ITEM_ICON[i.status]}
              </span>{' '}
              {i.label}
              {i.dica ? <span className="text-ink-mute"> — {i.dica}</span> : null}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function ImagensPanel({
  editando,
  acoes,
  onAtualizado,
}: {
  editando: BlogPostAdmin | null;
  acoes: ReturnType<typeof useBlogActions>;
  onAtualizado: (p: BlogPostAdmin) => void;
}) {
  const [prompt, setPrompt] = useState('');
  const [gerando, setGerando] = useState(false);
  const [sugestoes, setSugestoes] = useState<CapaSugestao[] | null>(null);
  const [sugerindo, setSugerindo] = useState(false);
  const [gerandoConteudo, setGerandoConteudo] = useState(false);
  const [sugConteudo, setSugConteudo] = useState<ImagemConteudoSugestao[] | null>(
    null,
  );
  const [sugerindoConteudo, setSugerindoConteudo] = useState(false);
  const [inserindo, setInserindo] = useState<number | null>(null);
  const [trocando, setTrocando] = useState<string | null>(null);

  if (!editando) {
    return (
      <div className="rounded-md border border-line bg-bg-alt/40 p-3 text-[12px] text-ink-mute">
        Imagens: salve o rascunho primeiro pra gerar a capa com IA ou enviar a
        sua versão final.
      </div>
    );
  }
  const id = editando.id;
  // marcadores {{IMG: ...}} pendentes no corpo SALVO (o redator insere; aqui geramos)
  const marcadores = (editando.body_md?.match(/\{\{\s*IMG:/gi) ?? []).length;
  // imagens já no corpo (papel=secao) — pra visualizar/baixar/substituir
  const imgsConteudo = (editando.imagens ?? []).filter((i) => i.papel === 'secao');

  async function gerarConteudo() {
    setGerandoConteudo(true);
    const post = await acoes.gerarImagensConteudo(id);
    setGerandoConteudo(false);
    if (post) onAtualizado(post);
  }

  async function sugerirConteudo() {
    setSugerindoConteudo(true);
    const r = await acoes.sugerirImagensConteudo(id);
    setSugerindoConteudo(false);
    if (r) setSugConteudo(r.sugestoes);
  }

  async function inserirConteudo(s: ImagemConteudoSugestao, i: number) {
    setInserindo(i);
    const post = await acoes.inserirImagemConteudo(id, {
      prompt: s.prompt,
      alt: s.alt,
      secao: s.secao,
      aspect_ratio: s.aspect_ratio,
    });
    setInserindo(null);
    if (post) {
      onAtualizado(post);
      // tira a sugestão já usada da lista
      setSugConteudo((prev) => prev?.filter((_, idx) => idx !== i) ?? null);
    }
  }

  async function trocarConteudo(urlAntiga: string, alt: string, file?: File | null) {
    if (!file) return;
    setTrocando(urlAntiga);
    const post = await acoes.substituirImagemConteudo(id, file, urlAntiga, alt);
    setTrocando(null);
    if (post) onAtualizado(post);
  }

  async function sugerir() {
    setSugerindo(true);
    const r = await acoes.sugerirCapas(id);
    setSugerindo(false);
    if (r) setSugestoes(r.sugestoes);
  }

  async function gerarComPrompt(p: string, aspect = '16:9') {
    if (!p.trim()) return;
    setGerando(true);
    const post = await acoes.gerarImagem(id, {
      prompt: p,
      papel: 'cover',
      aspect_ratio: aspect,
    });
    setGerando(false);
    if (post) {
      onAtualizado(post);
      setSugestoes(null);
    }
  }

  async function enviar(file?: File | null) {
    if (!file) return;
    const p = await acoes.uploadImagem(id, file, 'cover', editando?.title);
    if (p) onAtualizado(p);
  }

  return (
    <div className="rounded-md border border-line p-3 flex flex-col gap-2">
      <div className="eyebrow">Capa</div>
      {editando.cover_url ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={editando.cover_url}
          alt="capa atual"
          className="w-full max-h-44 object-cover rounded-md border border-line"
        />
      ) : (
        <div className="text-[12px] text-ink-mute">Sem capa ainda.</div>
      )}
      <div className="flex gap-2 items-center flex-wrap">
        <button
          type="button"
          onClick={sugerir}
          disabled={sugerindo || gerando}
          className="btn btn-ghost text-[13px]"
        >
          {sugerindo ? 'Pensando…' : '💡 Sugerir 3 capas'}
        </button>
        <label className="btn btn-ghost text-[13px] cursor-pointer">
          Enviar imagem
          <input
            type="file"
            accept="image/png,image/jpeg,image/webp"
            className="hidden"
            onChange={(e) => enviar(e.target.files?.[0])}
          />
        </label>
      </div>

      {sugestoes && (
        <div className="grid sm:grid-cols-3 gap-2">
          {sugestoes.map((s, i) => (
            <div
              key={i}
              className="border border-line rounded-md p-2.5 flex flex-col gap-1.5 bg-bg-alt/30"
            >
              <div className="text-[12px] font-medium text-ink">{s.conceito}</div>
              {s.descricao && (
                <p className="text-[11px] text-ink-mute m-0 flex-1">
                  {s.descricao}
                </p>
              )}
              <button
                type="button"
                onClick={() => gerarComPrompt(s.prompt, s.aspect_ratio)}
                disabled={gerando}
                className="btn btn-primary text-[12px] mt-1"
              >
                {gerando ? 'Gerando…' : 'Gerar esta'}
              </button>
            </div>
          ))}
        </div>
      )}

      <div className="flex gap-2 items-center flex-wrap">
        <input
          className="input flex-1 min-w-[200px]"
          placeholder="…ou descreva a capa você mesmo"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
        />
        <button
          type="button"
          onClick={() => gerarComPrompt(prompt)}
          disabled={gerando || !prompt.trim()}
          className="btn btn-ghost text-[13px]"
        >
          {gerando ? 'Gerando…' : '✨ Gerar'}
        </button>
      </div>
      <p className="text-[11px] text-ink-mute m-0">
        A IA gera um rascunho; você pode baixar, ajustar fora e reenviar a versão
        final antes de publicar.
      </p>

      <div className="border-t border-line pt-2.5 mt-1 flex flex-col gap-2">
        <div className="eyebrow">Imagens do conteúdo</div>
        <div className="flex items-center gap-2 flex-wrap">
          <button
            type="button"
            onClick={sugerirConteudo}
            disabled={sugerindoConteudo || inserindo !== null}
            className="btn btn-ghost text-[13px]"
            title="A IA sugere imagens pro corpo, por seção — você escolhe quais gerar"
          >
            {sugerindoConteudo ? 'Pensando…' : '💡 Sugerir imagens do conteúdo'}
          </button>
          {marcadores > 0 && (
            <button
              type="button"
              onClick={gerarConteudo}
              disabled={gerandoConteudo}
              className="btn btn-ghost text-[13px]"
              title="Gera as imagens dos marcadores {{IMG}} que o redator deixou no corpo"
            >
              {gerandoConteudo
                ? 'Gerando…'
                : `🖼️ Gerar marcadores {{IMG}} (${marcadores})`}
            </button>
          )}
        </div>

        {sugConteudo && sugConteudo.length === 0 && (
          <p className="text-[11px] text-ink-mute m-0">
            Todas as sugestões foram inseridas. Clique de novo pra mais ideias.
          </p>
        )}

        {sugConteudo && sugConteudo.length > 0 && (
          <div className="grid sm:grid-cols-2 gap-2">
            {sugConteudo.map((s, i) => (
              <div
                key={i}
                className="border border-line rounded-md p-2.5 flex flex-col gap-1.5 bg-bg-alt/30"
              >
                <div className="text-[12px] font-medium text-ink">{s.conceito}</div>
                {s.secao && (
                  <div className="text-[10px] uppercase tracking-wide text-ink-mute font-mono">
                    ↳ {s.secao}
                  </div>
                )}
                {s.descricao && (
                  <p className="text-[11px] text-ink-mute m-0 flex-1">{s.descricao}</p>
                )}
                <button
                  type="button"
                  onClick={() => inserirConteudo(s, i)}
                  disabled={inserindo !== null}
                  className="btn btn-primary text-[12px] mt-1"
                >
                  {inserindo === i ? 'Gerando…' : 'Gerar e inserir'}
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Galeria das imagens já no corpo: visualizar, baixar e substituir */}
        {imgsConteudo.length > 0 && (
          <div className="grid sm:grid-cols-2 gap-2">
            {imgsConteudo.map((img) => (
              <div
                key={img.url}
                className="border border-line rounded-md p-2 flex flex-col gap-1.5"
              >
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={img.url}
                  alt={img.alt ?? 'imagem do conteúdo'}
                  className="w-full h-28 object-cover rounded-md border border-line"
                />
                {img.alt && (
                  <p className="text-[11px] text-ink-mute m-0 line-clamp-2">{img.alt}</p>
                )}
                <div className="flex items-center gap-2 flex-wrap">
                  <a
                    href={img.url}
                    target="_blank"
                    rel="noreferrer"
                    download
                    className="btn btn-ghost text-[12px]"
                  >
                    Baixar
                  </a>
                  <label className="btn btn-ghost text-[12px] cursor-pointer">
                    {trocando === img.url ? 'Enviando…' : 'Substituir'}
                    <input
                      type="file"
                      accept="image/png,image/jpeg,image/webp"
                      className="hidden"
                      disabled={trocando !== null}
                      onChange={(e) =>
                        trocarConteudo(img.url, img.alt ?? '', e.target.files?.[0])
                      }
                    />
                  </label>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

/** ISO (UTC) → valor do <input datetime-local> (hora local), ou ''. */
function toLocalInput(iso?: string | null): string {
  if (!iso) return '';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '';
  const local = new Date(d.getTime() - d.getTimezoneOffset() * 60000);
  return local.toISOString().slice(0, 16);
}

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <label className="flex flex-col gap-1">
      <span className="text-[12px] text-ink-soft">{label}</span>
      {children}
    </label>
  );
}

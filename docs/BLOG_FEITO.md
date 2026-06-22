# 📰 BLOG (P5 §6) — FEITO

> Log do que já saiu do **agente de Blog headless** (studio = cérebro, site `reativesystems.com.br`
> consome via API). Movido do `PLANO-MESTRE.md` §6 em 2026-06-21. O caminho à frente (B5/LinkedIn/
> Docs-keeper + pendências) continua no plano.

## ✅ EM PRODUÇÃO (2026-06-21)
- **Studio** (`studio.reativesystems.com.br`): API pública do blog + admin + migrações + permissão
  `blog.editar` (seed) + **cdn de imagens** (`cdn.reativesystems.com.br` → MinIO bucket `blog`, atrás do
  Caddy, HTTPS Let's Encrypt). App existente (CRM/freela/finanças) intacto.
- **Site** (`reativesystems.com.br`, apex→www 308, repo `reative-site` no Vercel): consome o studio via
  ISR; home com 3 recentes + `/blog` navegável + post + categorias; **SEO consistente** no www.
- **Deploy** = `rsync` (excl. `.env`/volumes/`.claude`) → `02-deploy.sh` (build api+web; `alembic upgrade
  head` no start do api). Envs novas no `.env` de prod: `S3_ENDPOINT/REGION/PUBLIC_URL`, `S3_BUCKET_BLOG`,
  `CDN_DOMAIN`, `SITE_URL`, `GEMINI_IMAGE_MODEL`, `GEMINI_MODEL_BLOG` (também listadas no `environment:` do
  `api` no compose). Vercel: `NEXT_PUBLIC_API_URL`=studio, `NEXT_PUBLIC_SITE_URL`=www.

## Arquitetura (§6.A) — studio ⇄ site
- Vertical slice `blog` no backend (`db/models/blog/`, categoria Reative). API **pública** sem auth
  `/api/public/blog` (só `publicado` E `published_at<=now()`, `Cache-Control`, 301 em rename) +
  `/sitemap.xml` + `/feed.xml`. API **admin** `/api/blog` (auth `blog.editar`).
- Corpo em **Markdown**; imagens no **MinIO/S3** com URL pública permanente (`s3_storage.public_url`).
- Modelo `blog_post` enriquecido (slug, seo[*], imagens jsonb, published_at=gate, etc.) + `blog_redirect`
  (301) + `blog_pauta` (B3). Migrações: `f3b9c1d4e7a2` (post+redirect) → `a7c2e5f9b1d8` (pauta).

## Fatias (todas feitas e testadas c/ Gemini real)
- **B0 — Cano ponta-a-ponta:** modelo+API pública+sitemap/feed; site com `lib/api/blog.ts` +
  `lib/blog/source.tsx` + renderer Markdown (react-markdown/gfm/slug/highlight) + `/blog`.
- **B1 — CRUD + UI:** agente "Blog" no `registry.py`; admin `/api/blog` (CRUD + `PATCH /status` +
  301 no rename); `BlogScreen` (abas por status, editor Markdown + SEO).
- **B2 — Redator + checklist SEO + checkpoint:** `analyzers/blog/redator` (**anti-mentira** ancorado no
  Perfil Mestre) → `body_md`; `checklist_seo.py` determinístico (gate 0-100, anti-keyword-stuffing).
- **B3 — Motor de pauta:** `blog_pauta` + `analyzers/blog/pauta` (3 fontes: projeto/seo/tendência) +
  aba Pautas (gerar/escolher/escrever).
- **B4 — Coordenador 1-clique + agendamento + cron:** `coordenador.py` (pauta→rascunho), `published_at`
  editável, `jobs/blog_pautas.py` (semanal, off por default).
- **B-IMG — Imagens:** `analyzers/gemini/image_client.py` + `blog_service/imagens.py` (gera/upload →
  MinIO bucket público). **B-IMG+:** imagens no conteúdo (marcadores `{{IMG}}` + sugestões por seção),
  **galeria** (preview/baixar/substituir), fix do "16:9" desenhado na imagem.
- **Modelos premium (blog ≤1 post/dia):** texto `gemini-2.5-pro` (`gemini_model_blog`), imagem
  `gemini-3-pro-image` ("nano banana pro" — `image_client` roteia gemini→generateContent, imagen→predict).
- **Sugestão de 3 capas** antes de gerar; **pré-visualização** do post no editor (`PostPreview`).

## SEO (site, completo)
JSON-LD `BlogPosting`+`BreadcrumbList`+`Organization`+`WebSite`(SearchAction)+`Blog`+`ItemList`;
`app/sitemap.ts` + `app/robots.ts`; canonical/twitter/OG article; **páginas de categoria** indexáveis
`/blog/categoria/[slug]` + breadcrumbs; busca por URL `/blog?q=`; RSS no `<head>`; `loading=lazy` + LCP.
Helpers em `lib/blog/seo.ts`.

## Polimentos de produção (2026-06-21)
- **CTA do post** adapta por categoria (`lib/blog/cta.ts`); botão laranja "Entrar em contato" → `/#contato`
  (cor corrigida — `.article-prose a` vazava no botão); WhatsApp secundário; UI refinada.
- **Autor único** `Pablo Ortiz` (config/`NEXT_PUBLIC_AUTHOR`) na assinatura + JSON-LD.
- **Home/site sem fallback** de exemplo (mostra só posts reais do studio).
- **Anti-oferta-fantasma:** redator proibido de prometer recurso inexistente (planilha/template/bônus/
  "link virá aqui") → lista em `pendencias`; checklist SEO detecta placeholder/oferta (`oferta_fantasma`).

## Bugs de prod resolvidos na raiz
- `package-lock.json` regenerado com **npm 10.8.2** (build usa essa versão; npm 11 local gerava lock
  incompatível — `@emnapi/*` faltando).
- **JSON do `gemini-2.5-pro`:** (1) `client.py` junta partes ignorando `thought` (modelos thinking
  emitiam raciocínio antes do JSON); (2) `extrair_json` aceita **array `[...]` no topo** (o Pro às vezes
  devolve o array direto) — `[[gemini-thinking-parts]]`. Era a causa do "A IA não retornou pautas válidas".
- **Imagens com `minio:9000`:** compose não passava `S3_PUBLIC_URL` pro api → corrigido; URLs antigas
  trocadas no banco; **CSP do studio** liberou `img-src https://{$CDN_DOMAIN}` (preview do admin).
- **Domínio:** apex→www 308; `NEXT_PUBLIC_SITE_URL`=www → sitemap/canonical consistentes.

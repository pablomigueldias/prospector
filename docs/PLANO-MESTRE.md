
# 🧭 PLANO MESTRE — Prospector (roadmap único de código)

> **Fonte única do caminho de código.** Consolida 6 planos antigos
> (`plano-agentes-autonomos`, `plano-crm-profissional`, `plano-sistema-self-service`,
> `MELHORIAS_FREELA`, `MELHORIAS_VAGAS`, `MELHORIAS_FINANCAS`) num só roadmap,
> reorganizado pelas prioridades reais do Pablo. Data da consolidação: **2026-06-18**.
>
> **Princípios que não mudam:**
> - *Output primeiro, código depois* — cada fatia é **vertical (1 commit)**, testável, que já entrega valor sozinha. Melhoria vira backlog, não scope creep.
> - *Anti-mentira* — a IA reorganiza a verdade (Perfil Mestre), nunca inventa.
> - *Para no rascunho / supervisão humana* — nada que sai pra fora (e-mail, proposta, post, cobrança) é enviado sem o OK do Pablo.
> - Convenções técnicas em `[[stack-prospector]]` e `[[db-session-convention]]`.
>
> **Fora deste plano (planos PESSOAIS / não-código, ficam separados):**
> `plano.md` (cronograma diário), `Plano-Entrar-no-Jogo.md` (estratégia de captação),
> `Perfil-Freelancer.md` (perfil/conteúdo), `Workana.md` (filosofia/estratégia do
> copiloto), `Guia-Pagina-Projetos-Reative-Site.md` (é de outro repo).
> **Histórico:** `*_FEITO.md` (log do que já saiu) e `CONTINUA*.md` (handoffs).

---

## 0. Estado atual (snapshot — 2026-06-20)

| Módulo | Estado | Resumo |
|---|---|---|
| **Vagas** | ✅ bom | CRUD por JD, analisar (match/gaps/veredito), candidatura, currículo ATS, pipeline, funil, plano-de-gaps (**ranking "O que estudar" corrigido**). *Pablo: "só falta lapidar o modelo de IA".* |
| **Freela** | ✅ **essencialmente fechado** | Agente especializado + gestão total na tela + autonomia (cadeia coordenador). Detalhe em `FREELA_FEITO.md`. **Pablo satisfeito (2026-06-20); resto = manutenção** (§2). |
| **Site (Reative Systems)** | 🟢 **próximo foco** | Next.js institucional headless-ready (`NEXT_PUBLIC_API_URL`). **P5:** studio vira o cérebro (blog headless + LinkedIn + docs). Começar pelo **agente de blog** (§6). |
| **CRM** | ✅ completo | 5 seções (Empresas/Contatos/Negócios/Atividades/Projetos) fora do Notion, CRUD, filtros, pipeline+forecast, ficha 360, dashboard, edição inline, drawer, opções gerenciáveis. |
| **MAS (multi-agente)** | ✅ núcleo | Memória compartilhada (blackboard), coordenador (cadeia candidatura), outcomes, briefing noturno. Subiu a escada inteira do curso. |
| **Self-service (Parte 1)** | ✅ núcleo | Cockpit (S1), Observabilidade (S2), Configurações na UI (S3), Agendamentos (S4), Export/Backup (S8). Falta S5–S7. |
| **Finanças** | ✅ usável | Bot Telegram, contas/cartões/boletos, recorrências, orçamento, relatório. Backlog: **Dívidas/parcelamentos** (prioridade), Open Finance, NL queries. |
| **Auth** | ✅ | Login/sessão/RBAC (schema auth). Falta endurecimento (2FA obrigatório admin). |

> Detalhe do que **já saiu** vive nos `*_FEITO.md`. Este plano lista só o **caminho à frente** (+ contexto do que está pronto pra não repetir).

---

## 1. O caminho único (prioridades)

1. 🟢 **P5 — Reative Systems: Presença & Conteúdo** (🆕 FOCO ATUAL, 2026-06-20): **agente de blog** (começar) → **LinkedIn** → **Docs-keeper**. O studio vira o cérebro headless do site. (§6)
2. 🟡 **P2 — Novos agentes** de captação/comercial: **Propostas Comerciais, Radar de Oportunidades, Outbound**. (§3)
3. 🟢 **P3 — Vagas**: **lapidar o modelo de IA** (+ backlog de conveniência). (§4)
4. ✅ **P1 — Freela**: essencialmente fechado → **manutenção** (Pablo satisfeito, vai testar). (§2)
5. ⚪ **P4 — Backlogs de manutenção**: self-service S5–S7, MAS, CRM, Finanças, infra. (§5)

---

## 2. ✅ P1 — FREELA (essencialmente fechado — manutenção)

> Virou **agente especializado + gestão total na tela + autonomia** (meta-bússola: **R$10k líq./mês**).
> **O que SAIU** (análise profunda, momento/custo de oportunidade, motor da meta + progresso do mês,
> cadeia coordenador, cold start, win-rate, fila clara, tela em abas, importar por URL, A/B por ângulo…)
> → `FREELA_FEITO.md`. **Pablo satisfeito (2026-06-20); vai testar.** Resto = manutenção:

- [ ] ⏳ **Validar a cadeia coordenador na tela** — `ProjetoDrawer` → "🤝 Coordenador — proposta completa" → Preparar → checkpoint → Continuar. *(implementação feita; falta o Pablo confirmar — `[[freela-validar-coordenador]]`.)*
- [~] 🟡 **Opções dinâmicas** — motivo de perda feito; **falta** estágios de proposta + tags.
- [~] 🟡 **Extrair dados do cliente** (país, pagamento verificado, nº projetos, rating, idioma → auto-preenche `Cliente`) + **data de publicação** + **tipo de contrato** como colunas. *(migração/fluxo de `Cliente`.)*
- [ ] 🟡 **Timeline (MAS-1) na tela** de proposta/projeto (o coordenador já grava os eventos; falta exibir).
- [ ] 🟡 **Evento de proposta com payload estruturado** — `pessoal_freela_evento` (`proposta_id`+`payload` JSONB) p/ timeline rica.
- [~] 🟡 **Banco de propostas vencedoras — parte 2** — base feita (`GET /freela/propostas/vencedoras`); quando houver fechadas: ligar o seam `exemplos_vencedores` no redator + curadoria + UI.
- [ ] ⏸️ **Gringo/USD & recorrente como peso** no motor da meta — **ADIADO** (sem inglês ainda). A parte "recorrente como peso" pode ir isolada.
- [ ] 🟢 **Polimentos:** multimoeda USD↔BRL, motivo de perda estruturado, **histórico de precificações**, acompanhar prazo de entrega, relatório mensal (Recharts), dedup do follow-up, adapter 99freelas.

---

## 3. 🟡 P2 — Novos agentes (captação + comercial)

> Os que o Pablo marcou como interessantes. Cada um encaixa na arquitetura
> (analyzer/collector → service → memória/coordenador) — evolução, não reescrita.

### 3.1 📄 Agente de Propostas Comerciais 🟡 (Pablo: "interessante")
De um briefing → **escopo + preço + prazo + PDF** pronto. Estende o precificador do
freela pro CRM/negócios. Para no rascunho (PDF é gerado, envio é decisão do Pablo).

### 3.2 🔎 Agente Radar de Oportunidades 🟡 (Pablo: "muito bom")
Monitora fontes (vagas/freelas/editais) e **injeta no funil** automaticamente, já com
match score. Os collectors (duckduckgo/website) já existem; pluga no agente Vagas/Freela.

### 3.3 🧲 Agente Outbound 🟡 (Pablo: "muito bom")
Dado um ICP (perfil de cliente ideal), acha empresas + decisores e gera a 1ª
abordagem. O Prospector + copywriter já são a base; grava no CRM como negócio inicial.

### 3.4 Backlog de agentes (Parte 2 — quando fizer sentido)
- 🧠 **Segundo Cérebro (RAG)** — indexa Second-Brain/certificados/projetos/docs; vira insumo de todos. ⚠️ **Decisão de arquitetura:** sem GPU no VPS — embeddings via **Gemini (cloud)** ou **RTX 2060** por fila (ver `[[deploy-vps-hetzner]]`).
- 🪶 **Conteúdo (LinkedIn/X)** — transforma o que você FEZ em posts/threads + calendário editorial.
- 🤝 **Onboarding de cliente** (negócio "ganho" → cria projeto + e-mail boas-vindas + checklist).
- 💸 **Cobrança** (régua a partir de projetos/faturas, com OK).
- 🗣️ **Reunião → Ação** (transcrição → atividades no CRM + follow-ups).
- 👀 **Code Review / PR**, 📚 **Documentação**, 🧪 **Testes** (engenharia).
- 🧭 **Roadmap/Backlog** (ideias → backlog priorizado por impacto×esforço).
- 📈 **Financeiro Estratégico** (runway, preço/meta, alerta de desvio).
- 🎛️ **Comando por linguagem natural** (barra "faça X" usando o `nlu` → roteia pro agente/cadeia).

---

## 4. 🟢 P3 — Vagas (lapidar o modelo de IA + conveniência)

> **Pablo: "vagas está muito bom, só precisa lapidar o modelo de IA."** Então a
> prioridade aqui é **qualidade da análise/match/candidatura**, não features novas.
> Princípios: *para no rascunho* + *anti-mentira*.

### 4.1 🔴 Lapidar o modelo de IA (prioridade do módulo)
- [ ] 🔴 **Afinar prompts** de `analyzers/{vaga,candidatura,curriculo}` — match mais preciso (obrigatórios×desejáveis), veredito mais útil, currículo ATS mais aderente. (Conecta com **S5 Prompt Studio** §5.1 — editar/preview/rollback sem deploy.)
- [ ] 🟡 **Nota de confiança / anti-alucinação** no match (não inflar aderência sem prova no Perfil Mestre).

### 4.2 Backlog de conveniência (alta utilidade)
- [ ] 🔴 **Follow-up / lembretes** (`candidatei_em`/`proximo_followup_em`; agendador varre e avisa no Telegram; gerar follow-up rascunho). *(migração)*
- [ ] 🟡 **Prep de entrevista** (status=entrevista → perguntas técnicas+STAR+perguntas pra fazer+pontos fracos; analyzer `entrevista`).
- [ ] 🟢 **Deduplicação** ao cadastrar (mesmo link/empresa+título).
- [ ] 🟢 **Kanban do pipeline** (arrastar card muda status).
- [ ] 🟢 **Enviar candidatura com 1 clique** (opt-in, mailer, grava `enviado_em`, confirmação explícita).
- [ ] 🟢 **Timeline de eventos por vaga** (reusar MAS-1 / `pessoal_vaga_eventos`).

---

## 5. ⚪ P4 — Backlogs de manutenção

### 5.1 Self-service (Parte 1 restante)
- [ ] 🟡 **S5 — Prompt Studio** — mover prompts do código pra templates versionados (`config_app`/tabela própria) com variáveis, **preview** do prompt montado e **histórico/rollback**. Começar por 1 agente (candidatura ou vaga — casa com §4.1). *Pesado.*
- [ ] 🟡 **S6 — Manuseio direto em todas as telas** — reusar InlineCell/SidePanel/RecordModal/Timeline em Vaga e Freela (overlap com §2.A). *Refactor.*
- [ ] 🟡 **S7 — Opções dinâmicas além do CRM** — generalizar `OpcoesManager`/`crm_opcoes` pra status de vaga, estágios de freela, tags. *Médio: status de vaga é enum tipado hoje.*

### 5.2 MAS (multi-agente — núcleo feito)
- [ ] 🟡 **Ranking por `taxa_positiva`** — reordenar vagas/freela por probabilidade de retorno (quando houver histórico real de outcomes).
- [ ] 🟡 **Timeline (MAS-1) nas telas de Vaga/Freela** (hoje só no RecordModal do CRM) — overlap §2.E/§4.2.
- [ ] 🟢 **Normalizador de instituição** dos certificados (OCR às vezes erra: "IMPACTTA"→"IMPACTA").
- [ ] 🟢 **Cron do sync de certificados** (1×/dia → zero clique).

### 5.3 CRM (essencialmente completo)
- [ ] 🟢 **Gráficos Recharts** no dashboard comercial.
- [ ] 🟢 **Lembretes de atividade** via `jobs/` (atrasadas/hoje no Telegram).
- [ ] ⛔ Dual-write pro Notion — **não fazer de propósito** (o objetivo é sair do Notion).

### 5.4 Finanças
- [ ] 🔴 **Dívidas / parcelamentos (§4b — prioridade do Pablo)** — entidade `Divida` que **gera `Transacao` prevista** (herda "A pagar"/pagar/comprovante de graça) + N parcelas finitas + **saldo devedor** + seção no dashboard (progresso, próxima parcela, histórico). Fase 1 (modelo+cadastro) e 2 (seção) já entregam o essencial.
- [ ] 🔴 **Expor MinIO atrás do Caddy** — pra comprovantes **abrirem no navegador** (ajustar `S3_ENDPOINT` público + `img-src` do CSP). Destrava o comprovante visível (§4b fase 5).
- [ ] 🔴 **Perguntas em linguagem natural** sobre os dados (tool calling sobre os endpoints de resumo) — salto de "registrador" pra "copiloto"; vale no dashboard e no bot.
- [ ] 🟡 **Boleto parcelado na tela** (backend `POST /compras/boleto` existe; falta UI + surfaçar/pagar as `Parcela`s — hoje o carnê "some" da aba "A pagar").
- [ ] 🟡 **Atribuição por pessoa** (casal: quem lançou, mantendo carteira junta) + mapa chat→usuário em tabela.
- [ ] 🟡 **Insights proativos / detector de assinaturas / alerta de anomalia** (digest IA).
- [ ] 🟢 **Open Finance (Pluggy/Belvo)**, importar fatura/extrato (OFX/CSV/PDF), ler PIX/NF, **patrimônio líquido**, áudio no bot, coach de metas.

### 5.5 Infra / segurança / qualidade (transversal)
- [ ] 🟡 **2FA obrigatório pro admin** (`usuarios.gerenciar`).
- [ ] 🟡 **Testes E2E / verificação visual (Playwright)** — login + screenshot/smoke das telas.
- [ ] 🟡 **Monitoramento de saúde** (ping `/api/health` + aviso se cair; checar cron de backup).
- [ ] 🟢 **Testar o restore do backup**, logs estruturados, trilha de auditoria no front.
- [ ] ⚠️ **Dívida técnica conhecida:** ~362 avisos `ruff` manuais (B008 do `Depends` idiom etc.) — aceitos; não bloqueiam.

---

## 6. 🟢 P5 — Reative Systems: Presença & Conteúdo (site headless + agentes) 🆕 FOCO ATUAL

> **Visão (Pablo 2026-06-20):** o `studio` (este sistema) vira o **cérebro headless** de tudo que
> envolve a marca/profissionalismo — o site `reativesystems.com.br` é só a "cara". Três agentes
> novos: **Blog** (começar por aqui), **LinkedIn** e **Docs-keeper**. Objetivo: atrair
> **recrutador + cliente** via Google (SEO) e presença ativa.
>
> **Decisões travadas (2026-06-20):** (1) linkagem = **API headless** (posts no banco do studio, site
> consome via ISR); (2) fluxo = **rascunho → Pablo aprova → publica**; (3) motor de temas =
> **SEO/palavras-chave (ranquear no Google p/ recrutador E cliente) + projetos feitos viram case +
> tendências do setor**.

### 6.A Arquitetura da linkagem (studio ⇄ site) — base de tudo
> A "linkagem que o Pablo não sabia fazer". Resposta: **o site chama a API do studio.**
> **Análise pré-build (2026-06-20):** confirmado no código. Site mora em `~/Documentos/Reative Systems`
> (repo git próprio, branch `main`). **Achados que mudam o contrato** (entram no B0 pra não refatorar):
> (1) hoje TODO router do studio é autenticado (`require_permission`) — a API pública é **padrão novo**
> (`/api/public/blog`, sem auth/CSRF, com `Cache-Control`/ETag); (2) `s3_storage.presigned_url` **expira
> em 1h** — blog público precisa de **URL permanente** → puxa a task §5.4 "MinIO atrás do Caddy" pra DENTRO
> do B0; (3) o site usa **`coverClass`** (classe CSS, não URL), `date`/`readTime` como string e **corpo
> ReactNode (JSX), não markdown** — o B0 no site = renderer markdown + trocar `coverClass`→`cover_url`.
- **Studio = hub headless.** Nova vertical slice `blog` no backend (FastAPI): tabela `blog_post`
  (categoria **Reative**, não-pessoal → `db/models/blog/`), API **pública** read-only (só `status=publicado`
  E `published_at<=now()`) + API **admin** (CRUD / gerar / aprovar, B1+).
- **Site consome a API.** `lib/api/client.ts` usa `NEXT_PUBLIC_API_URL` (vazio→mock). Setar
  `NEXT_PUBLIC_API_URL=https://studio.reativesystems.com.br` + `CORS_ORIGINS` no studio liberando o
  domínio. O blog do site passa a **buscar via ISR** (`revalidate`) em vez de TSX hardcoded.
- **Corpo em Markdown** (amigável pro agente) renderizado no site (react-markdown/MDX), reusando
  `blog.css`/`app/blog/[slug]`. Migrar o post hardcoded (`lib/content/posts.tsx`) pro banco prova o cano.
- **Modelo `blog_post` (enriquecido — pro JSON-LD/SEO já nascer completo):** `slug(unique), title,
  excerpt, category, cover_url, cover_alt, cover_class(fallback p/ migração), body_md, toc(jsonb),
  status(rascunho|aprovado|publicado|arquivado), author, lang, tags(jsonb[]), reading_time, word_count,
  noindex, seo(meta_description, keyword_alvo, keywords[], og_image, og_title, og_description),
  imagens(jsonb: [{papel:cover|secao, url, origem:gerada|editada, prompt, alt}]),
  fonte(projeto|seo|tendencia|brief), published_at(=gate de agendamento), created/updated`. *(migração)*
- **`blog_redirect`** (`slug_antigo→slug_novo`): renomear post publicado sem 404/perder ranking (301).
- **`blog_pauta`** (B3): backlog de pautas é entidade própria (pauta→vira post), não `status` do post.
- **SEO de plataforma:** endpoints `/sitemap.xml` + `/feed.xml` (RSS) servidos pelo studio a partir de
  `published_at`/`updated_at`; JSON-LD `BlogPosting` montado no site com `author`/`datePublished`/`dateModified`/`image`.
- **Imagens** ficam no **MinIO/S3** (`s3_*` no `config.py`) com **URL pública permanente** (Caddy);
  `body_md`/`cover_url`/`og_image` referenciam essa URL.
- **Anti-mentira no redator (crítico):** cases vêm dos projetos reais do Perfil Mestre; prompt **proíbe
  métricas/clientes inventados** (mesma trava do freela — `[[perfil-mestre-estado]]`).
- **Loop de outcomes:** contar views/cliques no CTA (evento) p/ medir qual pauta converte (integra S2).

### 6.B 🟢 Agente de Blog (especialista) — DETALHADO (começar por aqui)
Pipeline espelha o padrão existente (analyzer `prompt_builder`+`parser` → service → coordenador como
`proposta_freela`), com **checkpoint humano**:
1. **Motor de pauta** — gera/ranqueia temas de 3 fontes: (a) **projetos feitos** (o studio já sabe o
   que o Pablo construiu → vira case/prova de competência), (b) **SEO/palavras-chave** (queries que
   PME/recrutador/cliente buscam no Google → intenção + volume + dificuldade), (c) **tendências**
   (IA/automação/dados). Saída: backlog de pautas com `keyword_alvo`, intenção (informacional/comercial),
   público-alvo (recrutador|cliente), estágio de funil.
2. **Briefing da pauta** — outline (TOC), keyword primária + secundárias, intenção de busca, CTA
   (serviço/contratar), tom Reative.
3. **Redator** — artigo completo em Markdown: título SEO, meta description, corpo com os headings do
   TOC, **links internos** (pras páginas `/servicos`), CTA. Voz do Pablo/Reative.
4. **Checklist SEO** (gate 0–100, anti-keyword-stuffing): keyword no título/H1/1º parágrafo/meta/slug,
   tamanho do texto, legibilidade, links internos, alt de imagem, meta description 150–160 chars.
   Espelha o checklist anti-genérico do freela.
5. **Imagens (Gemini)** — gera capa + imagens de seção via **Gemini** (Imagen 3/4 `:predict` p/
   qualidade, ou Gemini 2.x Flash Image `:generateContent` p/ inline/editável). Reusa a REST de Gemini
   que já existe. As imagens entram como **rascunho de asset**: ficam pra **Pablo baixar, editar fora
   e reenviar a versão final ANTES de publicar** (decisão dele 2026-06-20). Salvas no MinIO/S3.
6. **Checkpoint humano** — salva `rascunho` (texto + imagens geradas); Pablo revisa no studio (preview
   do markdown + score SEO + baixar/trocar imagens) → **Aprovar** vira `publicado` (seta
   `published_at`); o site pega no próximo ISR.
7. **(depois) Distribuição** — ao publicar, dispara o **agente LinkedIn** pra um post de divulgação
   linkando de volta (cross-agent via memória compartilhada, `alvo_tipo="blog"`).

**Fatias (cada uma = 1 commit testável):**
- [x] 🟢 **B0 — Cano ponta-a-ponta (linkagem) — FUNDAÇÃO COMPLETA (feito 2026-06-20, verde):**
  **Backend (studio):** modelo enriquecido `blog_post` + `blog_redirect` + migração `f3b9c1d4e7a2`; API
  **pública** `/api/public/blog` (list/get publicado, sem auth/CSRF, `Cache-Control`, 301 em slug
  renomeado) + `/sitemap.xml` + `/feed.xml`; `s3_storage.public_url` (URL permanente) + config
  (`s3_public_url`, `s3_bucket_blog`, `site_url`); smoke `tests/test_blog_public_api.py` (6 testes).
  **Site (`Reative Systems`):** client `lib/api/blog.ts` + camada `lib/blog/source.tsx` (API via ISR,
  fallback local), renderer Markdown (`react-markdown`+`remark-gfm`+`rehype-slug`+`rehype-highlight`,
  TOC casa via `github-slugger`), `cover_url`→`<img>` com fallback `coverClass`, página índice `/blog`,
  Blog de volta na home + item no menu, metadata/OG a partir do `seo`. Migração: `scripts/seed_blog.py`
  levou os 3 posts hardcoded pro banco. **Verificado:** `npm run build` com `NEXT_PUBLIC_API_URL`
  pré-renderiza os 3 posts do studio. **Falta só infra:** MinIO atrás do Caddy (§5.4) + `CORS_ORIGINS`
  prod (CORS é dispensável pro blog — fetch é server-side/ISR, não browser).
- [x] 🟢 **B1 — CRUD + UI no studio (feito 2026-06-20/21, build verde):** agente "Blog" no `registry.py`
  (`category="Reative Systems"`, order 19, ícone `ti-news`); API admin `/api/blog` (auth `blog.editar` —
  permissão nova no catálogo + seed) com CRUD + `PATCH /status` (publicar carimba `published_at`) +
  redirect 301 automático no rename; service `blog_service/admin.py` (slug único, métricas, gate);
  smoke `tests/test_blog_admin.py`. **Front:** `lib/api/blog.ts`+`hooks/useBlog.ts`+
  `components/blog/BlogScreen.tsx` (abas por status, lista com publicar/despublicar/apagar, editor
  Markdown + campos SEO com contador de meta description) ligado no `pages/agents/[slug].tsx`.
- [x] 🟢 **B2 — Redator + checklist SEO + checkpoint (feito 2026-06-21, verde — testado c/ Gemini real):**
  analyzer `analyzers/blog/redator` (prompt_builder+parser, **anti-mentira** ancorado no Perfil Mestre,
  espelha o redator do freela) → `body_md` completo; **checklist SEO determinístico**
  (`analyzers/blog/checklist_seo.py`, gate 0-100, **anti-keyword-stuffing** = densidade alta vira fail);
  service `blog_service/agente.py` (`redigir` PARA no rascunho/devolve pro editor; `checklist` puro);
  rotas admin `POST /api/blog/redigir` + `POST /api/blog/checklist`; smoke `tests/test_blog_seo.py`.
  **Front:** no editor da `BlogScreen`, "✨ Gerar com IA" (brief → preenche o form) + "Checar SEO"
  (painel com score + itens pendentes). Geração real rendeu artigo de ~1000 palavras, score 88.
- [x] 🟢 **B-IMG — Imagens (Gemini) (feito 2026-06-21, verde — testado c/ Imagen 4 real):** cliente
  `analyzers/gemini/image_client.py` (Imagen `:predict`, modelo `gemini_image_model` default
  `imagen-4.0-generate-001`) → `blog_service/imagens.py` sobe pro **MinIO com bucket de leitura pública**
  (`s3_storage.ensure_public_bucket` + `public_url` permanente) e grava em `imagens`/`cover_url`. Rotas
  `POST /api/blog/posts/{id}/imagem` (gera) e `/imagem/upload` (versão **editada** pelo Pablo via
  multipart). Front: `ImagensPanel` no editor (preview da capa + "✨ Gerar capa" + "Enviar imagem").
  *Decisão Pablo:* IA gera rascunho → baixar/editar fora/reenviar final antes de publicar. **Em prod:**
  expor o MinIO atrás do Caddy (§5.4) pra a URL pública abrir no domínio (em dev abre via localhost:9000).
- [x] 🟢 **B3 — Motor de pauta (feito 2026-06-21, verde — testado c/ Gemini real):** entidade própria
  `blog_pauta` (migração `a7c2e5f9b1d8`) + analyzer `analyzers/blog/pauta` (3 fontes: projeto/seo/
  tendência, ancorado no Perfil Mestre, com score 0-100) + `blog_service/pauta.py` (gerar com dedup +
  CRUD) + rotas `/api/blog/pautas*` + smoke `tests/test_blog_pauta.py`. **Front:** aba **Pautas** na
  `BlogScreen` (gerar c/ foco/sementes, lista por score, "Escrever" → abre o editor com o brief
  prefilled e marca a pauta como escrita ao salvar). Geração real rendeu 4 pautas ranqueadas das 3 fontes.
- [x] 🟢 **B4 — Coordenador (1 clique pauta→rascunho) + agendamento + cron (feito 2026-06-21, verde —
  testado c/ Gemini real):** `blog_service/coordenador.py` encadeia pauta → redator (B2) → post rascunho
  → liga a pauta (status escrita) — rota `POST /api/blog/pautas/{id}/escrever`; no front, "Escrever" virou
  **1-clique** (gera, salva e abre o rascunho pra revisão). **Agendamento:** `published_at` editável no
  editor (campo datetime-local) — o gate público já esconde data futura = calendário editorial enxuto.
  **Cron:** `jobs/blog_pautas.py` (semanal, top-up do backlog + aviso Telegram), guardado por
  `blog_pautas_cron_enabled` (default off), registrado no lifespan. Teste real: pauta→rascunho de ~1000
  palavras, SEO 92, pauta linkada.
- [ ] 🟢 **B5 — Cross-agent:** publicar → divulgação automática no LinkedIn (depende do §6.C).

> **Status (2026-06-21):** código B0–B4 + B-IMG + sugestão de capa **feito, testado e PUSHADO**
> (studio `feat/blog-agente-headless` → `prospector`; site `feat/blog-headless-b0` → `reative-site`).
> Falta só **ATIVAR** (infra/config), abaixo.

### 6.E ✅ ATIVAÇÃO LOCAL provada (2026-06-21) / ⏳ produção pendente
> **Causa raiz confirmada do "publiquei e não replicou":** o site não tinha `.env.local`, então usava o
> **fallback local** (`lib/content`) e nunca consultava o studio. **Resolvido em dev:** criado
> `Reative Systems/.env.local` com `NEXT_PUBLIC_API_URL=http://localhost:8000` (gitignored). Backend local
> (já rodava na :8000) verificado servindo `GET /api/public/blog/posts` (3 publicados, incl. 1 gerado por
> IA com capa), detalhe `[slug]`, `sitemap.xml`, `feed.xml` (todos 200) e a capa no MinIO (200 `image/png`,
> bucket público OK). **Falta só o usuário reiniciar o `npm run dev` do site** (env é lida no startup;
> limpar `.next` antes evita o `MODULE_NOT_FOUND` de build/dev misturados). **Produção** segue pelo
> checklist abaixo.
> Checklist na ordem (o item 1 é quase certo o motivo):
> 1. **`NEXT_PUBLIC_API_URL` no site** apontando pro studio (ex.: `https://studio.reativesystems.com.br`).
>    Sem isso o site usa o **fallback local** (`lib/content`) e ignora o banco. É **build-time** no Next:
>    setar a env **e rebuildar/redeployar** o site. (Em dev: `.env.local` + reiniciar `npm run dev`.)
> 2. **Studio acessível** publicamente e **`CORS_ORIGINS`** com o domínio do site (CORS não é estritamente
>    necessário pro fetch server-side/ISR, mas configurar evita dor no client-side).
> 3. **ISR**: a lista revalida a cada 300s e o post a cada 600s → pode levar até ~10 min; ou redeploy força.
> 4. **Gate de publicação**: o público só vê `status=publicado` **E** `published_at <= agora`. Se publicou
>    **agendado** (data futura), não aparece até a data. Conferir no editor.
> 5. **Imagens**: cobertura abre via URL do MinIO; em prod precisa do **MinIO atrás do Caddy** (§5.4) +
>    `S3_PUBLIC_URL`, senão a `cover_url` aponta pra `localhost:9000` e quebra.
> 6. **Deploy do backend**: rodar `python -m app.jobs.seed_admin` (permissão `blog.editar`); as 2 migrações
>    do blog (`blog_post`, `blog_pauta`) rodam no start do container.
> **Próximo passo recomendado:** abrir PR das 2 branches → deploy do studio → setar as 2 envs no site →
> rebuild do site → testar `GET https://studio.../api/public/blog/posts` e depois a página `/blog`.

### 6.C ⚪ Agente LinkedIn (próxima fase — esboço)
> Manter o LinkedIn ativo e atrair recrutador + serviço.
- ⚠️ **Restrição honesta:** publicar pela API oficial do LinkedIn exige app aprovado (Marketing/
  Community); auto-post "não-oficial" é frágil e arrisca ban. **Default:** o agente **gera rascunhos**
  (post + ideias de carrossel) numa fila + calendário; Pablo publica (copia/cola ou ferramenta de
  agendamento). Revisitar auto-post oficial se compensar o esforço de aprovação.
- **Conteúdo:** cada projeto/feature entregue e cada post de blog vira post de LinkedIn (hook + CTA);
  sugestões de otimização de perfil; pautas de engajamento.

### 6.D ⚪ Agente Docs-keeper (próxima fase — esboço)
> Manter a documentação do projeto sempre atualizada.
- **Gatilho:** roda no commit/PR (ou cron) → lê o `git diff` → detecta drift entre código e docs
  (`README`, `PLANO-MESTRE`, docs de arquitetura/API) → **propõe atualização como rascunho/PR** pra
  revisão (não edita direto sem checkpoint). Reusa o padrão MAS (memória + coordenador).

---

## 7. Como executar (lembrete)
1 fatia vertical = 1 commit testável (model → repo → service → schema → router → front), smoke/tsc/lint/ruff verdes entre cada. Deploy = `rsync` aditivo + `02-deploy.sh` (migração roda no start do container) — ver `[[deploy-vps-hetzner]]`. Sem trailer Co-Authored-By (`[[sem-co-author-commits]]`).

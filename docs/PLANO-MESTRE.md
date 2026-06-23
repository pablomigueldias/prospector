
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
| **Blog / Site (Reative Systems)** | ✅ **NO AR (2026-06-21)** | Agente de blog headless **completo e em produção** (studio ⇄ site Vercel ⇄ cdn de imagens); SEO completo. Detalhe em `BLOG_FEITO.md`. Falta **B5/LinkedIn** (§6.C) e **pendências** (§6.F: form de contato, custo na observabilidade). |
| **CRM** | ✅ completo | 5 seções (Empresas/Contatos/Negócios/Atividades/Projetos) fora do Notion, CRUD, filtros, pipeline+forecast, ficha 360, dashboard, edição inline, drawer, opções gerenciáveis. |
| **MAS (multi-agente)** | ✅ núcleo | Memória compartilhada (blackboard), coordenador (cadeia candidatura), outcomes, briefing noturno. Subiu a escada inteira do curso. |
| **Self-service (Parte 1)** | ✅ núcleo | Cockpit (S1), Observabilidade (S2), Configurações na UI (S3), Agendamentos (S4), Export/Backup (S8). Falta S5–S7. |
| **Finanças** | ✅ usável | Bot Telegram, contas/cartões/boletos, recorrências, orçamento, relatório. Backlog: **Dívidas/parcelamentos** (prioridade), Open Finance, NL queries. |
| **Auth** | ✅ | Login/sessão/RBAC (schema auth). Falta endurecimento (2FA obrigatório admin). |

> Detalhe do que **já saiu** vive nos `*_FEITO.md`. Este plano lista só o **caminho à frente** (+ contexto do que está pronto pra não repetir).

---

## 1. O caminho único (prioridades)

1. 🟢 **P5 — Reative Systems: Presença & Conteúdo** (2026-06-21): **agente de blog ✅ NO AR** → próximo: **LinkedIn** (B5/§6.C) → **Docs-keeper**. Pendências do site em §6.F. (§6 / `BLOG_FEITO.md`)
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
- [x] 🟢 **Editar currículo e carta na tela** (2026-06-22) — corrigir o gerado antes de baixar (sem regerar/gastar LLM): carta = textarea do corpo; CV = formulário estruturado. `PATCH /vagas/{id}/curriculo` e `PATCH /vagas/{id}/rascunhos/{email_id}`.
- [~] 🟢 **Polir UI do detalhe da vaga** — overflow corrigido (2026-06-22): coluna `1fr` do grid sem `min-w-0` deixava a URL longa estourar o card e a barra de etapas (`VagasScreen`). **Pendente:** revisar overflow/responsividade do detalhe inteiro (descrição longa, tags, salário) e em telas estreitas.

---

## 5. ⚪ P4 — Backlogs de manutenção

### 5.1 Self-service (Parte 1 restante)
- [ ] 🟡 **S5 — Prompt Studio** — mover prompts do código pra templates versionados (`config_app`/tabela própria) com variáveis, **preview** do prompt montado e **histórico/rollback**. Começar por 1 agente (candidatura ou vaga — casa com §4.1). *Pesado.*
- [~] 🟡 **S6 — Manuseio direto em todas as telas** — **drawer padronizado (2026-06-22):** `Modal`→`SidePanel`
  em **15 telas de CRUD** (CRM forms, Finanças forms/sections, Blog editor) pra "parecer um sistema só".
  Mantidos como `Modal` por design: confirmações de pagamento (Pagar/PagarMes/PagarRecorrencia),
  `ConfirmarExclusao`, busca global, extrato (leitura). **Falta:** reusar InlineCell/Timeline em Vaga e
  Freela (overlap §2.A).
- [ ] 🟡 **S7 — Opções dinâmicas além do CRM** — generalizar `OpcoesManager`/`crm_opcoes` pra status de vaga, estágios de freela, tags. *Médio: status de vaga é enum tipado hoje.*

### 5.2 MAS (multi-agente — núcleo feito)
- [ ] 🟡 **Ranking por `taxa_positiva`** — reordenar vagas/freela por probabilidade de retorno (quando houver histórico real de outcomes).
- [ ] 🟡 **Timeline (MAS-1) nas telas de Vaga/Freela** (hoje só no RecordModal do CRM) — overlap §2.E/§4.2.
- [ ] 🟢 **Normalizador de instituição** dos certificados (OCR às vezes erra: "IMPACTTA"→"IMPACTA").
- [ ] 🟢 **Cron do sync de certificados** (1×/dia → zero clique).

### 5.3 CRM (essencialmente completo)
- [ ] 🟡 **Integrar Copywriter + Outreach ao CRM** (PENDENTE — Pablo 2026-06-22): hoje são **agentes
  soltos na sidebar** e ficaram vagos/deslocados ali; o lugar deles é **dentro do CRM** (copy de
  prospecção + envio/follow-up agem sobre contatos/negócios). Decidir como unir (aba/ação no contato ou
  negócio) e tirar da lista de agentes. *Não fazer agora — só registrado.*
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

### 6.A–6.E — ✅ FEITO E EM PRODUÇÃO (ver `docs/BLOG_FEITO.md`)
> Agente de blog **completo e no ar** (2026-06-21): studio (API pública+admin) ⇄ site (Vercel, ISR) +
> cdn de imagens (`cdn.reativesystems.com.br`). Arquitetura, fatias **B0–B4 + B-IMG/+**, SEO completo,
> deploy de produção e bugs resolvidos → movidos pra **`docs/BLOG_FEITO.md`** (não inflar o plano).
> O que falta do blog está abaixo (B5) e em **§6.F** (pendências).

### 6.B — Falta no agente de blog
- [x] 🟢 **B5 — Cross-agent** (2026-06-22): publicar post de blog → rascunho de divulgação no LinkedIn
  (Página Reative), ligado por `origem_blog_post_id`. Determinístico (não trava/encarece a publicação),
  idempotente. Detalhe em §6.C (L3).


### 6.F ⏳ Pendências do site/blog (registradas 2026-06-21 — NÃO resolver agora)
- [ ] 🔴 **Formulário "Entrar em contato" do site não envia** — hoje o submit não vai pra lugar nenhum.
  Rotear pro **e-mail da empresa** (`contato@reativesystems.com.br`) — ex.: serverless do Vercel +
  Resend/SMTP, com confirmação pro usuário. O CTA de todo post já aponta pra `/#contato`, então isso
  **destrava o funil inteiro** do blog. (Pablo: prioridade quando for resolver.)
- [ ] 🟡 **Observabilidade não captura o CUSTO** das chamadas de IA (coluna $ = $0.00 na tela "Últimas
  chamadas") — falta a **tabela de preço por modelo** (gemini-2.5-pro, gemini-3-pro-image, flash…) →
  `tokens_input/output × preço`. É transversal (S2/observabilidade), aparece em todos os agentes.

### 6.C ✅ Agente LinkedIn (L0–L5 FEITOS — 2026-06-22)
> Manter o LinkedIn ativo e atrair recrutador + serviço. **Autônomo no sistema**
> (vai sozinho até o rascunho pronto na fila+calendário), mas **não auto-posta**.
> **Duas contas:** Página da Reative E perfil pessoal do Pablo (campo `conta`).
- ⚠️ **Restrição honesta:** publicar pela API oficial do LinkedIn exige app aprovado (Marketing/
  Community); auto-post "não-oficial" é frágil e arrisca ban. **Default:** o agente **gera rascunhos**
  (post + ideias de carrossel) numa fila + calendário; Pablo revisa, copia/cola e publica.
- **Conteúdo:** cada post de blog (cross-agent), cada projeto do Perfil Mestre e tendências do setor
  viram post (hook + corpo + CTA + hashtags), ancorado no Perfil Mestre (anti-mentira).
- [x] 🟢 **L0 — Cano ponta-a-ponta** (2026-06-22): modelo `linkedin_post` (conta/formato/hook/body/cta/
  hashtags/status/fonte/scheduled_for…) + migração + repo + service admin (CRUD + char_count +
  publicar) + schema + router `/api/linkedin` (perm `linkedin.editar`) + registry + tela
  `LinkedInScreen` **com SidePanel (drawer)** (abas por status, filtro por conta, preview "copiar pro
  LinkedIn", agendamento). Edição manual ponta-a-ponta funcionando.
- [x] 🟢 **L1 — Redator IA** (2026-06-22): `analyzers/linkedin/redator` (brief → hook/body/cta/hashtags,
  **sem Markdown**, anti-mentira ancorado no Perfil Mestre) com **voz por conta** (pessoal = 1ª pessoa/
  autoridade; reative = institucional). `POST /redigir` + botão "✍️ Escrever com IA" no drawer (preenche
  os campos, Pablo revisa). Testado c/ Gemini real nas duas vozes.
- [x] 🟢 **L2 — Coordenador autônomo** (2026-06-22): `linkedin_service/coordenador` gera **rascunhos
  prontos** sozinho — `gerar_de_projetos` (cada projeto do Perfil Mestre vira case) e
  `gerar_de_tendencias` (`analyzers/linkedin/temas` propõe N temas → redige cada, evita repetir o que já
  está na fila). `POST /gerar` + drawer "✨ Gerar com IA" (conta/fonte/qtd/público). Testado c/ Gemini.
- [x] 🟢 **L3 — Cross-agent** (= B5) (2026-06-22): `coordenador.do_blog` plugado em
  `blog_service.admin.mudar_status` (só na 1ª publicação, best-effort/try-except). Testado ponta-a-ponta
  + idempotência.
- [x] 🟢 **L4 — Cron + calendário editorial** (2026-06-22): `jobs/linkedin_posts.py` (off por default,
  `linkedin_cron_*`) mantém a fila de rascunhos cheia e **agenda `scheduled_for`** espaçado; aviso no
  Telegram; registrado no `main.py`. Front: toggle **Lista / 📅 Calendário** (agrupa por dia). Testado.
- [x] 🟢 **L5 — Direção de arte/mídia** (2026-06-22): `analyzers/linkedin/midia` (social media pro)
  recomenda a mídia ideal (foto/ilustração/carrossel/**vídeo-reel**/screenshot/gráfico) com
  **justificativa + roteiro passo a passo + dicas**; campos `midia`/`imagens` no modelo (migração
  `c1e8a4d7f3b2`). `POST /midia/sugerir` + `POST /imagem` (gera por IA via `image_client` Gemini → MinIO,
  bucket do blog). Front: seção "🎨 Direção de arte" no drawer + **preview fiel do feed do LinkedIn**
  (toggle Feed/Texto, avatar/nome por conta, imagem). Sugestão testada c/ Gemini; geração de imagem
  espelha o blog (em produção) — falta 1 teste com imagem real + MinIO.

### 6.D 🟡 Agente Docs-keeper + RAG do Second Brain (PRÓXIMO — visão Pablo 2026-06-22)
> **Visão do Pablo:** um agente que **aprende tudo sobre o sistema sozinho** e mantém a documentação
> **totalmente organizada** — pra ele não precisar re-explicar a mesma coisa toda hora e o sistema
> sempre progredir. Junto: um **RAG do "Second Brain"** (o conteúdo que ele estuda/anota) pra a IA
> **saber tudo que o Pablo sabe** e usar isso no **blog, no LinkedIn, no sistema, no site e no
> desenvolvimento pessoal** dele. Une o Docs-keeper com o "Segundo Cérebro (RAG)" do §3.4.

**Duas frentes que se reforçam:**
1. **Docs-keeper (documentação viva do sistema):** auto-aprende a arquitetura (lê código/`git diff`),
   detecta drift entre código e docs (`README`, `PLANO-MESTRE`, docs de arquitetura/API), e **propõe
   atualização como rascunho** (checkpoint humano, padrão MAS). Objetivo: documentação sempre atual =
   contexto pronto pros outros agentes (e pra mim) sem re-explicação.
2. **RAG do Second Brain (conhecimento do Pablo):** indexa as anotações/estudos dele (Second Brain) +
   projetos + certificados → vira **fonte de recuperação** que alimenta o redator do blog/LinkedIn
   (mais autêntico, ancorado no que ele REALMENTE sabe), o sistema e o site.

**Arquitetura (decisão travada):** o Postgres de produção **já é `pgvector/pgvector:pg16`** → embeddings
**no próprio Postgres (pgvector)**, sem serviço externo; gerar embeddings via **Gemini (cloud)** (sem GPU
no VPS — ver `[[deploy-vps-hetzner]]` e §3.4). Ingestão (upload/markdown/colar) → chunk → embed → busca por
similaridade → injeta no prompt dos agentes. *Para no rascunho* + *anti-mentira* continuam valendo.

---

## 7. Como executar (lembrete)
1 fatia vertical = 1 commit testável (model → repo → service → schema → router → front), smoke/tsc/lint/ruff verdes entre cada. Deploy = `rsync` aditivo + `02-deploy.sh` (migração roda no start do container) — ver `[[deploy-vps-hetzner]]`. Sem trailer Co-Authored-By (`[[sem-co-author-commits]]`).

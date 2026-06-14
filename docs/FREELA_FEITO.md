# O que já está pronto — Agente Freelancer (Workana)

Registro do que **já foi entregue** no agente `freela`, por fase (espelha o
plano do `docs/Workana.md`). O que **falta** está em `docs/MELHORIAS_FREELA.md`.

Última atualização: **2026-06-14**.

> O agente é um **copiloto**: a IA nunca toca na Workana nem envia proposta.
> Ele organiza (CRM), precifica e (nas fases de IA) rascunha — você revisa e
> envia na mão, e marca o status no painel. Vive na **área Pessoal** do
> Prospector (`category=Pessoal`, tabelas `pessoal_freela_*`).

---

## Fase 1 — Esqueleto + modelo de dados

- ✅ **4 models `pessoal_freela_*`** (2026-06-14) — `Plataforma`, `Cliente`,
  `Projeto`, `Proposta` em `app/db/models/pessoal/freela/`, no `Base.metadata`.
  Migration `20260614_1819_freela_agente_pessoal` (só as tabelas do freela; o
  drift pré-existente de `orcamentos`/`transacoes` foi removido do autogenerate
  de propósito). Índices em `projeto.cliente_id`, `proposta.projeto_id` e
  `proposta.status`.
- ✅ **Agente no catálogo** (2026-06-14) — `Agent(slug="freela",
  category="Pessoal", order=130)` em `app/api/registry.py`. Aparece no grupo
  Pessoal da sidebar junto de perfil-mestre/vagas/finanças.
- ✅ **Seed da plataforma Workana** (2026-06-14) — `scripts/seed_freela.py`
  (idempotente): faixas de comissão (20%/10%/5% por acúmulo do cliente) +
  custo de serviço 4,5% + lance mínimo R$760.

## Fase 2 — CRM manual + precificador (já útil, sem IA)

- ✅ **API `/api/pessoal/freela`** (2026-06-14) — protegida por
  `require_permission("pessoal.ver")`. Router `routers/freela.py` → service
  `services/pessoal/freela_service.py` → `repositories/pessoal/freela_repository.py`.
- ✅ **CRUD de Cliente** — com `ja_me_pagou_usd` (define a faixa de comissão).
- ✅ **CRUD de Projeto** — você **cola o texto** (`descricao`); lista é a "fila
  de oportunidades" ordenada por `fit_score` (vem do `analise_json`, Fase 3).
- ✅ **CRUD de Proposta** — nasce `rascunho`; `POST /propostas/{id}/status`
  move no Kanban, **carimba timestamp** (`enviada_em`/`data_resposta`/
  `data_fechamento`) e **registra evento** em `pipeline_events`
  (`freela_proposta_<status>`, `detalhe` = JSON com de/para).
- ✅ **Kanban** (`GET /kanban`) — propostas agrupadas pelos 7 status
  (rascunho→enviada→visualizada→respondida→negociando→fechada / perdida), com
  dias desde o envio.
- ✅ **Métricas** (`GET /metricas`) — taxa de resposta, taxa de fechamento,
  líquido total fechado e ticket médio.
- ✅ **Precificador** (`POST /precificar`) — **sem IA**: líquido desejado →
  `valor_a_cotar = liquido / (1 − comissão)`, com a comissão saindo da faixa do
  cliente (`ja_me_pagou_usd`) + `cliente_paga` (custo de serviço), checagem de
  lance mínimo e alerta de valor-hora. Smoke test bate com a tabela do
  `Workana.md` (cliente novo: cotar R$1750 → cliente paga R$1828,75; recorrente
  com US$500 pagos → 10%, cotar R$1555,56).

> **Verificado:** smoke test do service (round-trip no banco) verde; API sobe e
> expõe as 20 rotas em `/api/pessoal/freela/*` (401 sem auth, como esperado).

## Fase 6 — Tela do agente (painel)

- ✅ **`<FreelaScreen>` plugada no `[slug].tsx`** (2026-06-14) — slice de front
  completo: `lib/types/freela.ts`, `lib/api/freela.ts`, `hooks/useFreela.ts`,
  `components/FreelaScreen.tsx`; permissão `pessoal.ver` em `lib/permissions.ts`.
  Reusa o design system (`StatCard`, `.card`, `.btn-*`, `.input`, tokens OKLCH).
- ✅ **Métricas no topo** — `StatCard` de propostas, taxa de resposta, taxa de
  fechamento e líquido fechado (`GET /metricas`).
- ✅ **Precificador interativo** (Fase 4 no front) — "quero receber R$X" +
  cliente (ou US$ já pago) + horas/valor-hora → mostra comissão, valor a cotar,
  cliente paga, líquido/hora e alerta de lance mínimo (`POST /precificar`).
- ✅ **Fila de oportunidades** — colar projeto (form com orçamento/nº propostas)
  e lista ordenada por fit; cada card cria proposta inline (cotar/líquido/horas/
  prazo) ou é removido.
- ✅ **Kanban de propostas** — colunas pelos 7 status; mover por `select`
  (1 clique → `POST /status`, pede motivo se "perdida"), valor + dias desde o
  envio, remover. **Verificado:** typecheck e `npm run build` verdes.

> A partir daqui o agente é **usável pela tela** (não só Swagger). Falta a IA.

## Fase 3 — Analisador de projeto (IA)

- ✅ **`POST /projetos/{id}/analisar`** (2026-06-14) — cruza o texto colado +
  sinais do cliente com o `perfil-mestre` via `llm_provider` (Gemini→Groq→
  Ollama) e grava `analise_json`: `fit_score` (0–100), `recomendacao`
  (vale/talvez/evite), `veredito`, `requisitos`, `stack`, `red_flags`,
  `sinais_cliente` e `ganchos`. Analyzers em `app/analyzers/freela/analisador/`
  (prompt_builder + parser). Protege proposta escassa: diz onde vale gastar bala.
- ✅ **Regra anti-mentira** — `ganchos` só com o que ESTÁ no perfil (nada
  inventado), igual ao agente de candidatura.
- ✅ **Na tela** — botão "Analisar"/"Reanalisar" no card do projeto mostra a
  recomendação colorida + veredito + red flags + ganchos; a fila reordena por
  fit. Capabilities `analisa_projeto`/`precifica` ligadas no registry.
- ✅ **Verificado com LLM real** — exemplo WordPress/Salient do `Workana.md`
  (R$1.300–2.500, 64 propostas) retornou **fit 0 / "evite"** com red flags
  certeiras e ganchos vazios — exatamente o esperado.

## Fase 5 — Redator + Seletor de proposta (IA)

- ✅ **`POST /propostas/{id}/redigir`** (2026-06-14) — gera o rascunho da
  proposta ancorado no `perfil-mestre` (estrutura Workana: apresentação → plano
  → disponibilidade → prazo, citando um detalhe do projeto) e usa o
  `analise_json` (ganchos) do projeto. **Seletor**: escolhe até 3 projetos + 5
  habilidades do perfil. Analyzers em `app/analyzers/freela/redator/`.
- ✅ **PARA no rascunho** — grava `texto_enviado`/`projetos_destacados`/
  `habilidades_destacadas`/`prazo_proposto` na proposta; **nada é enviado**.
  Regra anti-mentira (só projetos/skills do perfil).
- ✅ **Na tela** — clicar no card do Kanban abre o **modal da proposta**:
  valores, destaques (chips), "Rascunhar com IA" (com instruções extra),
  textarea editável, **copiar** e salvar (PATCH). Também resolve o 🟢 "detalhe/
  edição da proposta" do backlog.
- ✅ **Verificado com LLM real** — projeto FastAPI/React/LLM (no núcleo do
  perfil) selecionou os 3 projetos certos (Prospector, Content Factory,
  Portfolio) e as 5 habilidades certas, com texto personalizado e persistido.

> 🎉 **Ciclo completo na tela:** colar → **analisar** (fit/red flags) →
> **precificar** → criar proposta → **rascunhar com IA** → revisar/copiar →
> mover no Kanban. Capability `rascunha_proposta` ligada.

## 🚀 Alavancas de desempenho (sessão 2026-06-14 noite)

- ✅ **Forecast de pipeline + meta mensal (§7)** — métricas ganham
  `pipeline_aberto_liquido` (soma do líquido das propostas em aberto),
  `forecast_liquido` (pipeline × taxa de fechamento) e `em_aberto`. Na tela, um
  painel mostra pipeline, previsão ponderada e uma **meta** (localStorage) com
  barra (fechado + previsto) e "faltam R$X". Dá visão de renda do que já está em
  jogo.
- ✅ **`ja_me_pagou_usd` sobe ao fechar (§9)** — ao fechar uma proposta pela 1ª
  vez (gate em `data_fechamento is None`, não duplica), soma o líquido convertido
  pra US$ (taxa `usd_brl` da plataforma, default 5,20) ao acumulado do cliente →
  a comissão cai de faixa sozinha e o precificador fica correto sem você lembrar.
  O evento registra `creditou_usd`.
- ✅ **Variações de abertura A/B (§8)** — o redator gera 2–3 primeiras linhas
  alternativas (ângulos diferentes: direta, com prova, com pergunta). No modal,
  painel "Aberturas alternativas (A/B)" — clicar troca a abertura preservando o
  corpo. A 1ª linha é o que decide se o cliente continua lendo.
- ✅ **Radar de cliente recorrente (§7)** — a fila marca projetos de clientes
  que já te pagaram (`ja_me_pagou_usd>0`) com badge "★ recorrente" e os ordena
  **primeiro** (comissão menor = mais líquido). "Cliente recorrente vale ouro."
- ✅ **Calibração: tempo de resposta + valor-hora real (§4/§9)** — métricas
  `tempo_medio_resposta_horas` (velocidade do cliente) e `valor_hora_real`
  (líquido/hora das fechadas → vê se está se subcobrando), num rodapé do painel.
- ✅ **Follow-up de propostas sem resposta (§10)** — job `freela_followup.py` na
  rotina diária (APScheduler): acha propostas "enviada" há ≥ N dias
  (`freela_followup_dias`, default 3) sem resposta e manda lembrete no Telegram
  pra dar follow-up **dentro da Workana** (não força contato fora).

---

## Ainda NÃO feito (resumo — detalhe e prioridade em MELHORIAS_FREELA.md)

- Fase 7 (segunda plataforma) e refinos de CRM (limite de propostas, drag-and-
  drop no Kanban, CRUD de cliente na tela). Mais alavancas em §7–§10 do backlog
  (win-rate por categoria, templates vencedores, follow-up, calibrador de
  valor-hora, etc.).

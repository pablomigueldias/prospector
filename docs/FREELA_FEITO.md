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

---

## Ainda NÃO feito (resumo — detalhe e prioridade em MELHORIAS_FREELA.md)

- Fase 3 (Analisador), Fase 4 (widget de precificação no front), Fase 5
  (Redator + Seletor com IA), Fase 6 (tela/painel Kanban no Next), Fase 7
  (segunda plataforma). **A tela ainda não existe** — hoje o agente é usável só
  via API/Swagger.

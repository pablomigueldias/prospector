# Agente Freelancer — Workana (e além)

> **Filosofia central:** isto é um **copiloto**, não um robô. A IA *nunca* envia
> proposta, *nunca* loga na Workana, *nunca* faz scraping da plataforma. Ela te
> ajuda a **decidir melhor, precificar melhor e escrever melhor** — e te dá um
> lugar único pra enxergar tudo que você mandou. Você cola o projeto, a IA te
> entrega o material, você revisa, **você envia na mão**, e marca no painel.

---

## 0. Por que esse formato (e por que ele cabe no seu ecossistema)

Você já tem o **Perfil Mestre** pra emprego CLT/PJ. Pensa neste aqui como o
**irmão freelancer** dele: mesma ideia de "fonte da verdade sobre quem eu sou e
o que eu já fiz", só que orientada a *fechar projeto pontual* em vez de *passar
numa vaga*.

Dois fatos da Workana que definem a estratégia do produto inteiro:

1. **Proposta é recurso escasso.** No plano grátis você manda pouquíssimas
   propostas por período. Isso muda tudo: o gargalo **não** é "mandar muitas",
   é **escolher certo e caprichar em cada uma**. Por isso o módulo mais valioso
   não é o redator — é o **priorizador** que te diz *onde vale gastar bala*.
2. **A comissão é escalonada por cliente** (começa em 20% e cai pra 10% depois
   de US$300 e 5% depois de US$3.000 acumulados com o *mesmo* cliente; o cliente
   ainda paga ~4,5% de "custo de serviço" por cima). Ou seja: **cliente
   recorrente vale ouro** e a precificação tem que embutir isso. O agente
   precisa saber se o cliente é novo ou já te pagou antes.

Esses dois fatos justificam a ferramenta inteira. Sem eles, "mandar proposta"
seria só copiar-colar.

---

## 1. Arquitetura — **mais um agente da área Pessoal do Prospector**

Isto **não é um repo novo**. É o irmão freelancer dos seus agentes pessoais
(`perfil-mestre`, `vagas`, `financas`) e mora **dentro do Prospector**, na
mesma área **Pessoal**, com as mesmas convenções. Você não monta
infraestrutura nenhuma — só adiciona um slice vertical.

| Camada | Como já é no Prospector | O que o freela reusa |
|---|---|---|
| Backend | FastAPI + SQLAlchemy 2.0 async + Alembic | mesma app, mesmas migrations |
| Banco | PostgreSQL 16 (no VPS) | mesmas migrations, tabelas com prefixo `pessoal_` |
| IA | `app.analyzers.llm_provider.gerar_texto()` — Gemini→Groq→Ollama com fallback | direto, sem novo provider |
| Frontend | Next.js (pages router) + Tailwind, design system OKLCH | `pages/agents/[slug].tsx` + um `<FreelaScreen>` |
| Observabilidade | tabelas `ai_call` e `pipeline_event` que você **já tem** | reusa as existentes — nada de `ai_calls`/`eventos` novos |
| Catálogo | `app/api/registry.py` com `category="Pessoal"` | só mais um `Agent(...)` na lista |
| Onde roda | **VPS (Hetzner)** — mesmo processo do Prospector | nada novo pra deployar |

**Separação Pessoal (inegociável, igual aos outros agentes):** tabelas com
prefixo `pessoal_` (aqui `pessoal_freela_*`), agente com `category="Pessoal"`
agrupado na sidebar, rotas e services no namespace pessoal. Nada toca em
`empresas`/`contatos`/Reative.

**Reaproveita o Perfil Mestre que já existe.** O doc original falava de um
"perfil mestre freelancer" em `.md` separado — esquece. Você já tem o agente
`perfil-mestre` (tabela `pessoal_perfil_mestre`): quem você é, projetos,
habilidades e tom de escrita. O redator e o seletor **consomem esse mesmo
perfil**, exatamente como o agente de `vagas` faz. Uma fonte da verdade só.

**Multi-plataforma** continua sendo **um campo `plataforma`** + um **adapter**
fino por site (hoje só `workana`; amanhã `99freelas`, `freelancer_com`). O
adapter só sabe (a) o *fluxo de proposta* e (b) os *campos* daquele site. A
inteligência (analisar / precificar / redigir / selecionar) é **compartilhada**
e vive nos analyzers.

Onde cada peça encaixa na árvore que já existe (`backend/`):

```
app/db/models/pessoal/freela/      # Plataforma, Projeto, Cliente, Proposta, Evento
                                   #   (todos no Base.metadata; tabelas pessoal_freela_*)
app/api/routers/freela.py          # rotas do agente
app/api/services/pessoal/freela_service.py   # CRUD + orquestração do ciclo
app/api/schemas/freela.py          # pydantic in/out
app/analyzers/freela/              # a inteligência, cada uma com prompt_builder + parser:
│   ├── analisador/                #   projeto colado -> requisitos + red flags + fit
│   ├── precificador/              #   líquido desejado -> valor a cotar (matemática da comissão)
│   ├── redator/                   #   rascunho ancorado no perfil-mestre que você já tem
│   └── seletor/                   #   quais 3 projetos + 5 habilidades destacar
app/api/registry.py                # + Agent(slug="freela", category="Pessoal", ...)
```

O adapter (comissão escalonada / lance mínimo / limite de propostas) entra como
módulo de domínio dentro do service — p.ex. `services/pessoal/freela_adapters/workana.py`.

---

## 2. Modelo de dados (o "CRM de propostas" que você pediu)

Isto é o coração do "quero ver todas as propostas, quais responderam, quais
fecharam". Todas as tabelas levam o prefixo `pessoal_freela_` (convenção da
área Pessoal) e entram no mesmo `Base.metadata`, com uma migration Alembic só.
Quatro tabelas próprias + reuso da `pipeline_event` que você já tem:

**`pessoal_freela_plataforma`** — `id`, `nome` (Workana…), `url_base`,
`config_comissao` (JSONB com as faixas), `lance_minimo_padrao`.

**`pessoal_freela_projeto`** (o projeto do cliente) — `id`, `plataforma_id`,
`cliente_id`, `titulo`, `descricao`, `url`, `faixa_orcamento_min/max`,
`habilidades` (array), `prazo_estimado`, `status_no_site` (analisando propostas
/ selecionado / fechado), `n_propostas_concorrentes`, `n_interessados`,
`coletado_em`, **`analise_json`** (JSONB — mesmo padrão do Prospector: dores,
fit score, red flags, ganchos).

**`pessoal_freela_cliente`** — `id`, `nome`, `rating`, `projetos_publicados`,
`projetos_pagos`, `pagamento_verificado` (bool), `membro_desde`,
**`ja_me_pagou_usd`** (acumulado — define a faixa de comissão!), `notas`.

**`pessoal_freela_proposta`** — `id`, `projeto_id`, `valor_cotado`,
`horas_estimadas`, `valor_liquido_estimado`, `texto_enviado`,
`projetos_destacados` (array de ids), `habilidades_destacadas` (array),
`prazo_proposto`, `enviada_em`, **`status`** (enum abaixo), `data_resposta`,
`data_fechamento`, `motivo_perda`.

**Observabilidade do ciclo de vida** — em vez de criar uma tabela `evento`
nova, **reusa a `pipeline_event` que o Prospector já tem**, gravando os tipos
`freela_proposta_criada / enviada / visualizada / respondida / negociando /
fechada / perdida` com o `payload` (JSONB) apontando pra `proposta_id`. Mesma
mesa de eventos dos outros agentes — um lugar só pra auditar o pipeline. (Toda
chamada de IA cai na `ai_call`, idem aos demais.)

### Ciclo de vida do `status` (vira as colunas do Kanban)

```
RASCUNHO → ENVIADA → VISUALIZADA → RESPONDIDA → NEGOCIANDO → FECHADA
                                              ↘ PERDIDA (com motivo)
```

Como a Workana não te avisa programaticamente quando o cliente vê/responde
(e você **não** quer automação), a transição é **você** que marca com 1 clique
no painel. Rápido e honesto.

---

## 3. Os quatro módulos de IA

### 3.1 Analisador de Projeto
**Entrada:** você cola o texto do projeto (copiar-colar manual da página).
**Saída (`analise_json`):**
- requisitos técnicos extraídos e normalizados,
- **fit score** contra o seu perfil (0–100) — "isso é a sua praia?",
- **red flags** ("orçamento incompatível com escopo", "cliente sem pagamento
  verificado", "64 propostas e 84 interessados = muito concorrido"),
- **sinais de qualidade do cliente** (verificado, nº de projetos pagos, rating),
- **ganchos** — o que desse projeto conversa com algo que você já fez.

No exemplo da sua captura (WordPress/Salient, R$1.300–2.500, 64 propostas): o
analisador deveria sinalizar *"projeto MUITO concorrido + é WordPress, fora do
seu núcleo React/Python → fit baixo, só vá se o preço compensar muito"*. Isso é
exatamente o tipo de decisão que economiza suas propostas escassas.

### 3.2 Precificador (com a matemática da comissão embutida)
A Workana te mostra três números (valor total, custo do serviço, "você vai
receber") mas não te ajuda a *chegar* neles. O precificador inverte a conta:
você diz **quanto quer receber líquido**, ele te diz **quanto cotar**.

Fórmula: `valor_a_cotar = liquido_desejado / (1 − comissao)`
A comissão vem do `cliente.ja_me_pagou_usd` (20% novo, 10% após US$300, 5% após
US$3.000).

Exemplo prático, cliente **novo** (comissão 20%), no projeto da sua captura:

| Você quer receber | Cotar (valor total) | Cliente paga (+4,5%) | Dentro da faixa R$1.300–2.500? |
|---|---|---|---|
| R$ 1.000 | R$ 1.250 | R$ 1.306 | ✅ |
| R$ 1.400 | R$ 1.750 | R$ 1.829 | ✅ |
| R$ 2.000 | R$ 2.500 | R$ 2.612 | no teto |

O precificador também cruza com **horas estimadas × seu valor-hora alvo** pra
você não cotar abaixo do que seu tempo vale, e respeita o **lance mínimo**
(R$760 na captura).

### 3.3 Redator de Proposta
Gera o rascunho seguindo a estrutura que a *própria Workana* recomenda na
lateral ("Apresente-se → Plano de trabalho → Disponibilidade → Prazo"):

- **ancorado nos seus projetos reais** (puxa do agente `perfil-mestre` que você
  já tem — `pessoal_perfil_mestre`), nunca genérico — é o oposto das 64
  propostas copia-cola que o cliente recebe;
- adapta o tom ao projeto (técnico vs. institucional);
- **regra anti-mentira** (mesma do seu agente de candidatura): reorganiza a
  verdade, nunca inventa experiência que você não tem;
- já sugere o **prazo** e referencia o "antes/depois" quando o projeto pede
  (no exemplo, o cliente valoriza prints de antes/depois — o redator lembra você
  disso).

### 3.4 Seletor
A tela de proposta deixa você destacar **até 5 habilidades** e **até 3 projetos**.
O seletor olha o projeto e recomenda *quais* — dentre os projetos/habilidades do
seu `perfil-mestre` — maximizam relevância.
Ex.: projeto React → destaca "Sistema de Captura de Leads (React)" e
"Dashboard"; projeto Python/dados → destaca o "Sistema de Gestão Financeira
(FastAPI)" e o churn prediction.

---

## 4. O fluxo de uma proposta (ponta a ponta)

```
1. Você acha um projeto na Workana e COLA o texto no painel
2. Analisador → fit score + red flags + sinais do cliente
3. Você decide: vale a pena? (a IA recomenda, você decide)
4. Precificador → faixa de preço (líquido que você quer ↔ valor a cotar)
5. Seletor → quais 3 projetos + 5 habilidades
6. Redator → rascunho da proposta
7. VOCÊ revisa, edita, deixa com a sua voz
8. VOCÊ envia na mão dentro da Workana
9. Você marca "ENVIADA" no painel (1 clique)
10. Depois, conforme o cliente reage, você atualiza o status
```

Em nenhum passo a IA toca na Workana. Ela é a sua mesa de trabalho.

---

## 5. A tela (o painel)

**Visão Kanban** (colunas = os status): você bate o olho e vê onde cada proposta
está. Cards mostram: cliente, valor cotado, líquido, dias desde o envio.

**Métricas no topo** (os números que dizem se você está melhorando):
- taxa de resposta (respondidas / enviadas),
- taxa de fechamento (fechadas / enviadas),
- ticket médio e **líquido total** já fechado,
- tempo médio até resposta.

**Fila de oportunidades** — projetos que você colou mas ainda não decidiu,
ordenados por fit score. É aqui que você protege suas propostas escassas.

A tela é só mais um caso no `pages/agents/[slug].tsx` (switch por slug, igual
`vagas` e `financas`), com um `<FreelaScreen>` em `components/`. Reusa direto o
design system: `StatCard` pras métricas, `.card` pros cards do Kanban,
`.btn-primary`/`.btn-ghost` nas ações, tokens OKLCH. Zero CSS novo.

---

## 6. Plano de construção (1 passo = 1 commit, testa entre cada)

> Como sempre no seu fluxo: cada passo é um commit, você testa antes de seguir.
> Aqui a ordem é pensada pra **entregar valor antes da IA** — você já consegue
> usar como CRM nas primeiras fases, mesmo sem nenhum modelo rodando.

**Fase 0 — Perfil mestre (você JÁ tem)**
- [ ] Nada de `.md` novo. Confere se o seu agente `perfil-mestre` cobre os
  projetos freelancer (problema/solução/stack/resultado) e habilidades; se
  faltar algo, completa lá. Essa é a fonte única que o redator e o seletor
  consultam — sem fonte paralela.

**Fase 1 — Slice no Prospector + modelo de dados**
- [ ] Registra o agente em `app/api/registry.py`: `Agent(slug="freela",
  name="Freela", category="Pessoal", status="active", order=130, ...)`.
- [ ] Models em `app/db/models/pessoal/freela/` (Plataforma, Cliente, Projeto,
  Proposta) + uma migration Alembic autogenerate (`pessoal_freela_*`).
- [ ] Seed do adapter `workana` (faixas de comissão, lance mínimo).

**Fase 2 — CRM manual (já é útil aqui!)**
- [ ] Router `freela.py` + `freela_service.py`: CRUD de propostas; tela Kanban
  no `[slug].tsx`/`<FreelaScreen>`.
- [ ] Marcar status com 1 clique (grava `pipeline_event`). **Pare aqui e use por
  uns dias** — você já ganha o "ver tudo num lugar" sem nenhuma IA.

**Fase 3 — Analisador**
- [ ] `app/analyzers/freela/analisador/` (prompt_builder + parser) chamando
  `llm_provider.gerar_texto()`; endpoint recebe texto colado → `analise_json`.
- [ ] Mostra o resultado na tela ao colar um projeto.

**Fase 4 — Precificador**
- [ ] Lógica de comissão no adapter `workana` + endpoint "líquido desejado → cotar".
- [ ] Widget de precificação na tela da proposta.

**Fase 5 — Redator + Seletor**
- [ ] Redator gera rascunho a partir do projeto + `perfil-mestre` (regra
  anti-mentira, igual ao agente de candidatura: reorganiza a verdade, nunca
  inventa). PARA no rascunho — você revisa e envia na mão.
- [ ] Seletor recomenda projetos/habilidades do perfil. Você sempre edita antes.

**Fase 6 — Polimento do painel**
- [ ] Métricas (taxa de resposta/fechamento, líquido total), fila por fit score.

**Fase 7 — Segunda plataforma**
- [ ] Cria `freela_adapters/99freelas.py` (ou outro). Prova que a abstração aguenta.

---

## 7. Fora do código — deixar o perfil atrativo e mostrar os projetos

A ferramenta acelera, mas quem fecha é o **perfil** + a **primeira avaliação**.
Coisas que não são código:

**Perfil Workana**
- **Headline específica**, não genérica: "Desenvolvedor Full-Stack · React/Next.js
  · Python/FastAPI · Automação e IA" — bate com o que você realmente faz.
- **Foto profissional** e **identidade verificada** (selo aumenta confiança).
- **Descrição** sai quase de graça do seu perfil mestre freelancer.
- **Portfólio dentro da Workana:** suba os MESMOS projetos que aparecem na tela
  de proposta (Gestão Financeira, Dashboard, Captura de Leads), cada um com
  **print/GIF + 1 parágrafo problema→solução→resultado**. Esses cards são o que
  o cliente clica.

**As primeiras avaliações (o ovo e a galinha)**
- A 1ª avaliação 5★ é a mais difícil e a mais valiosa. Estratégias: aceitar 1-2
  projetos menores/mais baratos no começo só pra cravar reputação; caprichar
  absurdamente na entrega desses; pedir a avaliação de forma natural ao entregar.

**Estratégia de proposta (o que a ferramenta potencializa)**
- **Velocidade importa:** projeto com 64 propostas — o cliente lê as primeiras
  com mais atenção. Responder cedo (com qualidade) ganha.
- **Específico vence genérico:** mencione um detalhe do projeto dele que ninguém
  mais mencionou (no exemplo: o bloco suspeito de "cassinos online" / possível
  spam injetado — citar isso prova que você LEU).
- **Proponha um plano**, não só um preço. O cliente do exemplo pediu
  diagnóstico + correção + testes no Safari iOS: estruture a proposta nesses
  passos.
- **Não force contato fora da plataforma** — a Workana penaliza, e a captura
  avisa isso explicitamente.

**O círculo de credibilidade**
- Perfil Workana → aponta pro seu **portfólio** (próximo `.md`) → aponta pro
  **GitHub** (repos pinados) → tudo coerente com o **LinkedIn**. Quem te acha
  num, confirma nos outros. É isso que faz o cliente escolher você entre 84
  interessados.

---

### Resumo em uma linha
Um CRM de propostas que vira copiloto: ele te diz **onde vale gastar proposta**,
**quanto cobrar pra receber o que você quer**, e **escreve um rascunho ancorado
nos seus projetos reais** — e você continua no comando de tudo.
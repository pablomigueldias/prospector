# Plano — De agentes isolados para um Sistema Multi-Agente (MAS)

> Origem: curso **"Como Criar Agentes de IA"** (Ricardo Vargas, LinkedIn Learning)
> aplicado ao **Prospector**. Notas em
> `/mnt/dados/Second-Brain/Pessoal/Como Criar Agentes de IA`.
> Data: 2026-06-17.

> **Princípio que mando do `plano.md`:** output primeiro, código depois. Cada fase
> abaixo é uma **fatia vertical = 1 commit**, testável, que já te entrega valor
> sozinha. Não precisa fazer tudo pra começar a usar.

---

# ⭐ PLANO DETALHADO DO MAS (atualizado 2026-06-18)

> Esta seção é a **fonte autoritativa** do estado atual. As seções 1–6 abaixo são
> a base derivada do curso (mantida como contexto). O CRM-fora-do-Notion **já foi
> concluído** (ver `docs/plano-crm-profissional.md` e `[[crm-sistema-proprio]]`),
> então o norte agora é de fato o **MAS**.

## A. Inventário real — o que você JÁ tem (mapeado no código)

| Peça do MAS | Estado | Onde, de verdade |
|---|---|---|
| **Agentes especializados** | ✅ forte | `app/analyzers/` (vaga, curriculo, candidatura, copywriter, freela, certificado, boleto, nlu) + os **services** que os chamam (`api/services/*`). Os services são os *pontos de entrada* reais de cada agente. |
| **Abstração de LLM** | ✅ | `analyzers/llm_provider.py` → `gerar_texto()` com fallback **Gemini → Groq** (e bloqueio diário quando Gemini estoura cota). É por aqui que qualquer agente fala com modelo. |
| **Observabilidade de IA** | ✅ | `db/models/ai_call.py` — toda chamada de LLM grava agente/operação/provider/modelo/tokens/custo/latência/sucesso. Já dá pra medir custo por cadeia. |
| **Telemetria de pipeline** | ✅ (mas ≠ memória) | `db/models/pipeline_event.py` = `pipeline_events`. **Correção importante:** os campos são `evento/status/detalhe/empresa_cnpj/duracao_ms` — é um **log técnico** (escrito por `db/observability.py` e `freela_service/propostas.py`), **NÃO** a memória por-alvo (`agente/alvo_id/payload`) que o plano antigo supôs. |
| **Agendador (autonomia)** | ✅ | APScheduler no `api/main.py` (`lifespan`) chama `jobs.lembretes.rotina_diaria` 1×/dia quando `settings.scheduler_enabled`. Jobs prontos: `freela_followup`, `lembretes`, `recorrencias`. |
| **Roteador de intenção** | 🟡 semente | `analyzers/nlu/` (`interpretar_llm`/`construir_prompt`/`parse_nlu`) — já roteia linguagem natural no bot do Financeiro. Reaproveitável como o "ouvido" do coordenador. |
| **Catálogo de agentes** | 🟡 só p/ UI | `api/registry.py` lista os agentes pro front; ninguém o usa pra *orquestrar*. |
| **Memória compartilhada por alvo** | ❌ | não existe. É o pré-requisito nº 1 do MAS. |
| **Coordenador** | ❌ | não existe `app/orchestrator/`. Cada service roda sozinho. |

**Resumo:** você tem **2,5 das 3 peças** (agentes ✅, infra de execução/telemetria ✅,
e meia peça de roteamento via NLU). Faltam as duas que dão o "eles se conversarem":
**memória compartilhada** e **coordenador**.

## B. Como os agentes vão CONVERSAR (a arquitetura)

Dois mecanismos complementares — é assim que MAS reais comunicam:

**1) Indireto — Blackboard (memória compartilhada).** Uma tabela única onde todo
agente **escreve fatos sobre um alvo** e **lê o que os outros já fizeram**. É o que
permite o agente B saber o que o agente A descobriu sem chamá-lo direto.

```
agente_evento  (nova tabela — NÃO mexer no pipeline_events de telemetria)
  id, agente, alvo_tipo (vaga|freela|empresa|negocio|contato|projeto),
  alvo_id, tipo (analise|gap|rascunho|outcome|nota…), payload JSONB,
  origem (manual|coordenador|cron), created_at
```

**2) Direto — Coordenador (orquestração).** Um agente que recebe uma **intenção** e
**encadeia** os agentes certos, passando contexto e parando em **checkpoints
humanos**. O handoff A→B é a conversa direta.

**Contrato de mensagem** (o "idioma" comum — `app/orchestrator/contratos.py`):
```
Tarefa      = {intent, alvo_tipo, alvo_id, contexto: dict, origem}
AgentResult = {agente, ok, resumo, dados: dict, eventos: list[Evento], sugestao_proxima?}
```
Cada agente orquestrável vira um **adapter fino** sobre o service que já existe,
devolvendo um `AgentResult` (e gravando `eventos` no blackboard).

**Fluxo (cadeia com checkpoint):**
```
intenção do Pablo
   │  (nlu interpreta → escolhe a cadeia)
   ▼
COORDENADOR ──▶ lê memória do alvo (blackboard)
   │
   ├─▶ agente A (ex: vaga.analisador)  ──▶ grava eventos (gap, match)
   │            │
   │     [CHECKPOINT humano: "vale aplicar?"]   ◀── regra de ouro: nada caro/externo sem OK
   │            │
   ├─▶ agente B (curriculo)  ──▶ grava rascunho
   ├─▶ agente C (candidatura)──▶ grava rascunho
   └─▶ entrega consolidada (CV+carta+checklist) + linha do tempo no alvo
```

## C. O que dá pra CONSTRUIR (cadeias candidatas)

Cada cadeia reusa services que já existem — é coordenação por cima, sem reescrever:

1. **Candidatura completa** (vagas): `vaga_service.analisar` → [checkpoint] →
   `curriculo` → `candidatura` → `checklist`. *(a do plano antigo — maior salto percebido)*
2. **Proposta de freela**: `freela_service.analise` → `precificador` →
   [checkpoint] → `propostas` (redator) → `checklist`.
3. **Lead → cliente** (CRM, fecha o ciclo agora que o CRM é a fonte): `prospector`
   (enriquece) → grava no CRM → `copywriter`/`outreach` (rascunho de abordagem) →
   cria `negocio` no estágio inicial → eventos na ficha 360.
4. **Briefing noturno** (autonomia): cron já existente roda o coordenador em modo
   proativo e monta o "Resumo da Noite" (vagas novas triadas, follow-ups vencendo,
   1 micro-ação) — entrega às 19h, **sem enviar nada** sozinho.

## D. Roadmap detalhado (fatias verticais, cada uma 1 commit)

### MAS-1 — Memória compartilhada (blackboard) — *o keystone* ✅ FEITO (2026-06-18)
- **Modelo+migração:** `db/models/agente_evento.py` (tabela `agente_eventos`:
  agente/alvo_tipo/alvo_id/tipo/resumo/payload JSONB/origem/created_at), migração
  `b7f2c9e14a05`. Separada da telemetria `pipeline_events`, como decidido.
- **Service:** `services/memoria_service.py` — `registrar(...)` (best-effort, não
  derruba o fluxo de quem chama), `criar(...)` (nota explícita) e
  `timeline(alvo_tipo, alvo_id)`.
- **Endpoint:** router `api/routers/memoria.py` → `GET /api/memoria/{alvo_tipo}/{alvo_id}`
  e `POST /api/memoria` (nota manual). Registrado no `main.py`.
- **Plugado (CRM, onde o Pablo vive hoje):** `crm_service.patch_record` grava
  evento `edicao` por edição inline; `mover_negocio_estagio` grava `estagio`. (Os
  pontos de vaga/freela e a escrita pelos próprios agentes entram junto do MAS-2.)
- **UI:** `components/crm/Timeline.tsx` plugado no `RecordModal` — linha do tempo do
  alvo + campo pra anotar. Pontinho por origem (agente/cron/manual).
- **Verificado:** edição inline e nota manual aparecem na timeline do alvo
  (ordenada por recência); ruff/tsc/lint verdes; rotas registradas.
- **Done ✅:** abrir uma empresa/negócio/contato/projeto/atividade mostra "o que já
  foi feito com ela".

### MAS-2 — Coordenador com 1 cadeia (candidatura completa) ✅ FEITO (2026-06-18)
- **Criado:** `app/orchestrator/candidatura.py` (cadeia) compondo os agentes que já
  existem via `vaga_service` (`analisar_vaga` → `gerar_curriculo` → `gerar_candidatura`
  → checklist determinístico). Schemas em `api/schemas/orchestrator.py`.
- **Checkpoint stateless** (sem token): 2 endpoints —
  `POST /api/orchestrator/candidatura/analisar` (fase 1, devolve aderência/veredito/
  gaps/recomenda) e `POST /api/orchestrator/candidatura/preparar` (fase 2, gera
  CV+carta+checklist). A UI gateia entre as duas = o checkpoint humano.
- **Conversa entre agentes:** cada passo grava na memória (MAS-1) com
  `origem="coordenador"` na timeline da vaga (tipo análise/curriculo/candidatura/
  checklist) — o que um agente faz fica visível pros próximos.
- **UI:** `components/vagas/CoordenadorCandidatura.tsx` no `VagaDetalhe` — botão
  "Preparar candidatura" → mostra match/gaps/veredito → "Continuar" → CV+carta+
  checklist (em `details` expansíveis). CV/carta também persistem como rascunho.
- **Verificado:** rotas registradas (179 totais), imports/ruff/tsc/lint verdes. (A
  cadeia LLM ao vivo não foi disparada aqui pra não gastar token; a composição
  reusa os services já testados.)
- **Done ✅:** 1 clique encadeia os agentes com você aprovando no meio.

### MAS-3 — Loop de aprendizado (outcomes) ✅ FUNDAÇÃO FEITA (2026-06-18)
- **Outcome = evento no blackboard:** `memoria_service.registrar_outcome(...)` grava
  `tipo="outcome"` com `payload={resultado, sinal}` (sinal +1/−1/0 via
  `_OUTCOME_SINAL`). Reusa 100% a tabela do MAS-1.
- **Agregação:** `resumo_outcomes()` → total, positivos/negativos, **taxa_positiva**,
  por_resultado, por_alvo_tipo. Endpoints: `POST /api/memoria/outcome`,
  `GET /api/memoria/outcomes/resumo` e `/outcomes/vocabulario` (declarados antes do
  `/{alvo_tipo}/{alvo_id}` pra não colidir).
- **UI:** seletor "Resultado…" no `Timeline` (marca o desfecho onde você já está; o
  pontinho fica verde/vermelho pelo sinal) + card **"O que tem dado retorno"** no
  Dashboard do CRM (taxa de retorno, contagens, breakdown por resultado).
- **Verificado:** registrar+resumo OK (taxa 50% no smoke); rotas ordenadas; tsc/lint/
  ruff verdes.
- **Falta (backlog):** usar a `taxa_positiva` pra **reordenar** vagas/freelas por
  "probabilidade de retorno" (precisa acumular histórico real antes de valer).

### MAS-4 — Autonomia supervisionada (briefing noturno) ✅ FEITO (2026-06-18)
- **Coordenador proativo:** `app/orchestrator/briefing.py` (`gerar()`) monta o
  "Resumo da Noite" agregando vagas a triar (sem análise), follow-ups de freela
  vencendo (≥ `freela_followup_dias`), atividades pendentes/atrasadas do CRM e
  **1 micro-ação** determinística. Não envia nada pra fora — só prepara.
- **Job + scheduler:** `jobs/briefing.py` (`rotina_briefing`) roda no APScheduler
  às `settings.briefing_hora` (default 18h) — gera, manda no Telegram e registra na
  memória (`alvo_tipo="briefing"`, origem="cron"). Settings: `briefing_enabled`,
  `briefing_hora`.
- **Sob demanda + UI:** `GET /api/orchestrator/briefing` + componente
  `components/crm/ResumoNoite.tsx` no topo do Dashboard do CRM (gera na hora, botão
  "Atualizar").
- **Verificado:** `gerar()` com dados reais (4 follow-ups, micro-ação escolhida);
  183 rotas; ruff/tsc/lint verdes.
- **Governança:** tudo que sai pra fora segue exigindo seu OK — o briefing só te
  cutuca.
- **Done ✅:** "Resumo da Noite" pronto automaticamente (cron) e on-demand (UI).

---

## 🏁 STATUS DO MAS (2026-06-18)
As **3 peças do MAS estão completas e realimentadas**: agentes especializados ✅ ·
memória compartilhada (MAS-1) ✅ · coordenador (MAS-2) ✅ · loop de outcomes (MAS-3) ✅ ·
autonomia/briefing (MAS-4) ✅. Subiu a escada inteira do curso (reativo →
deliberativo → aprendizado → colaborativo → autônomo supervisionado).

**Backlog priorizado:**
- Ranking de vagas/freela por `taxa_positiva` (MAS-3) — quando houver histórico.
- Replicar a cadeia do coordenador no **freela** (analise→precificador→propostas) e
  no **Lead→cliente** do CRM.
- Timeline (MAS-1) também nas telas de Vaga/Freela (hoje só no RecordModal do CRM).
- Normalizador de instituição dos certificados (OCR às vezes erra).

## E. Por onde começar (recomendação)
1. **MAS-1 (memória)** — é o keystone: destrava a conversa entre agentes e já
   entrega a linha do tempo (valor imediato na ficha do CRM/vaga).
2. **MAS-2 (coordenador, cadeia de candidatura)** — o maior "parece autônomo".
3. MAS-3 e MAS-4 viram backlog priorizado.

> ⚠️ **Decisão sua antes do MAS-1:** confirmar o nome/escopo da tabela de memória.
> Recomendo `agente_evento` **nova e separada** do `pipeline_events` (telemetria) —
> misturar os dois sujaria os dois propósitos.

---

## 1. O diagnóstico (o que o curso revelou)

Você sente que "falta autonomia entre os agentes". O curso dá o nome disso:
você tem **agentes generativos isolados**, não um **Sistema Multi-Agente (MAS)**.

Um MAS (módulo 18) precisa de **3 peças**:

1. **Agentes especializados** → ✅ você tem ~10 (`backend/app/analyzers/`).
2. **Memória compartilhada** → ❌ falta (mas a semente já existe:
   `db/models/pipeline_event.py` + `ai_call.py`).
3. **Agente coordenador** → ❌ falta (`api/registry.py` só lista pra UI; ninguém
   encadeia um agente no outro).

> 💡 Frase-chave do curso: *"a vantagem competitiva deixa de ser o poder de um
> modelo e passa a ser a inteligência da **coordenação** entre vários agentes."*

### A escada dos 5 tipos (módulo 04) aplicada a você

| Tipo | Estado no Prospector |
|---|---|
| **Reativo** (reage, sem memória) | ✅ é o que todos os analyzers são hoje |
| **Deliberativo** (planeja/simula) | 🟡 só o motor da meta R$10k (freela §V) |
| **Aprendizado** (melhora com feedback) | ❌ nenhum loop de outcome ainda |
| **Colaborativo** (coordena os outros) | ❌ **o vão que você percebeu** |
| **Autônomo** (roda fim-a-fim) | ❌ objetivo final |

O plano é **subir essa escada** sem refazer nada — reaproveitando os analyzers
que já funcionam.

---

## 1b. Norte imediato — CRM 100% no sistema (fora do Notion)

> Decisão do Pablo (2026-06-17): parar de usar o Notion e rodar o CRM inteiro
> aqui, com os agentes o mais autônomos possível.

**Onde estamos hoje (mapeado no código):**
- O Notion é a *"fonte de verdade pra negócio"* (`leads_reader.py` diz isso na
  cara). O `prospector_service` faz: monta o `Lead` → **envia pro Notion**
  (`NotionExporter.send_lead`) → grava no Postgres.
- Já existem os modelos locais do CRM: `db/models/{empresa,contato,socio,
  pipeline_event,email_outreach}.py`. Ou seja, **o dado já é espelhado no
  Postgres** — o Notion virou redundante, não insubstituível.

**Decisões (2026-06-17):** transição **dual-write** (Prospector segue gravando
Notion + Postgres até confiarmos), fonte = **importar do Notion**.

**Slices da Fase CRM:**
1. ✅ **FEITA — Migração Notion → Postgres** (keystone). `exporters/notion/
   importer.py` (reverso do exporter) + `scripts/migrar_notion.py`. Lê as bases de
   Empresas/Contatos, mapeia as propriedades reais (schema conferido ao vivo) e faz
   **upsert idempotente** (empresa por `notion_page_id`+CNPJ; contato por
   empresa+email/nome). **Resultado: 35 empresas, 66 contatos, 63 sócios, 64
   decisores** — com status, setor, análise IA nas notas, sócios. Idempotente
   (contagem estável no re-run). Notion intacto. Pula páginas vazias. *(De quebra:
   corrigido bug de vírgula faltando no `empresa_repository.upsert_by_cnpj`.)*
2. ✅ **FEITA — Telas de CRM no front.** API de leitura
   (`crm_service` + router `/api/crm`): `GET /empresas` (filtro status/busca,
   paginado), `/empresas/{id}` (detalhe com contatos+sócios), `/kanban`
   (agrupado por status), `/metricas`. Repo ganhou `listar/contar/listar_todas/
   find_by_notion_page_id`. Front: agente **"CRM"** no registry + `CrmScreen.tsx`
   (kanban por status, métricas, busca, modal de detalhe com contatos/decisores/
   sócios/notas). Verificado end-to-end via HTTP (35 empresas, 66 contatos, 64
   decisores). Rota: `/agents/crm`.
3. **Linha do tempo / memória `pipeline_event` (próximo):** atividades por
   empresa (aqui conecta com o MAS — `agente`/`alvo_tipo`/`alvo_id`).
4. **Inverter a escrita:** `NotionExporter` vira export *opcional* (flag), não
   etapa obrigatória. Desliga o dual-write quando você confiar.

> 💡 Por isso o CRM-fora-do-Notion e o MAS **convergem**: a tabela
> `pipeline_event` é, ao mesmo tempo, o histórico do CRM e a memória que dá
> autonomia aos agentes. Fazer a Fase CRM já entrega metade da Fase 1.

**Ordem sugerida agora:** Fase CRM (passos 1–2 primeiro: source of truth +
telas) → Fase 1 (memória) → Fase 2 (coordenador). As demais viram backlog.

---

## 2. Os 2 pilares (o que construir)

### Pilar A — Fonte Única de Verdade (módulos 16 e 05)
Tudo que os agentes leem/escrevem mora num lugar só, sem versões conflitantes.
Você **já tem** o pedaço mais importante: o **Perfil Mestre**. Falta:
- absorver os **27 certificados** (insumo factual — ver Fase 0);
- uma **memória de contexto** por alvo (vaga/freela/lead): o que já foi feito,
  qual o status, qual o último feedback. Hoje isso está espalhado.

### Pilar B — O Coordenador (módulo 18)
Um agente que recebe uma **intenção de alto nível** ("essa vaga vale a pena? me
prepara pra aplicar") e **encadeia os analyzers certos**, parando em
**checkpoints humanos** (o padrão do Caso Claude, módulo 15: analisar → mostrar →
confirmar → agir).

---

## 3. Roadmap por fases (cada uma = 1 fatia vertical)

### Fase 0 — Certificados na Fonte Única de Verdade ✅ FEITA (2026-06-17)
**Entregue:**
1. ✅ Campo `certificacoes: list[Certificacao]` no `PerfilMestreBase`
   (`Certificacao = {nome, tema, instituicao?, ano?, prova}`) + coluna JSONB
   `certificacoes` no `pessoal_perfil_mestre` (migração `c7e1a9d4f2b8`).
2. ✅ Os **27 certificados** carregados via `scripts/seed_certificacoes.py`
   (idempotente, merge não-destrutivo). Catálogo versionado na seção 5.
3. ✅ `_perfil_texto.py` renderiza as certificações → **todos os analyzers**
   (vaga, currículo, candidatura, freela) já as enxergam no prompt, sem tocar em
   cada um. Seção "Certificações" também na tela do Perfil Mestre (front).

**Verificado:** app 137 rotas · `perfil_para_texto` mostra as certificações ·
smoke `test_freela_plano_meta` 6/6 · `tsc`+`next lint` verdes.

#### Fase 0.1 — Ingestão AUTÔNOMA do Drive ✅ FEITA (2026-06-17)
O Pablo joga PDFs numa pasta pública do Drive e o sistema se atualiza sozinho —
sem digitar nada. Pipeline encadeado (já é um mini-MAS: collector → analyzer →
service):
1. **`collectors/drive/`** — lê a pasta pública (scrape, sem API key/OAuth):
   `listar_pasta_publica` (id+nome via `data-id`/`aria-label`) + `baixar_arquivo`.
2. **`analyzers/certificado/`** — manda cada PDF pro **Gemini multimodal**
   (mesmo padrão do boleto, sem OCR local) → JSON `{nome_curso, instituicao,
   carga_horaria, data_conclusao, tema, prova}`.
3. **`certificado_sync_service.sincronizar()`** — orquestra: lista → baixa →
   extrai → vira `Certificacao` → **merge idempotente** (chave = nome do
   arquivo). Rodar de novo só pega arquivos novos.
4. **Gatilhos:** botão "Sincronizar do Drive" na tela do Perfil + endpoint
   `POST /api/pessoal/perfil/certificados/sincronizar` + script
   `scripts/sync_certificados.py` (`--reset` troca placeholders por dados reais).
   Pasta configurável em `settings.certificados_drive_folder_id`.

**Resultado real (scan dos 27):** 27/27 com instituição, 24/27 com data, 25/27
com carga horária. (1 caiu por 503 transitório do Gemini e entrou no re-run —
prova da idempotência.) Ruído de OCR ocasional no emissor ("IMPACTTA"), editável
na tela.

**Próxima autonomia (backlog):** cron (`app/jobs/`) chamando o sync 1×/dia →
zero clique. Normalizador de instituição (canonicalizar "IMPACT A/IMPACTTA" →
"IMPACTA").

---

### Fase 1 — Memória Compartilhada (o "enxame com memória", módulo 18)
**O quê:** promover `pipeline_event` a **log de memória dos agentes**. Toda ação
de agente vira um evento (`agente`, `alvo_id`, `tipo`, `payload`, `ts`). Um
serviço `memoria_service` responde *"o que já fizemos com a vaga X?"*.

**Por quê:** é o que permite um agente saber o que o outro já fez — o pré-requisito
da coordenação. Sem isso, todo agente começa do zero (Reativo).

**Done quando:** abrir uma vaga/freela mostra a **linha do tempo** de tudo que os
agentes fizeram com ela.

---

### Fase 2 — O Coordenador (1 cadeia real primeiro)
**O quê:** novo slice `app/orchestrator/`. Um `coordenador` que executa **uma**
cadeia ponta a ponta, com checkpoint humano entre fases:

> **Cadeia "Candidatura completa":**
> vaga nova → `vaga.analisador` (match + gaps) → **[checkpoint: vale aplicar?]** →
> `curriculo` (CV sob medida) → `candidatura` (carta) → `checklist` → entrega
> pronta pra enviar.

**Padrão do prompt (Caso Claude, módulo 15):** o coordenador **mostra os achados
e pede confirmação** antes de gastar tokens nas etapas caras. Nada é enviado sem
seu OK — a "regra de ouro" do curso (supervisão humana, módulo 20).

**Por quê uma cadeia só:** prova o conceito sem reescrever o sistema. Depois
replica pro freela (analisador → redator → negociador).

**Done quando:** um clique em "Preparar candidatura" produz CV+carta+checklist
encadeados, com você aprovando no meio.

---

### Fase 3 — Loop de Aprendizado (Agente de Aprendizado, módulo 04)
**O quê:** capturar **outcomes** (proposta respondida? vaga virou entrevista?
cliente fechou?) e alimentar de volta o ranking/priorização. Começa simples:
um campo de resultado + um painel "o que tem dado retorno".

**Por quê:** transforma os agentes de ferramenta em **colaborador que melhora**.
Hoje você decide tudo no escuro; aqui o sistema aprende seu padrão de sucesso.

**Done quando:** o agente de Vagas/Freela ordena por "probabilidade de retorno"
baseada no seu histórico real, não só no match cru.

---

### Fase 4 — Autonomia supervisionada (o briefing noturno)
**O quê:** o coordenador roda **proativo** via os jobs que você já tem
(`jobs/freela_followup.py`, `jobs/lembretes.py`, `jobs/recorrencias.py`). Toda
noite, antes das 19h, ele prepara o **briefing** que o seu `plano.md` pede no bloco
"19:00 Abertura": vagas novas filtradas, propostas sugeridas, follow-ups vencendo,
1 micro-ação de LinkedIn.

**Por quê:** fecha o ciclo do curso (Agente Autônomo) **e** pluga direto na sua
rotina real. Você chega às 19h e o trabalho já está triado — você só decide e
envia.

**Governança (módulos 18 e 20):** autônomo ≠ sem supervisão. Tudo que **sai pra
fora** (e-mail, proposta) continua exigindo seu OK. O agente prepara; você aprova.

**Done quando:** existe um "Resumo da Noite" gerado automaticamente, pronto às 19h.

---

## 4. Como isso encaixa no que você já tem (sem retrabalho)

| Peça do plano | Reaproveita |
|---|---|
| Memória compartilhada | `db/models/pipeline_event.py`, `ai_call.py` |
| Coordenador | `api/registry.py` (vira fonte dos agentes orquestráveis) |
| Cadeias | os analyzers que já existem em `app/analyzers/` |
| Autonomia/cron | `app/jobs/*` (já rodam follow-up e lembretes) |
| Extrator de cert | padrão do `analyzers/boleto/extrator.py` |
| Fonte de verdade | `Perfil Mestre` (já está bem preenchido) |

> Nenhuma fase joga código fora. É **coordenação por cima** do que funciona.

---

## 5. Os 27 certificados (já catalogados — insumo da Fase 0)

Fonte: Drive público do Pablo. Agrupados por tema, com o que **provam** para o
perfil/vagas:

### Frontend / Web
- HTML5 · HTML5 (nano) · CSS3 · Frontend React + JavaScript · Do Figma ao código
  → **prova:** stack frontend React/JS/HTML/CSS + handoff design→código.

### Backend / Linguagens
- Python 3 (Mundo 1) · Python 3 (Mundo 2) · Introdução à lógica de programação ·
  Introdução à orientação a objetos
  → **prova:** Python + fundamentos sólidos de POO/lógica.

### Banco de Dados / Dados
- Criando sistemas de banco de dados · SQL Server 2016 — programação em T-SQL ·
  MongoDB (introdução) · Big Data — introdução e oportunidades
  → **prova:** SQL relacional + NoSQL + noção de Big Data.

### IA / Machine Learning
- Fundamentos de Machine Learning · Formação completa em Inteligência Artificial ·
  Fundamentos de IA e Chatbot com IBM Watson · Domine a IA com Gemini ·
  Prompting — Maximizar a IA no seu negócio ·
  **Como Criar Agentes de IA Avançado**
  → **prova:** IA aplicada, prompting, agentes — **diferencial direto** pra vagas
  de IA e pro próprio Prospector.

### Infra / Redes / Segurança
- Conceitos e infraestrutura de redes · SOC (Security Operations Center)
  → **prova:** base de redes + noção de segurança/SOC.

### Ferramentas / CRM (Zoho)
- Zoho CRM · Console do Administrador do Zoho Mail · Zoho Desk — primeiros passos ·
  Zoho Desk — atendimento omnichannel
  → **prova:** domínio da suíte Zoho (CRM/Desk/Mail) — casa com o lado CRM do
  Prospector e com vagas de implantação/suporte.

### Soft skills / Gestão
- Coaching para alta performance em TI · Liderança corporativa
  → **prova:** liderança e performance de times (histórias STAR comportamentais).

> **Decisão pendente (Fase 0):** esses 27 entram como novo campo `certificacoes`
> no Perfil Mestre, ou mapeados no `formacao` que já existe? Recomendo campo
> próprio — currículo e match conseguem tratar "certificação" diferente de
> "formação acadêmica".

---

## 6. Por onde começar HOJE

1. **Fase 0** — campo `certificacoes` + carregar os 27 (1 commit, ~1 noite de
   código no bloco das 21h05).
2. Depois **Fase 2** com **uma** cadeia (candidatura completa) — é a que mais
   "parece autônomo" e te dá o maior salto percebido.
3. Fases 1, 3 e 4 viram backlog priorizado (regra do `plano.md`).

> Lembrete do curso (módulo 20): a IA **não te substitui, te eleva**. Cada fase
> aqui tira de você o trabalho mundano (triar, formatar, encadeiar) e te deixa no
> que importa — decidir e se vender.

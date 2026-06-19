# Plano — Sistema self-service + novos agentes (dev/empreendedor)

> Objetivo do Pablo (2026-06-18): **operar tudo pela própria tela**, sem precisar
> pedir pro Claude pra mexer em config/prompt/agendamento, com visualização
> intuitiva — e ter **agentes que aumentem a produtividade** de quem é
> desenvolvedor E empreendedor.
>
> Princípio do projeto: *output primeiro, código depois*. Cada item abaixo é uma
> **fatia vertical = 1 commit** que já entrega valor sozinha.

---

## Parte 1 — "Tudo na minha tela" (autonomia operacional)

Mapeamento do que hoje te faz "pedir pro Claude" e a tela que resolve cada caso.

### S1 — Central de Agentes (cockpit) ✅ FEITO (2026-06-18)
**Dor:** os agentes vivem espalhados em `/agents/<slug>`; não há uma visão única do
que existe, do que está rodando e do que precisa de você.
**Tela:** uma home `/` (ou `/cockpit`) dirigida pelo `registry.py`: cards de todos os
agentes (ativo/em breve), o **Resumo da Noite** (MAS-4) no topo, e "o que precisa de
você hoje" (vagas a triar, follow-ups, atividades atrasadas) com link direto.
**Backend:** já existe (`registry`, `/orchestrator/briefing`). É montagem de front.
**Done:** abrir o sistema e ver, numa tela, tudo que importa + 1 clique pra agir.

**Entregue:** `components/cockpit/CockpitScreen.tsx` (eyebrow "Central de Agentes" +
saudação, `ResumoNoite` no topo = o que precisa de você hoje, grid de **agentes
ativos** clicáveis filtrados por permissão, e `MoreAgentsSection` pros próximos). A
home `pages/index.tsx` deixou de redirecionar pro prospector e agora renderiza o
cockpit no `DashboardLayout` — é onde o login pousa e onde o logo do menu aponta.
Reusa `useAgents`/`registry`, `ResumoNoite` (MAS-4) e `IconFromName`. Verificado:
`tsc` + `next lint` verdes.

### S2 — Observabilidade & Custos de IA ✅ FEITO (2026-06-18)
**Dor:** você não vê o que os agentes gastam nem o que falha — isso mora só no banco
(`ai_call`, `pipeline_events`).
**Tela:** `/observabilidade` — custo/tokens por agente e por dia, latência, taxa de
erro, últimas chamadas. Gráficos com Recharts (ver `[[grafico-recharts]]`).
**Backend:** endpoint de agregação sobre `ai_call` (provavelmente já há um router
`observability` — estender). 
**Done:** "quanto meu sistema gastou de IA esta semana e onde" numa tela.

**Entregue:** `observability_service.resumo(dias)` agrega `ai_calls` —
totais (chamadas/falhas/taxa_erro/tokens/custo/latência), **por agente**,
**série diária** (pros gráficos) e **últimas 20 chamadas**. Estendido o router
`observability` com `GET /api/observability/resumo?dias=N` (async, leitura via
`get_session`). Tela `/observabilidade`: seletor 7/30/90d, KPIs, `ComposedChart`
(barra custo + linha chamadas, cores oklch como o `RelatorioSection`), tabela por
agente e lista das últimas chamadas (pontinho verde/vermelho). Link no Sidebar
(substituiu o "Métricas" desabilitado). Verificado **live** no dev: $0.2552 / 80
chamadas / 6 agentes / 7 dias. `tsc`/`lint`/`ruff` verdes.

### S3 — Configurações na UI (sem mexer em `.env`/`config.py`) ✅ FEITO (2026-06-18)
**Dor:** ligar/desligar briefing, mudar a hora, trocar `llm_provider` (gemini/groq),
dias de follow-up… tudo isso é `settings` no código — só eu mexo hoje.
**Como:** tabela `config_app` (chave/valor/tipo) + `config_service` que faz override
das `settings` em runtime; tela `/configuracoes` com toggles/inputs por seção
(Agendador, Briefing, Freela, LLM, CRM). Mesmo padrão do `crm_opcoes` que já fizemos.
**Done:** você muda o comportamento do sistema na tela; reinício não é necessário.

**Entregue:** modelo `config_app` (só os overrides; migração `c4a9e7b21d68`) +
`config_service` com **catálogo curado** de 10 settings editáveis (Agendador,
Briefing, Freela, LLM, Orçamento) — segredos/infra ficam de fora de propósito.
`aplicar()` sobrescreve o singleton `settings` em runtime (rodado no topo do
`lifespan`, antes do scheduler) e a cada PATCH; quem lê `settings.x` em tempo de
chamada (followups, LLM, alertas) já vê o novo valor. O que afeta o *agendamento*
dos jobs (horas/scheduler) é marcado `requer_restart` e avisado na UI. Router
`/api/config` (GET/PATCH) gateado por `usuarios.gerenciar`; tela `/configuracoes`
(toggle/number/select, badge "alterado"/"restart", default, salvar/descartar) +
link no Sidebar (admin). Verificado e2e no DB de dev: atualizar→aplicar no
`settings`, listar reflete override, validação rejeita fora-de-range. `tsc`/`lint`/
`ruff` verdes. *(De quebra: corrigido o log `%sh` do agendador — loguru usa `{}`.)*

### S4 — Agendamentos na UI ✅ FEITO (2026-06-18)
**Dor:** os jobs (briefing 18h, lembretes 8h, follow-up) são fixos no `main.py`.
**Tela:** `/agendamentos` — lista os jobs, liga/desliga, muda o horário e **"rodar
agora"** (dispara o job on-demand). Lê/escreve via S3 (config_app).
**Done:** controlar a automação sem tocar em código.

**Entregue:** `agendamentos_service` com catálogo de jobs (Rotina diária =
recorrências+lembretes+follow-up freela @ `lembretes_hora`/`scheduler_enabled`;
Resumo da Noite @ `briefing_hora`/`briefing_enabled`) — `listar()` lê hora/estado
do `settings` e `rodar(id)` dispara o job na hora (reusa as funções já testadas
`rotina_diaria`/`rotina_briefing`). Router `/api/agendamentos` (GET + POST
`/{id}/rodar`) gateado por `usuarios.gerenciar`. Tela `/agendamentos` (card por
job: toggle, hora, "Rodar agora" com resultado em JSON) + link no Sidebar; o
liga/desliga e a hora gravam via `/api/config` (S3) e avisam que valem no próximo
restart. `tsc`/`lint`/`ruff` verdes; rotas no ar no dev (187 totais).

### S5 — Editor de Prompts (Prompt Studio)
**Dor:** os prompts dos agentes estão no código (`analyzers/*/prompt_builder.py`).
Ajustar tom/regra = me pedir.
**Como:** mover os prompts pra templates versionados em `config_app`/tabela própria,
com variáveis (`{perfil}`, `{vaga}`…). Tela pra editar + **pré-visualizar** o prompt
montado + histórico/rollback. (Começar por 1 agente — ex: candidatura.)
**Done:** você afina os prompts e vê o efeito sem deploy.

### S6 — Manuseio direto em todas as telas (padrão do CRM em todo lugar)
**Dor:** o CRM já tem edição inline + `SidePanel` (drawer) + `RecordModal` + Timeline.
Vaga/Freela/Perfil ainda usam formulários/telas antigas.
**Como:** reaproveitar `InlineCell`, `SidePanel`, `RecordModal` e `Timeline` nas telas
de Vaga e Freela (editar campo no lugar, drawer de detalhe, linha do tempo do alvo).
**Done:** a mesma fluidez "tipo Notion" em todo o sistema.

### S7 — Opções/那listas dinâmicas além do CRM
**Dor:** `crm_opcoes` resolveu os selects do CRM; vaga/freela ainda têm listas fixas.
**Como:** generalizar o `OpcoesManager` pra outros domínios (status de vaga, estágios
de freela, tags). Mesmo backend (`crm_opcoes` vira `opcoes` genérico).

### S8 — Export / Backup pela tela ✅ FEITO (2026-06-18)
**Dor:** dados só saem por script.
**Como:** botões "Exportar CSV" (empresas, contatos, negócios, vagas, transações) e
um "Backup agora" (dump JSON). Útil pra você levar dado pra fora quando quiser.

**Entregue:** `export_service` genérico (lê as colunas do próprio modelo
SQLAlchemy → linhas; serializa datetime/Decimal/UUID; JSONB vira JSON no CSV) pros
5 recursos. Router `/api/export` (`/csv/{recurso}`, `/backup`, `/recursos`)
gateado por `usuarios.gerenciar`. Tela `/exportar` com botões por recurso +
"Backup agora" (download autenticado via fetch+blob com `credentials:'include'`) +
link no Sidebar. Verificado contra o dev: empresas 36 / contatos 66 / vagas 13 /
transações 140; CSV 119 KB. `tsc`/`lint`/`ruff` verdes.

---

## Parte 2 — Novos agentes (produtividade de dev + empreendedor)

Cada ideia encaixa na arquitetura que já existe (analyzer/collector → service →
memória/coordenador), então é evolução, não reescrita.

### Marca & captação (você vende)
- **🪶 Agente de Conteúdo (LinkedIn/X):** transforma o que você FEZ (commits,
  projetos, certificados, cases do CRM) em posts/threads + um **calendário
  editorial**. Presença vira lead. *(reusa Perfil Mestre + copywriter.)*
- **🔎 Agente Radar de Oportunidades:** monitora fontes (vagas/freelas/editais) e
  **injeta no funil** automaticamente, já com match score. *(collectors já existem:
  duckduckgo/website; pluga no agente Vagas/Freela.)*
- **🧲 Agente Outbound:** dado um ICP (perfil de cliente ideal), acha empresas +
  decisores e gera a 1ª abordagem. *(o Prospector + copywriter já são a base.)*

### Comercial & operação (você fecha e entrega)
- **📄 Agente de Propostas Comerciais:** de um briefing → escopo + preço + prazo +
  **PDF** pronto. *(freela já tem precificador; estende pro CRM/negócios.)*
- **🤝 Agente de Onboarding de Cliente** *(já "soon" no registry)*: quando um negócio
  vira "ganho", cria o projeto, manda o e-mail de boas-vindas e o checklist inicial.
- **💸 Agente de Cobrança** *(já "soon")*: régua de cobrança a partir de
  projetos/faturas (lembrete gentil → firme), tudo com seu OK.
- **🗣️ Agente Reunião → Ação:** cola a transcrição/nota da call → vira atividades no
  CRM + follow-ups agendados.

### Engenharia (você constrói)
- **👀 Agente de Code Review / PR:** resume o diff, aponta riscos e sugere testes.
  *(este projeto já tem `/code-review`; um agente interno faria isso pros seus repos.)*
- **📚 Agente de Documentação:** gera/atualiza README, changelog e docs a partir do
  repo.
- **🧪 Agente de Testes:** propõe casos de teste pros pontos sem cobertura.

### Cérebro & decisão (você pensa melhor)
- **🧠 Segundo Cérebro (RAG):** indexa seu Second-Brain, certificados, projetos e
  docs → responde perguntas e vira **insumo de todos os outros agentes**. É o
  multiplicador. *(encaixa no Pilar "Fonte Única" do plano MAS.)*
- **🧭 Agente de Roadmap/Backlog:** pega ideias soltas (inclusive conversas como esta)
  e devolve um backlog priorizado por **impacto × esforço**.
- **📈 Agente Financeiro Estratégico:** sobre o Organizador, projeta **runway**,
  sugere preço/meta e alerta desvio. *(reusa `financas`.)*
- **🎛️ Comando por linguagem natural:** uma barra "faça X" que usa o `nlu` (já existe)
  pra rotear pro agente/cadeia certa — o coordenador (MAS-2) com porta de entrada
  conversacional.

---

## Ordem sugerida (valor × esforço)
1. **S1 Cockpit** (puro front, junta o que já existe) — sensação imediata de controle.
2. **S3 Configurações na UI** (+ S4 Agendamentos) — o verdadeiro "sem pedir pro Claude".
3. **S2 Observabilidade** — confiança (custo/erros à vista).
4. **🧠 Segundo Cérebro (RAG)** — o agente que potencializa todos os outros.
5. **🪶 Conteúdo** ou **📄 Propostas** — o que mais devolve dinheiro/visibilidade.
6. Demais agentes e S5–S8 como backlog priorizado.

> Regra de ouro mantida (MAS): autonomia **com** supervisão — o que sai pra fora
> (e-mail, post, proposta, cobrança) sempre passa pelo seu OK.

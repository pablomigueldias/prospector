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

## 0. Estado atual (snapshot — 2026-06-18)

| Módulo | Estado | Resumo |
|---|---|---|
| **Vagas** | ✅ bom | CRUD por JD, analisar (match/gaps/veredito), candidatura, currículo ATS, pipeline, funil, plano-de-gaps. *Pablo: "só falta lapidar o modelo de IA".* |
| **Freela** | 🟡 **avançando** | Era o grande buraco. **Sessão 2026-06-19:** gestão na tela (CRUD cliente, edição inline na fila, motivo de perda dinâmico) + cold start (projeto fresco, "bom 1º projeto", veredito `momento` com capacidade/anti-furada, "onde insistir"). **Falta:** A/B por ângulo, custo de oportunidade, mais autonomia (cadeia coordenador — WIP `proposta_freela`), dnd no Kanban. |
| **CRM** | ✅ completo | 5 seções (Empresas/Contatos/Negócios/Atividades/Projetos) fora do Notion, CRUD, filtros, pipeline+forecast, ficha 360, dashboard, edição inline, drawer, opções gerenciáveis. |
| **MAS (multi-agente)** | ✅ núcleo | Memória compartilhada (blackboard), coordenador (cadeia candidatura), outcomes, briefing noturno. Subiu a escada inteira do curso. |
| **Self-service (Parte 1)** | ✅ núcleo | Cockpit (S1), Observabilidade (S2), Configurações na UI (S3), Agendamentos (S4), Export/Backup (S8). Falta S5–S7. |
| **Finanças** | ✅ usável | Bot Telegram, contas/cartões/boletos, recorrências, orçamento, relatório. Backlog: **Dívidas/parcelamentos** (prioridade), Open Finance, NL queries. |
| **Auth** | ✅ | Login/sessão/RBAC (schema auth). Falta endurecimento (2FA obrigatório admin). |

> Detalhe do que **já saiu** vive nos `*_FEITO.md`. Este plano lista só o **caminho à frente** (+ contexto do que está pronto pra não repetir).

---

## 1. O caminho único (prioridades)

1. 🔴 **P1 — Freela**: virar de "monte de features soltas" em **agente especializado + gestão total na tela + autonomia**. (§2)
2. 🟡 **P2 — Novos agentes** de captação/comercial: **Propostas Comerciais, Radar de Oportunidades, Outbound**. (§3)
3. 🟢 **P3 — Vagas**: **lapidar o modelo de IA** (+ backlog de conveniência). (§4)
4. ⚪ **P4 — Backlogs de manutenção**: self-service S5–S7, MAS, CRM, Finanças, infra. (§5)

---

## 2. 🔴 P1 — FREELA (prioridade máxima)

> **Diagnóstico do Pablo (2026-06):** *"O freela está péssimo pra mim, não está bom
> ainda. Falta muita coisa — precisa de agente especializado, gestão melhor pra eu
> manipular tudo na tela, e mais autonomia."* O analisador já cospe dado, mas vem
> **solto e genérico**, a tela não deixa manusear tudo, e o fluxo não encadeia
> sozinho. As 4 frentes abaixo resolvem isso. Meta-bússola: **R$10k líquido/mês**.

### 2.A — Gestão TOTAL na tela (manipular tudo, estilo CRM) 🔴 NOVO
> O CRM já tem o padrão "tipo Notion" (edição inline, drawer lateral, CRUD completo).
> O freela ainda usa telas/forms antigos. Trazer a mesma fluidez.
- [x] ✅ **Reusar `InlineCell` + `SidePanel`** — `InlineCell` generalizado (prop
  `onSave`, CRM intocado) na fila (orçamento/nº concorrentes/publicado); **`ProjetoDrawer`**
  (SidePanel): clicar no projeto abre o detalhe 360 com o **porquê da decisão** (momento,
  fit, risco, quadrante, preço, frescor, concorrência, bom 1º projeto), **todos os campos
  editáveis** e a análise (tarefas/perguntas/skills/red flags/ganchos). *RecordModal não
  reusado: a proposta já tem `PropostaModal` rico.*
- [x] ✅ **CRUD de cliente na tela** — seção "Clientes" + drawer criar/editar/excluir.
- [~] 🟡 **Opções dinâmicas** — **motivo de perda** feito (`OpcoesManager` generalizado
  com prop `grupos`, grupo `freela_motivo_perda`; diálogo no lugar do `window.prompt`).
  **Falta:** estágios de proposta e tags.
- [ ] 🟢 **Drag-and-drop no Kanban** (hoje move por `select`; pede dnd-kit).

### 2.B — Análise PROFUNDA (acabar com a "análise vaga") — V.1
> *"É difícil? é rápido? o preço tá justo? o que vai dar trabalho?"* sem reinterpretar.
- [x] ✅ Quadrante **dificuldade × esforço** (`complexidade_tecnica`/`clareza_escopo` → quick_win/dificil_longo/escopo_vago/padrao), selo na fila e na análise.
- [x] ✅ **Veredito de preço** determinístico (orçamento × faixa de mercado → subcotado/justo/acima + R$/h efetivo).
- [x] ✅ **Breakdown do escopo** (`tarefas`+horas, `perguntas_cliente`, `skills_faltando`).
- [~] 🟡 **Extrair TODA a info da proposta.** Já puxa skills exigidas + nº de interessados. **Falta:** dados do **cliente** (país, pagamento verificado, nº de projetos, rating, idioma) auto-preenchendo um `Cliente`; **data de publicação** (frescor); **tipo de contrato** (fixo/hora) como colunas do projeto. *(precisa migração/fluxo de Cliente.)*
- [ ] 🟡 **Nota de confiança da análise** (`alta/média/baixa`) — quando o texto colado é pobre, a IA pede o que falta em vez de fingir certeza.

### 2.C — "É o MOMENTO pra mim?" — timing e custo de oportunidade — V.2
> Não *"o projeto é bom?"* e sim *"é bom **pra mim, agora**, dada minha fase e agenda?"*.
- [x] ✅ **Veredito de timing pessoal** — campo `momento` (`agora/espere/passe`)
  determinístico: fit/risco + frescor + concorrência + "bom 1º projeto" + **capacidade
  livre** (anti-furada já entra na conta). Selo na fila com motivo.
- [x] ✅ **Capacidade / agenda (anti-furada)** — capacidade/semana via `config_app`
  (`freela_capacidade_horas_semana`, editável na tela de Config), comprometidas = horas
  das fechadas, `GET /capacidade` + card; `momento` vira "espere — sem mão essa semana".
  *Backlog: comprometidas só conta `fechada` (não há tracking de entrega/prazo ainda).*
- [ ] 🟡 **Custo de oportunidade — ranquear a fila por valor esperado** = `ticket × prob. resposta × fit ÷ horas`. Mostra onde a próxima proposta rende mais.

### 2.D — MOTOR DA META (R$10k/mês como bússola) — V.3
> Premissas do Pablo: **R$10k líquido/mês**, **5h/dia** (~90h faturáveis/mês), meta **em rampa**. Matemática reversa: ~90h ⇒ exige **R$/h efetivo ~R$110–120** ⇒ *não dá pra bater empilhando projeto barato* — depende de ticket/nicho/gringo.
>
> **Rampa:** F1 cold start (1–2 notas 5★, ~R$1,5–2k) → F2 tração (~R$4k) → F3 crescimento (~R$7k, recorrente/USD) → F4 meta cheia (R$10k).
- [x] ✅ **Matemática reversa** (`POST /freela/meta/plano` → valor-hora alvo, projetos/mês, propostas/semana, gargalo).
- [x] ✅ **Valor-hora alvo vs real** (pinta vermelho quando abaixo).
- [x] ✅ **Estratégia por fase** (rampa F1–F4 pela reputação).
- [~] 🟡 **Painel da meta com "plano da semana".** Já mostra o ritmo necessário. **Falta:** progresso real vs ritmo (no caminho/atrás/na frente) no mês corrente.

### 2.E — Mais AUTONOMIA (encadear sozinho) 🔴 NOVO
> Hoje cada passo é manual. Replicar a cadeia do coordenador (MAS-2) no freela.
- [ ] 🔴 **Cadeia coordenador "Proposta de freela"**: `freela_service.analise` → `precificador` → **[checkpoint humano]** → `propostas` (redator) → `checklist`. Grava eventos na memória (blackboard) por proposta. Espelha a cadeia de candidatura que já existe.
- [ ] 🟡 **Timeline (MAS-1) na tela de proposta/projeto** — hoje só no RecordModal do CRM. Mostra o que os agentes já fizeram com aquele alvo.
- [ ] 🟡 **Evento de proposta com payload estruturado** — tabela `pessoal_freela_evento` (`proposta_id`+`payload` JSONB) p/ timeline rica (hoje reusa `pipeline_events`, sem JSONB).

### 2.F — Cold start / decidir onde gastar a proposta (§0 do plano antigo)
> Fase atual: **muitas propostas, ainda 0 cliente** → métrica que importa é **taxa de resposta**. Workana Prime (sem limite de proposta).
- [x] ✅ Modo cold start no redator (prova por descrição, sem link externo, redução de risco).
- [x] ✅ Checklist anti-genérico (gate 0–100 + varredura de contato/link p/ conformidade Workana).
- [x] ✅ Painel adaptativo focado em resposta (Em conversa / Tempo até resposta).
- [x] ✅ **Velocidade — "projeto fresco" em destaque** — coluna `publicado_em` (migração), selo 🆕 + edição inline da data, fila ordena por novo + pouco concorrido.
- [x] ✅ **Detector de "bom 1º projeto"** — selo determinístico: pagamento verificado (pré-req) + 3 de 4 (fit alto, pouca concorrência, escopo enxuto, orçamento saudável); sobe no ranking.
- [ ] 🟡 **A/B real por ângulo de abertura** — registrar qual ângulo (direto/prova/pergunta) foi usado e cruzar com quem respondeu.
- [x] ✅ **Taxa de resposta por categoria/stack** — painel "Onde insistir" (`GET /metricas/por-stack`). ⚠️ depende de normalizar os stacks (hoje verbosos demais — ver [[freela-stack-verboso]]).

### 2.G — Alavancas de desempenho (§7–§10 do plano antigo)
- [ ] 🟡 **Win-rate por categoria** (usa `analise_json.stack`) → "gaste proposta aqui".
- [ ] 🟡 **Banco de propostas vencedoras** — proposta que fecha vira "modelo" p/ o redator se inspirar.
- [ ] 🟡 **Alerta de orçamento incompatível** no precificar (estoura/abaixo da faixa).
- [ ] 🟡 **Gringo/USD & recorrente como peso** no motor da meta (multimoeda + radar recorrente já existem).
- [ ] 🟢 **Multimoeda USD↔BRL**, **motivo de perda estruturado**, **histórico de precificações**, **acompanhar prazo de entrega**, **relatório mensal do freela** (Recharts), **dedup do follow-up**, **adapter 99freelas**.

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
- [ ] 🔴 **Importar vaga por URL** (auto-preencher via collector website + analyzer `vaga_extracao`; fallback: colar texto).
- [ ] 🔴 **Follow-up / lembretes** (`candidatei_em`/`proximo_followup_em`; agendador varre e avisa no Telegram; gerar follow-up rascunho). *(migração)*
- [ ] 🟡 **Prep de entrevista** (status=entrevista → perguntas técnicas+STAR+perguntas pra fazer+pontos fracos; analyzer `entrevista`).
- [x] ✅ **Plano de ação pros gaps** (painel "O que estudar" + `plano_gaps` por vaga).
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
- [x] ✅ S1 Cockpit · S2 Observabilidade · S3 Configurações · S4 Agendamentos · S8 Export/Backup.

### 5.2 MAS (multi-agente — núcleo feito)
- [ ] 🟡 **Ranking por `taxa_positiva`** — reordenar vagas/freela por probabilidade de retorno (quando houver histórico real de outcomes).
- [ ] 🟡 **Timeline (MAS-1) nas telas de Vaga/Freela** (hoje só no RecordModal do CRM) — overlap §2.E/§4.2.
- [ ] 🟢 **Normalizador de instituição** dos certificados (OCR às vezes erra: "IMPACTTA"→"IMPACTA").
- [ ] 🟢 **Cron do sync de certificados** (1×/dia → zero clique).

### 5.3 CRM (essencialmente completo)
- [x] ✅ Export CSV (entregue como S8).
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

## 6. Como executar (lembrete)
1 fatia vertical = 1 commit testável (model → repo → service → schema → router → front), smoke/tsc/lint/ruff verdes entre cada. Deploy = `rsync` aditivo + `02-deploy.sh` (migração roda no start do container) — ver `[[deploy-vps-hetzner]]`. Sem trailer Co-Authored-By (`[[sem-co-author-commits]]`).

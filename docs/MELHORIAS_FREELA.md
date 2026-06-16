# Melhorias pendentes — Agente Freelancer (Workana)

Backlog **do que falta / dá pra melhorar** no agente `freela` — cardápio de
ideias com **prioridade sugerida** (🔴 alta / 🟡 média / 🟢 baixa) e o *porquê*.

> **Como usamos este arquivo:** sempre que eu termino algo, sugiro melhorias
> aqui. **Você marca** o que achar interessante (`[x]` ou um ✅ na frente) e eu
> implemento; o que entra pra valer sai daqui pro `docs/FREELA_FEITO.md`.
> O plano-mãe é o `docs/Workana.md`; o que já está pronto, o `FREELA_FEITO.md`.

Última revisão: **2026-06-14** (Fases 1, 2, 3, 5 e 6 + 9 alavancas §7–§10).
**👉 Foco AGORA: §0 — landar o 1º cliente** (ver abaixo). As §7–§10 já feitas
rendem mais *depois* que você começa a fechar; o gargalo de hoje é outro.

---

# 🎯 §0. FASE ATUAL — muitas propostas, ZERO cliente ainda (cold start)

> **Contexto real (2026-06-14):** o Pablo ainda não fechou nenhum projeto.
> Está mandando várias propostas pra cravar o **primeiro cliente**. Aqui o
> cliente não tem como te julgar por reputação (você não tem nota) — então a
> **proposta** e o **perfil** são 100% do que decide. A métrica que importa
> nesta fase é **TAXA DE RESPOSTA**, não de fechamento. Esta seção é a
> prioridade; as alavancas §7–§10 (negociação, cliente recorrente, forecast de
> fechado, pedir avaliação) só pagam *depois* do 1º cliente.

**O problema central do cold start:** sem avaliações, o cliente desconfia. Tudo
abaixo ataca isso — ou ajudando a *escolher onde gastar a proposta escassa*, ou
*compensando a falta de reputação com prova externa e proposta impecável*, ou
*medindo o que faz o cliente responder* (pra você melhorar rápido com pouco dado).

### A) Escrever a proposta que vence sem reputação

- [x] ✅ 🔴 **Modo "cold start" no redator** — FEITO 2026-06-15. Quando há 0
  propostas fechadas, o redator entra em modo cold start: (1) prova por
  DESCRIÇÃO (problema→solução→impacto) e remete ao "portfólio aqui na Workana"
  — **sem colar link externo** (a Workana penaliza links na proposta); (2)
  oferece redução de risco (entrega em etapas, "aprova e paga ao ver
  funcionando"); (3) tom confiante, nunca diz "iniciante". Ver FREELA_FEITO.
- [ ] 🔴 **Checklist anti-genérico antes de enviar (gate de qualidade).** Um
  passo de IA que, no rascunho pronto, confere e pontua: cita um **detalhe real**
  do projeto? propõe um **plano em passos**? tem **prazo**? tem **prova/link**?
  evita clichê ("sou apaixonado por...")? Mostra um selo "pronta / fraca" + o que
  faltou. Como proposta é escassa, **nenhuma sai genérica**. *(Era §8 🟢; sobe
  pra 🔴 nesta fase.)*
- [ ] 🟡 **Completude do perfil puxa a qualidade.** O redator fica MUITO melhor
  com `tom_escrita`, `experiencias` e `o_que_procuro` preenchidos — hoje vazios.
  Um aviso na tela ("seu perfil está 60% — preencher tom e experiências melhora
  todas as propostas") + atalho pro Perfil Mestre.

### B) Escolher onde gastar a proposta (ela é escassa)

- [ ] 🔴 **Velocidade — "projeto fresco" em destaque.** (já estava em §7) Em
  projeto com 64 propostas, o cliente lê as primeiras. Guardar a **data de
  publicação** (você informa ao colar) e marcar/ordenar a fila por "novo +
  pouco concorrido". Responder cedo é uma das poucas vantagens que independem de
  reputação.
- [ ] 🔴 **Detector de "bom 1º projeto".** Um selo pra projetos que são a melhor
  aposta pra cravar a 1ª nota: **escopo pequeno**, **cliente com pagamento
  verificado**, **poucas propostas**, **dentro do seu núcleo** e **orçamento
  saudável**. Estratégia clássica: aceitar 1–2 menores pra destravar reputação —
  a ferramenta aponta quais.
- [x] ⛔ **Contador de propostas do período** — DISPENSADO 2026-06-15: o Pablo
  assinou o **Workana Prime** (sem limite de propostas). Não se aplica.

### C) Medir o que FAZ o cliente responder (aprender rápido)

- [x] ✅ 🔴 **Métricas da fase = TAXA DE RESPOSTA** — FEITO 2026-06-15: o painel
  é adaptativo. Com 0 fechadas, os 2 últimos cards viram **Em conversa**
  (respondidas) e **Tempo até resposta**, e o forecast de fechado some
  (irrelevante com 0 cliente). Quando fechar a 1ª, os cards financeiros voltam.
- [ ] 🟡 **Resposta por ângulo de abertura (A/B real).** Você já gera 2–3
  aberturas (A/B). Registrar **qual ângulo você usou** em cada proposta e cruzar
  com quem **respondeu** → descobre que tipo de abertura converte (direta / com
  prova / com pergunta). Aprendizado com pouquíssimo dado.
- [ ] 🟡 **Resposta por categoria/stack.** (cf. §7 win-rate, mas com RESPOSTA)
  Taxa de resposta por stack do projeto → mostra onde vale insistir (provável:
  React/FastAPI/IA, o seu núcleo) e onde parar de gastar proposta.

### D) Credibilidade fora da ferramenta (o que mais trava o 1º sim)

- [ ] 🟡 **Checklist do "círculo de credibilidade".** (do `Workana.md` §7) Um
  lembrete/checklist na tela: perfil Workana com headline específica + foto +
  **identidade verificada**; **portfólio na Workana** com os mesmos projetos do
  `Perfil-Freelancer.md` (print + problema→solução→resultado); GitHub com repos
  pinados; tudo coerente com o LinkedIn. Sem isso, a melhor proposta ainda
  esbarra na desconfiança.

> **Recomendação de ordem:** comece por **A** (modo cold start + checklist
> anti-genérico) e pelo **C** (painel focado em resposta) — juntos, fazem cada
> proposta valer mais e te mostram se está melhorando. Depois **B** (velocidade
> + bom 1º projeto) pra escolher melhor onde gastar. **D** é fora do código, mas
> destrava muito o 1º sim.

---

## 1. Tela / Painel (Fase 6) — ✅ FEITO (ver FREELA_FEITO.md)

> A tela existe: métricas + precificador + fila de oportunidades + Kanban.
> O que sobrou aqui são refinamentos, não bloqueadores.

- [x] ✅ Tela do agente, Board Kanban, Fila de oportunidades, Métricas e Widget
  de precificação — todos entregues em 2026-06-14.
- [ ] 🟢 **Drag-and-drop no Kanban** — hoje move por `select` (1 clique, sem
  dep). Arrastar carta entre colunas é mais gostoso, mas pede uma lib (dnd-kit).
- [x] ✅ **Detalhe/edição da proposta** — FEITO 2026-06-14: clicar no card do
  Kanban abre o modal (editar texto/prazo, ver destaques, rascunhar com IA,
  copiar, salvar).
- [ ] 🟢 **CRUD de cliente na tela** — hoje cria cliente só via API; a tela só
  seleciona os existentes (no precificador e no form de projeto).

## 2. Inteligência / IA (Fases 3 e 5)

> ✅ Analisador (Fase 3) e Redator+Seletor (Fase 5) PRONTOS, em
> `app/analyzers/freela/{analisador,redator}/`. O que sobra aqui é refinamento.

- [x] ✅ **Analisador de projeto (Fase 3)** — FEITO 2026-06-14: `POST
  /projetos/{id}/analisar` → `analise_json` (fit_score, recomendação, red flags,
  sinais do cliente, ganchos), botão na tela e fila ordenada por fit. Ver
  FREELA_FEITO.md.
- [x] ✅ **Redator de proposta (Fase 5)** — FEITO 2026-06-14: `POST
  /propostas/{id}/redigir`, rascunho ancorado no perfil (estrutura Workana,
  anti-mentira), modal da proposta na tela com editar/copiar. Ver FREELA_FEITO.
- [x] ✅ **Seletor (Fase 5)** — FEITO: escolhe até 3 projetos + 5 habilidades do
  perfil (sai junto do redator).
- [x] ✅ **Auto-preencher o Projeto ao colar** — FEITO 2026-06-15: extrator
  dedicado (`POST /projetos/extrair`) lê o texto colado e pré-preenche título,
  orçamento mín/máx e nº de propostas; botão "✨ Auto-preencher do texto" no
  form. Ver FREELA_FEITO.

## 3. CRM / regras de negócio (refino do que já existe)

- [x] ✅ **Atualizar `ja_me_pagou_usd` ao fechar** — FEITO 2026-06-14 (ver §9 e
  FREELA_FEITO).
- [x] ⛔ **Limite de propostas do plano grátis** — DISPENSADO 2026-06-15:
  Workana Prime ativo, sem limite. Não se aplica.
- [ ] 🟢 **Motivo de perda estruturado** — enum (preço/escopo/sumiu/escolheu
  outro) além do texto livre, pra depois cruzar "por que perco".
- [ ] 🟢 **Reabrir/desfazer status** — hoje dá pra voltar status (sem trava);
  avaliar se quer impedir transições "para trás" ou manter livre.

## 4. Observabilidade / dados

- [ ] 🟡 **Evento de proposta com payload estruturado** — hoje reusa
  `pipeline_events` (campo `detalhe` como JSON em texto, sem JSONB e com a
  coluna `empresa_cnpj` irrelevante). Se quiser timeline rica por proposta,
  criar `pessoal_freela_evento` (com `proposta_id` + `payload` JSONB) como o
  `Workana.md` §2 imaginava.
- [x] ✅ **Tempo médio até resposta** nas métricas — FEITO 2026-06-14
  (`tempo_medio_resposta_horas`, no rodapé do painel de forecast).
- [ ] 🟢 **Histórico de precificações** — guardar o que o precificador sugeriu
  vs o que você cotou de fato, pra calibrar.

## 5. Multi-plataforma (Fase 7)

- [ ] 🟢 **Adapter `99freelas` (ou outro)** — prova que a abstração aguenta. O
  campo `plataforma` + `config_comissao` já existe; falta seed + (se o fluxo de
  proposta diferir) ajustes no precificador.

## 6. Fora do código (não é dev, mas potencializa)

> Do `Workana.md` §7 — a ferramenta acelera, mas quem fecha é o perfil.

- [ ] 🟢 Headline específica + foto + identidade verificada no perfil Workana.
- [ ] 🟢 Subir os mesmos projetos do `Perfil-Freelancer.md` como portfólio na
  Workana (print/GIF + problema→solução→resultado).
- [ ] 🟢 Estratégia das primeiras avaliações 5★ (aceitar 1–2 projetos menores).

---

# 🚀 ALAVANCAS DE DESEMPENHO (ganhar mais, fechar mais, perder menos)

> Estas não são "refino": são features que mexem no **resultado** — taxa de
> fechamento, ticket, tempo gasto por proposta e renda. Priorizadas pelo retorno
> esperado. Escolha o que te ajuda AGORA; eu implemento e movo pro FEITO.

## 7. Decidir melhor (proteger a proposta escassa)

- [ ] 🔴 **Velocidade conta — "projeto fresco" em destaque.** Em projeto com 64
  propostas, o cliente lê as primeiras. Guardar a *data de publicação* do projeto
  (campo novo, você informa ao colar) e ordenar/marcar a fila por "quão novo +
  quão pouco concorrido". A IA já te diz SE vale; isto te diz QUANDO corre.
- [x] ✅ **Forecast de pipeline + meta mensal.** FEITO 2026-06-14: métricas com
  `pipeline_aberto_liquido` + `forecast_liquido` (× taxa de fechamento) e painel
  na tela com meta (localStorage) e "faltam R$X". Ver FREELA_FEITO.
- [ ] 🟡 **Win-rate por categoria.** Taxa de resposta/fechamento **por stack/
  tipo de projeto** (React vs WordPress vs dados). Mostra onde você é forte de
  verdade → gaste proposta lá. Usa o `analise_json.stack` que já guardamos.
- [x] ✅ **Radar de cliente recorrente.** FEITO 2026-06-14: badge "★ recorrente"
  na fila + ordenação primeiro pra clientes com `ja_me_pagou_usd>0`.
- [x] ✅ **Scam/red-flag radar dedicado.** FEITO 2026-06-14: o analisador
  classifica `risco` (baixo/medio/alto) e a fila + painel mostram badge
  "⚠️ risco" quando médio/alto.

## 8. Escrever melhor (converter mais por proposta)

- [x] ✅ **Variações de abertura (A/B).** FEITO 2026-06-14: o redator gera 2–3
  aberturas alternativas (ângulos diferentes); no modal, clicar troca a abertura
  preservando o corpo. Ver FREELA_FEITO.
- [ ] 🟡 **Banco de propostas vencedoras (templates).** Quando uma proposta
  FECHA, marcar como "modelo": o redator passa a se inspirar nas suas que deram
  certo (estilo `blocos_curriculo` do perfil). Você melhora sozinho com o tempo.
- [x] ✅ **Assistente de negociação.** FEITO 2026-06-14: `POST /negociar` gera
  2–3 respostas (defende valor / troca escopo / concessão condicionada); painel
  no modal. Ver FREELA_FEITO.
- [ ] 🟢 **Checklist anti-genérico antes de enviar.** A IA confere se a proposta
  cita um detalhe REAL do projeto, propõe um plano e tem prazo — e avisa se
  soou copia-cola.

## 9. Precificar e cobrar melhor (proteger a margem)

- [x] ✅ **`ja_me_pagou_usd` sobe ao fechar (automático).** FEITO 2026-06-14: ao
  fechar pela 1ª vez (não duplica), soma o líquido convertido pra US$ (taxa
  `usd_brl`, default 5,20) ao acumulado do cliente → comissão cai de faixa
  sozinha. Ver FREELA_FEITO.
- [x] ✅ **Calibrador de valor-hora.** FEITO 2026-06-14: `valor_hora_real` (avg
  líquido/hora das fechadas) no rodapé do painel. Falta o "por tipo de projeto"
  e sugerir piso no precificar.
- [ ] 🟡 **Alerta de orçamento incompatível.** No precificar/criar proposta,
  avisar quando o valor a cotar estoura (ou fica muito abaixo) da faixa do
  projeto — some no campo que já guardamos (`faixa_orcamento_min/max`).
- [ ] 🟢 **Multimoeda (USD↔BRL).** Projetos internacionais vêm em US$; mostrar a
  conversão e precificar nos dois. Abre o mercado gringo (que paga mais).

## 10. Não deixar dinheiro na mesa (pós-envio e pós-venda)

- [x] ✅ **Follow-up no tempo certo (sem forçar contato fora).** FEITO
  2026-06-14: job `freela_followup.py` na rotina diária avisa no Telegram sobre
  propostas "enviada" há ≥ N dias sem resposta. *(Refino futuro: dedup pra não
  repetir o lembrete todo dia da mesma proposta.)*
- [x] ✅ **Pedir avaliação 5★ ao entregar.** FEITO 2026-06-14: modal mostra a
  mensagem pronta quando a proposta está "fechada" (botão copiar).
- [ ] 🟢 **Acompanhar prazo de entrega.** Depois de fechar, guardar o prazo
  prometido e avisar quando estiver perto — entregar no prazo = avaliação melhor
  = mais trabalho.
- [ ] 🟢 **Relatório mensal do freela.** Quanto cotou, quanto fechou, líquido,
  win-rate e tempo médio de resposta no mês — igual ao Relatório do Finanças
  (Recharts), pra ver a evolução.

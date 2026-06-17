# Melhorias pendentes — Agente Freelancer (Workana)

Backlog **do que falta / dá pra melhorar** no agente `freela` — cardápio de
ideias com **prioridade sugerida** (🔴 alta / 🟡 média / 🟢 baixa) e o *porquê*.

> **Como usamos este arquivo:** sempre que eu termino algo, sugiro melhorias
> aqui. **Você marca** o que achar interessante (`[x]` ou um ✅ na frente) e eu
> implemento; o que entra pra valer sai daqui pro `docs/FREELA_FEITO.md`.
> O plano-mãe é o `docs/Workana.md`; o que já está pronto, o `FREELA_FEITO.md`.

Última revisão: **2026-06-16** (+ §V: nova direção — análise profunda + motor da
meta R$10k/mês). Fases 1, 2, 3, 5 e 6 + 9 alavancas §7–§10 já feitas.
**👉 Foco AGORA: §0 — landar o 1º cliente** (tática imediata). **§V abaixo é o
PORQUÊ/visão** que o Pablo pediu em 2026-06-16: "a análise está vaga, quero pegar
TODA a info da proposta, saber se o valor é justo, se é difícil ou rápido, se é o
MOMENTO de gastar essa proposta, e amarrar tudo à minha meta de R$10k/mês". §V é
o destino; §0 é o primeiro passo pra lá.

---

# 🧭 §V. NOVA DIREÇÃO — de "copiloto de proposta" a MOTOR DA META (R$10k/mês)

> **Pedido do Pablo (2026-06-16):** *"Sinto que falta muita coisa pra esse agente
> ser útil — a análise está muito vaga. Quero pegar TODA a informação da proposta,
> analisar se o valor está justo no mercado, se é um projeto difícil ou rápido,
> ter uma meta de R$10.000/mês com uma estratégia pra bater, e na análise saber se
> é o MOMENTO de iniciar essa proposta (ainda estou começando). E outras coisas
> que eu não esteja vendo."*
>
> **Diagnóstico:** o analisador de hoje já cospe `fit_score`, `risco`, `veredito`,
> `red_flags`, `ganchos` e `estimativa` (horas, prazo, valor de mercado, valor a
> cotar). O problema **não é "não ter dado"** — é que o dado vem **solto e
> genérico**, sem (a) dizer **o quão difícil/demorado** é de forma clara, (b)
> cravar se o **preço está justo**, (c) responder **"vale a pena AGORA, pra mim,
> nesta fase?"** e (d) ligar cada decisão à **meta de R$10k**. §V resolve isso em
> 4 frentes. Muita coisa **reaproveita o que já existe** (forecast §7, calibrador
> de valor-hora §9, radar de recorrente §7, o próprio analisador) — é mais
> **enriquecer a saída + um motor de meta por cima** do que construir do zero.

### ⚙️ Inputs do motor — RESPONDIDOS pelo Pablo (2026-06-16)
- **Meta = R$10.000 LÍQUIDO/mês** (o que entra no bolso, depois da comissão
  Workana + impostos). O motor mira líquido e faz o caminho de volta pro bruto a
  cotar.
- **Capacidade = 5h/dia no começo**, podendo subir conforme a renda melhora.
  Premissa de planejamento: 5h/dia × ~26 dias ≈ **~130h/mês brutas**; descontando
  propostas/admin/estudo (~30%), sobram **~90h/mês faturáveis** na largada.
- **Meta em RAMPA** (não 10k de cara) — a meta cresce junto com a reputação e a
  dedicação. Rampa sugerida abaixo.

### 📈 Rampa de meta sugerida (ajustável)
> A lógica: no cold start o gargalo é **reputação**, não R$; conforme as notas
> chegam, o win-rate e o ticket sobem e a meta financeira acelera. Cada degrau só
> "abre" quando o anterior é batido — não pular etapa.

| Fase | Foco real | Meta líquida/mês | Estratégia dominante |
|------|-----------|------------------|----------------------|
| **F1 — Cold start** (mês ~1) | **1–2 avaliações 5★** (R$ é secundário) | R$ 1,5–2k | Aceitar 1–2 menores/quick wins; entregar impecável p/ destravar nota |
| **F2 — Tração** (mês ~2) | Converter com 1–2 notas na conta | R$ 3,5–4,5k | Subir ticket, parar de aceitar fundo de poço, focar no núcleo |
| **F3 — Crescimento** (mês ~3) | Ticket + recorrência | R$ 6,5–7,5k | Caçar **recorrente** e **gringo/USD**; nicho claro |
| **F4 — Meta cheia** (mês ~4+) | Renda estável de R$10k | **R$ 10k** | Mix maduro: 1–2 recorrentes de base + projetos de ticket alto; subir horas se preciso |

### 🧮 Matemática reversa (com os números do Pablo) — insight que muda a estratégia
> Com **~90h faturáveis/mês**, bater **R$10k líquido** exige um **valor-hora
> efetivo de ~R$110–120/h líquido** (10.000 ÷ ~90h). **Conclusão dura:** *não dá
> pra bater 10k empilhando projeto barato* — no preço de fundo de poço seriam
> 200h+ que o Pablo não tem. A meta cheia (F4) **depende de ticket/nicho/gringo**,
> não de volume. Por isso a rampa: F1–F2 constroem a reputação que **permite
> cobrar** o R$/h que fecha a conta em F4. (Se a dedicação subir de 5h → 7h/dia, o
> R$/h alvo cai pra ~R$80–90 e a meta fica mais folgada — o motor recalcula.)

---

## V.1 🔬 Análise PROFUNDA — acabar com a "análise vaga"

> Mesmo dado, **muito mais acionável**: a tela tem que responder *"é difícil? é
> rápido? o preço tá justo? o que vai dar trabalho?"* sem o Pablo reinterpretar.

- [x] ✅ 🔴 **Dificuldade × Esforço explícitos (quadrante).** FEITO 2026-06-16:
  o analisador devolve `complexidade_tecnica` (trivial/média/alta/incerta) e
  `clareza_escopo` (claro/parcial/vago); o backend deriva o **quadrante**
  (`quick_win` / `dificil_longo` / `escopo_vago` / `padrao`) e a tela mostra o
  selo na fila e na análise. Resolve o *"é difícil ou rápido?"*. Ver FREELA_FEITO.
- [x] ✅ 🔴 **Veredito de PREÇO — "o valor está justo?"** FEITO 2026-06-16:
  cálculo **determinístico** no service (não confia na IA pra cruzar números) —
  orçamento do cliente × faixa de mercado → selo `subcotado / justo / acima` +
  `gap_texto` ("cliente ~R$800; mercado R$1.5–2.5k → subcotado") + **R$/h efetivo**
  do orçamento. Selo na fila e linha 💰 na análise. Ver FREELA_FEITO.
- [x] ✅ 🔴 **Breakdown do escopo em tarefas + incertezas.** FEITO 2026-06-16: a
  análise devolve `tarefas` (entrega + horas, com total na tela), `perguntas_cliente`
  (ambiguidades a esclarecer antes de cotar) e `skills_faltando` (gap — o que o
  projeto exige e não está claro no seu perfil). O "20h mágico" virou lista. Ver
  FREELA_FEITO.
- [~] 🟡 **Extrair TODA a info da proposta (não só título/orçamento).** PARCIAL
  2026-06-16: o extrator passou a puxar **habilidades exigidas** (campo novo no
  form) e **nº de interessados**, e a análise já mostra o **gap de skill**. **Falta
  (precisa de migração/fluxo de Cliente):** **dados do cliente** (país, pagamento
  verificado, nº de projetos, rating, idioma) auto-preenchendo um `Cliente`,
  **data de publicação** (frescor — cf. §0B/§7) e **tipo de contrato** (fixo/hora)
  como colunas do projeto. → próximo passo desta frente.
- [ ] 🟡 **Nota de confiança da análise.** Quando o texto colado é pobre, a IA não
  deve fingir certeza. Um `confianca` (alta/média/baixa) + "me dê o perfil do
  cliente / a data de publicação pra eu cravar". Evita decisão sobre achismo.

## V.2 ⏱️ "É o MOMENTO?" — timing e custo de oportunidade

> O Pablo está começando e a proposta é escassa. A pergunta não é só *"esse
> projeto é bom?"* e sim *"é bom **pra mim, agora**, dado minha fase e minha
> agenda?"*.

- [ ] 🔴 **Veredito de timing pessoal.** Um campo `momento` (`agora / espere /
  passe`) que combina: fase cold start (cf. detector de **bom 1º projeto** §0B) +
  frescor/concorrência (§7) + sua capacidade livre. Ex.: *"fit alto, mas é difícil
  e longo pra primeira nota — comece por um quick win; volte a este quando tiver
  1–2 avaliações."* Responde literalmente o *"é o momento ou não de iniciar"*.
- [ ] 🔴 **Capacidade / agenda (anti-furada).** Guardar horas livres/semana e horas
  já comprometidas em projetos abertos. Alertar **"você não tem mão pra isso sem
  atrasar o resto"** — atraso = avaliação ruim = mata a meta. Fechar demais é tão
  ruim quanto fechar de menos.
- [ ] 🟡 **Custo de oportunidade — ranquear a fila por valor esperado.** Ordenar as
  oportunidades por **valor esperado rumo à meta** = `ticket × prob. de resposta ×
  fit ÷ horas`. Mostra *onde* a próxima proposta rende mais — não só "fit alto".

## V.3 🎯 MOTOR DA META — R$10.000/mês como bússola

> O grande pedido novo. Transformar "quero 10k" num **plano com números e ritmo**,
> e usar a meta pra **priorizar** (já existe um forecast simples no painel §7 —
> isto o evolui pra um motor de estratégia).

- [x] ✅ 🔴 **Matemática reversa da meta.** FEITO 2026-06-16: endpoint
  `POST /freela/meta/plano` (reusa as métricas reais) → **valor-hora alvo**,
  **projetos/mês**, **propostas/semana** e **diagnóstico de gargalo**
  (`ticket / conversao / volume / no_caminho / sem_dados`). Testado em
  `tests/test_freela_plano_meta.py`. Ver FREELA_FEITO.
- [x] ✅ 🔴 **Valor-hora alvo vs real.** FEITO 2026-06-16: o painel mostra
  `valor_hora_alvo` (meta ÷ horas faturáveis) vs `valor_hora_real`, pinta de
  vermelho quando abaixo, e o gargalo `ticket` cospe a conclusão dura *"R$/h × horas
  não fecha — suba ticket, não volume"*. Ver FREELA_FEITO.
- [x] ✅ 🟡 **Estratégia por FASE (o mix muda).** FEITO 2026-06-16: rampa
  **F1–F4** (`_RAMPA_META`), fase escolhida pela reputação (nº de fechadas); o
  painel mostra o badge da fase + meta do degrau + foco. Ver FREELA_FEITO.
- [~] 🟡 **Painel da meta com "plano da semana".** PARCIAL 2026-06-16: já mostra
  o **ritmo necessário** (propostas/semana + projetos/mês + ticket). Falta o
  **progresso real vs ritmo** (no caminho / atrás / na frente) no mês corrente.

## V.4 💡 O que você talvez não esteja vendo (alavancas de eficiência)

> Pontos que o Pablo pediu pra eu levantar — coisas que mexem na meta e não são
> óbvias no dia a dia. Várias **ligam features que já existem** à meta.

- [ ] 🟡 **Gringo/USD paga mais → menos projetos pra bater 10k.** Priorizar
  internacional encurta o caminho (ticket maior, menos esforço de prospecção).
  Liga o **multimoeda §9** à priorização da fila e à matemática da meta.
- [ ] 🟡 **1 cliente recorrente > 5 avulsos** pra renda estável e previsível.
  O **radar de recorrente §7** já existe — usar como peso forte no motor da meta
  (recorrente = quase-receita garantida do mês).
- [ ] 🟡 **Nicho/especialização sobe win-rate E ticket.** Espalhar proposta por
  tudo dilui; focar no núcleo (React/FastAPI/IA) faz o cliente confiar mais e
  pagar mais. O **win-rate por categoria §7** mostra ONDE focar — conectar isso ao
  "gaste proposta aqui".
- [ ] 🟢 **ROI da proposta (tempo é dinheiro).** Redigir custa tempo; medir
  "minutos por proposta × taxa de resposta" mostra se vale automatizar mais. O
  **banco de propostas vencedoras §8** corta esse custo (reusa o que converteu).
- [ ] 🟢 **Entregar no prazo = 5★ = mais convites** (loop de reputação). O
  **acompanhar prazo §10** protege a meta de longo prazo: avaliação boa traz
  cliente sem gastar proposta.

> **Resumo da direção:** §V.1 mata a "análise vaga" (difícil/rápido + preço justo +
> breakdown), §V.2 responde *"é o momento pra mim?"*, §V.3 amarra tudo na meta de
> R$10k, §V.4 são as alavancas.
>
> **✅ Entregue em 2026-06-16 (1ª leva):** o **par de maior impacto** — V.1
> (quadrante dificuldade×esforço + veredito de preço) e V.3 (motor da meta:
> matemática reversa, valor-hora alvo, propostas/semana, gargalo, rampa F1–F4).
> Ver `docs/FREELA_FEITO.md`.
>
> **Próximos passos sugeridos (em ordem de retorno):** (1) **V.1 breakdown de
> tarefas + extrair-toda-info do cliente** (completa a "análise profunda"); (2)
> **V.2 timing pessoal + capacidade/agenda** (o *"é o momento pra mim?"* depende
> de saber quantas horas você já comprometeu); (3) **V.3 progresso real vs ritmo**
> no mês corrente. Marque o que quer e eu sigo.

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
- [x] ✅ 🔴 **Checklist anti-genérico antes de enviar (gate de qualidade)** —
  FEITO 2026-06-15: `POST /propostas/{id}/checklist` pontua o rascunho (0-100,
  selo pronta/ajustar/fraca) em 5 critérios (detalhe real, plano em passos,
  prazo, prova concreta, anti-clichê) e sugere melhorias. **Bônus de
  conformidade:** varredura determinística (regex) de e-mail/telefone/WhatsApp/
  link no texto → alerta e limita o selo (a Workana penaliza). Botão "Conferir
  proposta" no modal. Ver FREELA_FEITO.
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

> **Progresso:** ✅ **A** (cold start no redator + checklist anti-genérico) e
> ✅ **C** (painel focado em resposta) FEITOS em 2026-06-15. Falta a completude
> do perfil (A 🟡). Próximo: **B** (velocidade "projeto fresco" + detector de bom
> 1º projeto) pra escolher melhor onde gastar. **D** é fora do código, mas
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
- [x] ✅ **Checklist anti-genérico antes de enviar** — FEITO 2026-06-15 (ver §0 A
  e FREELA_FEITO): gate que pontua detalhe real, plano, prazo, prova e clichê +
  alerta de contato/link (conformidade Workana).

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

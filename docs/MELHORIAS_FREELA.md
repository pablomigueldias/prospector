# Melhorias pendentes — Agente Freelancer (Workana)

Backlog **do que falta / dá pra melhorar** no agente `freela` — cardápio de
ideias com **prioridade sugerida** (🔴 alta / 🟡 média / 🟢 baixa) e o *porquê*.

> **Como usamos este arquivo:** sempre que eu termino algo, sugiro melhorias
> aqui. **Você marca** o que achar interessante (`[x]` ou um ✅ na frente) e eu
> implemento; o que entra pra valer sai daqui pro `docs/FREELA_FEITO.md`.
> O plano-mãe é o `docs/Workana.md`; o que já está pronto, o `FREELA_FEITO.md`.

Última revisão: **2026-06-14** (Fases 1, 2, 3, 5 e 6 — o copiloto está completo).
Sobra: refinos (§3/§4), Fase 7 (multi-plataforma) e fora-do-código (§6).

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
- [ ] 🟢 **Auto-preencher o Projeto ao colar** — o analisador já extrai
  orçamento/habilidades/nº de propostas do texto; gravar direto nos campos
  (hoje você digita à mão).

## 3. CRM / regras de negócio (refino do que já existe)

- [ ] 🟡 **Atualizar `ja_me_pagou_usd` ao fechar** — quando uma proposta vira
  `fechada`, somar o líquido ao acumulado do cliente (hoje é manual). É o que
  faz a comissão cair de faixa sozinha — fecha o ciclo "cliente recorrente vale
  ouro".
- [ ] 🟡 **Limite de propostas do plano grátis** — registrar quantas restam no
  período e avisar; é o recurso escasso que justifica o priorizador.
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
- [ ] 🟢 **Tempo médio até resposta** nas métricas — já dá pra calcular
  (`data_resposta − enviada_em`); só não está exposto.
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

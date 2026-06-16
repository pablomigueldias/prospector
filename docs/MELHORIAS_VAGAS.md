# Melhorias — Agente de Vagas

> Backlog de evolução do agente **Vagas** pra você ser **mais efetivo** caçando e
> se candidatando. Priorizado por impacto × esforço. Cada item diz **a dor**, **o
> que fazer** e **onde mexer** (arquivos reais).
>
> **Princípios que NÃO mudam:** (1) *para no rascunho* — a ferramenta nunca envia
> nada sem você mandar; (2) *anti-mentira* — a IA reorganiza a verdade do Perfil
> Mestre, nunca inventa. Toda melhoria respeita isso.

## Estado atual (o que já existe)

- **CRUD de vaga** colando a descrição (JD) na mão.
- **Analisar** → `analise_json` (obrigatórios/desejáveis/stack) + `match_json`
  (aderência, tenho, gaps, destaques, veredito) + `match_score`.
- **Gerar candidatura** → e-mail + variantes + carta (status `rascunho`, não envia).
- **Gerar currículo ATS** sob medida (PDF no front; não persiste — regera sempre).
- **Pipeline de status**: `quero_candidatar → candidatei → respondeu → entrevista → fim`.
- **Lista** com busca, filtros e ordenação; **funil/métricas** no topo;
  **pretensão salarial PJ/CLT** na análise. *(detalhe em `docs/VAGAS_FEITO.md`)*

> O que **já foi entregue** está em `docs/VAGAS_FEITO.md`. Este arquivo guarda só
> o que **falta**.

**Arquivos-chave:**
`backend/app/api/services/pessoal/vaga_service.py` ·
`backend/app/repositories/pessoal/vaga_repository.py` ·
`backend/app/db/models/pessoal/vaga.py` + `candidatura_email.py` ·
`backend/app/api/schemas/pessoal.py` · `backend/app/api/routers/vagas.py` ·
`backend/app/analyzers/{vaga,candidatura,curriculo}/` ·
`frontend/components/VagasScreen.tsx` · `frontend/hooks/useVagas.ts`

---

## Priorização (faça de cima pra baixo)

| # | Melhoria | Impacto | Esforço | Migration? |
|---|---|---|---|---|
| 1 | Importar vaga por **URL** (auto-preencher) | 🔥🔥🔥 | Médio | não |
| 2 | **Follow-up / lembretes** (não perder timing) | 🔥🔥🔥 | Médio | sim |
| 3 | **Persistir o currículo** gerado por vaga | 🔥🔥 | Baixo | sim |
| 6 | **Prep de entrevista** (status = entrevista) | 🔥🔥 | Médio | não |
| 7 | **Plano de ação pros gaps** do match | 🔥 | Baixo | não |
| 8 | **Deduplicação** ao cadastrar | 🔥 | Baixo | talvez |
| 9 | **Kanban** do pipeline (arrastar) | 🔥 | Médio | não |
| 10 | **Enviar candidatura** com 1 clique (opt-in) | 🔥 | Médio | usa enviado_em |
| 11 | **Timeline** de eventos por vaga | ➕ | Médio | sim |

---

## 1. Importar vaga por URL (auto-preencher) 🔥🔥🔥

**Dor:** colar a descrição inteira na mão é o maior atrito. Você desiste de
cadastrar vagas por preguiça.

**O que fazer:** campo "colar link da vaga" → backend baixa a página e a IA
extrai `titulo`, `empresa`, `localizacao`, `modelo`, `senioridade`, `descricao`,
e (se achar) `contato_email`. Você revisa e salva.

**Onde mexer:**
- Já existe collector de site: `backend/app/collectors/website/` (stealth/sessão).
  Reusar pra baixar o HTML → texto.
- Novo analyzer `backend/app/analyzers/vaga_extracao/` (prompt + parser) que
  recebe o texto da página e devolve os campos estruturados.
- `vaga_service.py`: `async def importar_de_url(url) -> VagaCreate` (não salva,
  devolve pré-preenchido pra revisão).
- Endpoint `POST /api/pessoal/vagas/importar` em `routers/vagas.py`.
- `VagasScreen.tsx` / `NovaVagaForm`: input de URL + botão "Puxar da vaga" que
  preenche o form.

**Cuidado:** muitos sites (LinkedIn/Gupy) bloqueiam scraping/exigem login.
Fallback honesto: se não conseguir baixar, pedir pra colar o texto (fluxo atual).
Suportar bem o caso "colei o texto **e** o link" também.

---

## 2. Follow-up e lembretes 🔥🔥🔥

**Dor:** você se candidata e **esquece de dar follow-up**. Timing é metade do
jogo — um "ainda tenho interesse" no dia certo destrava resposta.

**O que fazer:**
- Campos novos na vaga: `candidatei_em` (timestamp), `proximo_followup_em` (date),
  `followup_feito` (bool).
- Ao mover status pra `candidatei`, setar `candidatei_em = now` e sugerir
  `proximo_followup_em = +5 dias úteis`.
- O **Agendador diário** (já roda — vi `⏰ Agendador ligado` nos logs) varre
  vagas com `proximo_followup_em <= hoje` e **avisa pelo Telegram**: *"Follow-up
  da vaga X (empresa Y) hoje. Quer que eu rascunhe?"*.
- Botão "Gerar follow-up" → analyzer de candidatura com modo `followup` (e-mail
  curto, educado, reforça interesse + 1 prova nova). Para no rascunho.

**Onde mexer:**
- Migration: colunas em `pessoal_vagas`.
- `vaga.py` (model) + `pessoal.py` (schema) + `VagaUpdate`.
- Job no agendador (procure onde a rotina diária é registrada no backend).
- Telegram: reusar o pipeline do bot já existente.
- `candidatura/prompt_builder.py`: variante `followup`.

---

## 3. Persistir o currículo gerado 🔥🔥

**Dor:** o currículo ATS **não é salvo** — toda vez regera (gasta LLM, muda o
texto, você não consegue reusar/comparar).

**O que fazer:** salvar o último `curriculo_json` por vaga; ao reabrir, carregar
o salvo (com botão "Regerar" explícito). Opcional: histórico de versões.

**Onde mexer:**
- Migration: coluna `curriculo_json JSONB` (e talvez `curriculo_gerado_em`) em
  `pessoal_vagas`. *(Ou tabela própria se quiser versionar.)*
- `vaga_service.gerar_curriculo`: persistir o resultado; novo
  `get_curriculo(vaga_id)` que devolve o salvo.
- `routers/vagas.py`: `GET /{id}/curriculo` (busca o salvo) além do `POST` (gera).
- `VagasScreen.tsx`: carregar currículo salvo ao selecionar a vaga; "Regerar"
  separado de "Gerar".

> Mesma lógica vale pra deixar o rascunho de candidatura sempre visível ao
> reabrir a vaga (hoje só aparece logo após gerar).

---

## 6. Preparação de entrevista 🔥🔥

**Dor:** quando vira entrevista, você está sozinho. Esse é o momento de maior
valor — e a ferramenta para no `entrevista`.

**O que fazer:** com status `entrevista`, botão "Preparar entrevista" gera:
- Perguntas técnicas prováveis (a partir do `analise_json` da vaga) **com roteiro
  de resposta** baseado no seu perfil (anti-mentira).
- Perguntas comportamentais + como responder no formato STAR usando suas
  experiências reais.
- 3–5 **perguntas pra você fazer** ao entrevistador (mostra interesse).
- Pontos fracos prováveis (os `gaps`) e como contornar com honestidade.

**Onde mexer:**
- Novo analyzer `backend/app/analyzers/entrevista/` (prompt + parser).
- `vaga_service.preparar_entrevista(vaga_id)` + endpoint
  `POST /{id}/entrevista`.
- `VagasScreen.tsx`: seção que aparece quando `status === 'entrevista'`.

---

## 7. Plano de ação pros gaps 🔥

**Dor:** o match mostra os `gaps` mas não diz **o que fazer** com eles.

**O que fazer:** pra cada gap relevante, 1 linha acionável: "Gap: Kubernetes →
faça um deploy do Prospector em k8s e cite no currículo" ou "estude X em Y horas".
Conecta com o `Plano-Entrar-no-Jogo.md` (transformar projeto seu em prova).

**Onde mexer:** estender `analyzers/vaga/` (ou novo passo) pra devolver
`plano_gaps`; mostrar abaixo dos gaps em `VagasScreen.tsx`.

---

## 8. Deduplicação ao cadastrar 🔥

**Dor:** cadastrar a mesma vaga 2x (re-postada, achou em 2 fontes).

**O que fazer:** ao criar, avisar se já existe vaga com mesmo `link` (normalizado)
ou mesma `empresa + titulo` próximos. Não bloqueia — só alerta "parece duplicada".

**Onde mexer:** `vaga_service.criar_vaga`: checagem antes de inserir; índice em
`link` ajuda. Front: aviso não-bloqueante.

---

## 9. Kanban do pipeline 🔥

**Dor:** lista + botõezinhos de status é funcional mas não dá visão do funil.

**O que fazer:** visão kanban com colunas por status, arrastar o card muda o
status. Alterna com a lista atual.

**Onde mexer:** novo componente `frontend/components/VagasKanban.tsx` consumindo
os mesmos hooks; toggle lista/kanban na `VagasScreen`. Backend não muda (já tem
`atualizar` status).

---

## 10. Enviar candidatura com 1 clique (opt-in) 🔥

**Dor:** depois de aprovar o rascunho, você sai da ferramenta pra mandar o e-mail.

**O que fazer (com trava):** botão "Enviar" que dispara via mailer
(`backend/app/mailer/outreach.py` já existe), grava `enviado_em`, anexa o PDF do
currículo e **move o status pra `candidatei`** (e seta `candidatei_em`). Sempre
com **confirmação explícita** — o princípio "para no rascunho" só é quebrado por
ação consciente sua.

**Onde mexer:** `vaga_service.enviar_candidatura(email_id)` usando o mailer;
endpoint `POST /{id}/candidatura/{email_id}/enviar`; botão no
`RascunhoCandidatura` com modal de confirmação.

> Mantém o envio **manual por padrão**. Isso é conveniência, não automação cega.

---

## 11. Timeline de eventos por vaga ➕

**Dor:** sem histórico do que rolou (quando analisei, candidatei, dei follow-up,
respondeu).

**O que fazer:** tabela `pessoal_vaga_eventos` (vaga_id, tipo, descricao,
created_at). Registrar eventos automaticamente nas ações; mostrar uma timeline no
detalhe da vaga.

**Onde mexer:** migration + model + repo + render no `VagaDetalhe`.

---

## Ordem sugerida pra atacar

> ✅ Quick wins #4 (busca/filtros) e #5 (métricas) já foram — ver `VAGAS_FEITO.md`.

1. **#1 (importar por URL)** — mata o maior atrito de entrada.
2. **#2 (follow-up + Telegram)** — onde mais se ganha resposta.
3. **#3 (persistir currículo)** — para de desperdiçar LLM.
4. **#6 (prep entrevista)** — valor alto quando chega lá.
5. O resto conforme a necessidade aparecer.

> Cada item é um **slice vertical** (model → repo → service → schema → router →
> front), no padrão do projeto (ver `stack-prospector`). Faça um por commit.

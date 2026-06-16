# O que já está pronto — Agente de Vagas

Registro do que **já foi entregue** no agente `vagas` (caçador de vagas). O que
**falta** está em `docs/MELHORIAS_VAGAS.md`.

Última atualização: **2026-06-15** (currículo persistido).

> **Princípios que NÃO mudam:** (1) *para no rascunho* — a ferramenta nunca envia
> nada sem você mandar; (2) *anti-mentira* — a IA reorganiza a verdade do Perfil
> Mestre, nunca inventa. Vive na **área Pessoal** (`pessoal.ver`, tabelas
> `pessoal_vagas` / `pessoal_candidatura_emails`).

---

## Base (Fases 1–4)

- ✅ **CRUD de vaga** colando a descrição (JD) na mão.
- ✅ **Analisar** → `analise_json` (obrigatórios/desejáveis/stack) + `match_json`
  (aderência, tenho, gaps, destaques, veredito) + `match_score`.
- ✅ **Gerar candidatura** → e-mail + variantes + carta (status `rascunho`).
- ✅ **Gerar currículo ATS** sob medida (PDF no front; regera sempre).
- ✅ **Pipeline de status**: `quero_candidatar → candidatei → respondeu →
  entrevista → fim`.

## Quick wins (sessão 2026-06-15)

- ✅ **Busca + filtros na lista (#4)** — `vaga_repository.listar` aceita `busca`
  (título/empresa, `ilike`), `match_min`, `modelo`, `fonte`, `tem_rascunho` e
  `ordenar_por` (`match` | `recentes`). Query params no `routers/vagas.py`;
  `useVagas(filtro)` refaz a busca quando o filtro muda. Barra de filtros
  (`FiltrosBar`) na `VagasScreen` com busca, status, modelo, slider de match
  mínimo, ordenação, toggle "tem rascunho" e "limpar filtros".
- ✅ **Funil e métricas (#5)** — `GET /api/pessoal/vagas/metricas` →
  `VagasMetricas`: funil por status, `candidaturas`, `em_andamento`,
  `responderam`, `entrevistas`, **taxa de resposta/entrevista** e **match médio**
  (geral e das candidaturas). Agrega **todas** as vagas (ignora os filtros da
  lista). Taxas calculadas sobre `em_andamento` (exclui `fim`) pra não inflar —
  honesto dado o pipeline de status único. Faixa de `StatCard` no topo da
  `VagasScreen` agora vem da API (substituiu o cálculo client-side).

## Pretensão salarial PJ/CLT na análise (extra, 2026-06-15)

- ✅ **Bloco `salario` no `analise_json`** — a análise agora estima a faixa de
  mercado brasileira (R$/mês) separando **PJ** (bruto) e **CLT** (base) e quanto
  **pedir** em cada regime (`pretensao_pj`/`pretensao_clt`), ajustado pela
  aderência: fit alto → topo da faixa. Inclui `base` (no que se baseou) e
  `observacao` (ressalva honesta). Schema `FaixaSalarial` em `schemas/pessoal.py`
  com `field_validator` tolerante (`"R$ 8.000"` → `8000`, vazio → `null`).
- ✅ **Prompt orientado a honestidade** — PARTE 3 do `analyzers/vaga/
  prompt_builder.py`: respeita o gap PJ > CLT (~20–35%), usa sinais da vaga
  (senioridade/stack/modelo/porte), dá faixa ampla e diz isso quando faltam
  dados, `null` quando não dá pra estimar. Valores como inteiros em reais.
- ✅ **Na tela** — `BlocoSalario` renderiza dois cards (PJ | CLT) abaixo da
  stack, com a faixa formatada em BRL e "pedir: R$ X" em destaque, mais base e
  observação.

> **Verificado:** import do app ok e rotas registradas na ordem certa
> (`/metricas` antes de `/{vaga_id}`); `tsc --noEmit` limpo; coerção de
> `FaixaSalarial` testada (`"R$ 9.000"` → `9000`, `null` preservado).

## Persistir o currículo gerado (#3, 2026-06-15)

- ✅ **Migration `d1f4a7c9e2b6`** — colunas `curriculo_json JSONB` e
  `curriculo_gerado_em` em `pessoal_vagas` (encadeada no head `a09c2bcb4148`).
- ✅ **Salva ao gerar** — `vaga_service.gerar_curriculo` persiste o resultado
  (`repo.salvar_curriculo`, carimba `curriculo_gerado_em`) e devolve `gerado_em`.
  Dados factuais continuam saindo do perfil (anti-mentira), só o adaptado é salvo.
- ✅ **Carrega ao reabrir** — o currículo salvo viaja embutido no `VagaResponse`
  (`curriculo` + `curriculo_gerado_em`, igual `analise_json`/`match_json`), sem
  endpoint extra. A lista ganhou `tem_curriculo` (badge "📄 currículo" no card).
- ✅ **Na tela** — `VagaDetalhe` mostra o currículo salvo ao selecionar a vaga
  (não regera); o recém-gerado tem prioridade. Botão vira **"Regerar currículo"**
  quando já existe, com a data de geração e dica de atualizar.

> **Verificado:** roundtrip no banco (salvar → ler `curriculo_json`/
> `curriculo_gerado_em` → `tem_curriculo` na lista) verde; migration aplica e
> reverte; `tsc --noEmit` limpo.

---

## Ainda NÃO feito (resumo — detalhe e prioridade em MELHORIAS_VAGAS.md)

- #1 importar vaga por URL, #2 follow-up + Telegram, #6 prep de entrevista,
  #7 plano de ação pros gaps, #8 deduplicação, #9 kanban, #10 enviar com
  1 clique, #11 timeline de eventos.

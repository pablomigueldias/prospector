# 📋 Continuar amanhã — Prospector

> Handoff da sessão de **2026-06-16**. Tudo que ficou pendente, em ordem de
> prioridade, com arquivos reais, passos e comandos de verificação. Marque `[x]`
> conforme for fazendo.

## Estado atual

- **Branch:** `feat/freela-analise-profunda-meta` (13 commits à frente da `main`,
  **nada pushado ainda**). Working tree limpo (fora 3 `.md` soltos não rastreados:
  `Guia-Pagina-Projetos-Reative-Site.md`, `linkedin.md`, `plano.md`).
- **O que já entrou nesta branch:** freela §V (análise profunda + motor da meta
  R$10k + breakdown/perguntas/gap), correção anti-mentira do redator, perfil
  mestre completado, painel "O que estudar" do vagas, e a **Fatia 1** da
  auditoria (quick wins) — ver `FREELA_FEITO.md` / `VAGAS_FEITO.md`.
- ⚠️ **Nome da branch ficou enganoso** (carrega freela + vagas + refator geral).
  Decidir no fim: abrir 1 PR grande ou separar.

---

## 🔧 Ativar tooling (rápido, faça primeiro)

- [x] **ESLint no front** — instalado (`fc8853e`); `next lint` roda e está **verde**
  (escapadas as aspas em JSX que apareceram, commit `26aa4c2`).
- [ ] **Ruff já instalado** no venv. Rodar quando quiser:
  ```bash
  cd backend && ./venv/bin/ruff check app
  ```
- [ ] **Coverage** instalado. Pegadinha: os smokes batem no servidor via HTTP, então
  `pytest --cov` mede ~0% do service layer. Cobertura real = testes **in-process**
  (ex.: `tests/test_freela_plano_meta.py`) ou servidor sob coverage (ver `.coveragerc`).

---

## Auditoria do projeto — fatias restantes

> A **Fatia 1 (quick wins)** já foi feita (commits `5abf38a` + `64d1356`):
> dir-lixo removido, `_helpers.py` compartilhado, ruff + 177 fixes de código morto,
> bug do `Estado` no Notion corrigido. Faltam as 3 abaixo. **Uma por vez, cada
> uma com seu commit e verificação.**

### [x] Fatia 2 — Quebrar os "god-files" (alto valor) ✅ FEITA

Seguiu o padrão que o projeto **já usa** (`financas/transacao_service/` é pacote;
`components/financas/` é pasta). Sem mudar comportamento.

- [x] **Backend `freela_service.py` (1111 linhas)** → pacote
  `app/api/services/pessoal/freela_service/` com `__init__.py` re-exportando
  (`ee00410`). Módulos: `_base`, `cadastro`, `projetos`, `analise`, `propostas`,
  `checklist`, `metricas`, `meta`, `precificador`. Verificado: `from app.api.main
  import app` OK (136 rotas) + `tests.test_freela_plano_meta` 6/6 (o teste passou
  a dar patch em `metricas` no módulo `meta`, onde o nome é resolvido agora).
- [x] **`FreelaScreen.tsx` (1613 → 210 linhas)** → `components/freela/`
  (`PropostaModal`, `MetaForecast`, `PlanoMetaPanel`, `Precificador`,
  `FilaProjetos`, `Kanban`, `NovoProjetoForm`) — `6ee6269`. `tsc` limpo.
- [x] **`VagasScreen.tsx` (1293 → 129 linhas)** → `components/vagas/`
  (`Metricas`, `PainelEstudo`, `FiltrosBar`, `ListaVagas`, `VagaDetalhe`,
  `NovaVagaForm`, `_shared`) — `d3c2f7a`. `tsc` limpo.

### [x] Fatia 3 — Organizar o front por domínio ✅ FEITA

- [x] Os 35 componentes soltos foram agrupados em
  `components/{shared,prospector,perfil,vagas,freela,financas}/` (commit da Fatia 3).
  Imports cross-componente normalizados pra `@/components/<dominio>/<nome>`
  (absoluto). Verificado: `tsc --noEmit` + `next lint` verdes. **shared/**: BrandMark,
  BuscaGlobalModal, CopiarLinha, DashboardLayout, DevSyncButton, Icon, Modal,
  MoreAgentsSection, PermissionGate, Sidebar, StatCard, Topbar. **prospector/**:
  ProspectorForm, LeadRow, Copywriter{Form,Screen}, OutreachScreen. **perfil/**:
  PerfilMestreScreen. **vagas/**: VagasScreen, CurriculoPdf. **freela/**:
  FreelaScreen. **financas/**: FinancasScreen + as ~14 Sections/Modais.

### [x] Fatia 4 — Renomear árvores legadas ✅ FEITA

- [x] Resolvida a dualidade: `app/services` → **`app/prospector_engine/`** (engine
  CLI do Prospector: `manual_overrides` + `investigador/`) e `app/models` →
  **`app/domain/`** (Pydantic do Lead). `app/api/services` e `app/db/models`
  ficaram intactos (a sed só casa o prefixo exato). Imports atualizados em 14
  arquivos + `run.py` + `scripts/reanalisar_lote.py`. Validado vs baseline
  capturado antes: `app.api.main` importa (136 rotas), os 13 módulos da cadeia
  importam, `ruff` 1958 erros (inalterado), smoke `test_freela_plano_meta` 6/6.

### [x] (Opcional) Pass de modernização do ruff ✅ FEITO (autofix seguro)

- [x] Aplicado o autofix seguro (1812 fixes, commit isolado `style: ruff
  modernization`): `Optional[X]`→`X | None` (UP045), `List/Dict`→`list/dict`
  (UP006), `datetime.UTC` (UP017), anotações sem aspas (UP037), imports ordenados
  (I001). 204 arquivos, zero mudança de comportamento (validado: app 136 rotas +
  smoke 6/6).
- [ ] **Restam 362 avisos NÃO-autofixáveis** (precisam de mão/julgamento, adiáveis):
  - `F405` (167) — **há `import *` em algum lugar**; investigar e explicitar os nomes.
  - `B904` (152) — `raise ... from` dentro de `except` (cadeia de exceção).
  - `B008` (18) — chamada de função em default de argumento.
  - `E402` (9), `UP035` (112, precisa `--unsafe-fixes`), e alguns avulsos (B007/B905/E741/F601).

---

## Pendências de produto acumuladas (não-refator)

> Vieram das conversas da sessão; detalhe em `MELHORIAS_FREELA.md §V` e
> `MELHORIAS_VAGAS.md`.

- [ ] **Freela V.2 — "é o momento pra mim?"**: veredito de timing pessoal +
  capacidade/agenda (horas livres vs comprometidas) pra avisar quando não tem mão.
- [ ] **Freela — autofill de cliente (com migração)**: extrator puxar país,
  pagamento verificado, rating, data de publicação, tipo de contrato → precisa de
  colunas novas no `Projeto`/fluxo de `Cliente`.
- [ ] **Freela V.3 — progresso real vs ritmo** no mês corrente (o painel já mostra
  o ritmo necessário; falta o "no caminho / atrás / na frente").
- [x] **Vagas #7 — plano de ação POR vaga** ✅ (2026-06-17): match devolve
  `plano_gaps` (1 ação por gap decisivo) + painel "🎯 Plano pros gaps" no detalhe.
- [ ] **Perfil**: `portfolio` URL está vazio em `o_que_procuro`/contato (decidir
  se entra).

---

## Comandos úteis

```bash
# Subir (já costuma estar no ar): backend :8000, front :3000, containers db/minio
cd backend && ./venv/bin/python run.py serve        # API
cd frontend && npm run dev                            # front

# Verificações
cd backend && ./venv/bin/python -c "from app.api.main import app; print(len(app.routes))"
cd backend && ./venv/bin/python -m tests.test_freela_plano_meta
cd backend && ./venv/bin/ruff check app
cd frontend && npx tsc --noEmit

# Telas pra validar
# http://localhost:3000/agents/freela   e   /agents/vagas
```

## Decisão final pendente

- [ ] **PR**: abrir da branch `feat/freela-analise-profunda-meta` (renomear o
  título no PR, já que carrega freela + vagas + refator), ou separar em PRs.

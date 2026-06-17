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

- [ ] **ESLint no front** (config já existe em `frontend/.eslintrc.json`, só falta instalar):
  ```bash
  cd frontend && npm install -D eslint eslint-config-next@14.2.18
  npm run lint        # primeira rodada: ver o que aparece (NÃO auto-fixar em massa)
  ```
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

### [ ] Fatia 2 — Quebrar os "god-files" (alto valor)

Seguir o padrão que o projeto **já usa** (`financas/transacao_service/` é pacote;
`components/financas/` é pasta). Sem mudar comportamento.

- [ ] **Backend `freela_service.py` (1122 linhas)** → virar pacote
  `app/api/services/pessoal/freela_service/` com `__init__.py` re-exportando, e
  módulos por área: `_base.py` (helpers/_uuid/_chamar_llm/conversores),
  `projetos.py`, `propostas.py`, `analise.py`, `meta.py` (plano_meta + rampa),
  `checklist.py`, `precificador.py`. **Risco baixo** (mecânico). Verificar:
  `./venv/bin/python -c "from app.api.main import app"` + `python -m tests.test_freela_plano_meta`.
- [ ] **`FreelaScreen.tsx` (1613 linhas)** → quebrar por seção em
  `components/freela/`: `PlanoMetaPanel`, `MetaForecast`, `Precificador`,
  `FilaProjetos`/`ProjetoCard`, `Kanban`, `PropostaModal`, `NovoProjetoForm`.
  Manter `FreelaScreen.tsx` como casca que monta as seções.
- [ ] **`VagasScreen.tsx` (1293 linhas)** → mesmo tratamento em `components/vagas/`
  (`Metricas`, `PainelEstudo`, `FiltrosBar`, `VagaDetalhe`, `NovaVagaForm`).
- [ ] Verificar front: `cd frontend && npx tsc --noEmit`.

### [ ] Fatia 3 — Organizar o front por domínio

- [ ] Hoje: 35 componentes soltos em `components/` (só `financas/` é agrupado).
  Agrupar em `components/{vagas,freela,prospector,perfil,shared}/` e ajustar os
  imports (o `tsc` aponta o que quebrar). Fazer **depois** da Fatia 2 (senão move
  duas vezes).

### [ ] Fatia 4 — Renomear árvores legadas (a mais arriscada — por último)

- [ ] Dualidade que confunde: `app/services` (engine CLI do Prospector) vs
  `app/api/services`; `app/models` (dataclasses) vs `app/db/models` (ORM). **Ambas
  vivas.** Renomear pra nomes claros (ex.: `app/prospector_engine/`,
  `app/domain/`) e atualizar **todos** os imports. Muitos call sites →
  fazer isolado, com `ruff check` + import de `app.api.main` + smokes pra validar.

### [ ] (Opcional) Pass de modernização do ruff

- [ ] Sobraram ~1344 avisos **cosméticos** (`Optional[X]`→`X | None` UP045,
  `List`→`list` UP006) + `B904` (raise ... from) + `F405` (há `import *` em algum
  lugar — investigar). Tudo adiável. Se for fazer, é um commit isolado
  `style: ruff modernization`, sozinho, pra não poluir diffs de feature.

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
- [ ] **Vagas #7 — plano de ação POR vaga**: 1 linha acionável por gap (o painel
  agregado "O que estudar" já foi feito; falta o por-vaga).
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

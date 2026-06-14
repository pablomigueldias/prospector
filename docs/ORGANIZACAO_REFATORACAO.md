# Organização & Refatoração — escalabilidade do sistema e dos agentes

Diagnóstico do que **atrapalha crescer e refatorar** hoje, com um plano
incremental e de baixo risco. Não é reescrita — é quebrar "arquivos-deus" em
fatias por domínio, mantendo o comportamento.

Última revisão: **2026-06-14** (passo 1 do plano §5 ✅ feito).

> Regra de ouro pra aplicar: **um passo = um commit, smoke/build verde entre
> cada**, sem mudar comportamento (só mover/dividir). Usar *barrel files*
> (`index.ts` / `__init__.py`) pra os imports antigos continuarem funcionando.

---

## 1. O problema em números (arquivos grandes demais)

Arquivos que já passaram do tamanho saudável (alvo: ~300 linhas; teto: ~500):

**Frontend**
| Arquivo | Linhas | O que tem dentro (mistura) |
|---|---|---|
| `frontend/lib/api.ts` | ~1070 | **todos** os endpoints de **todos** os domínios num cliente só |
| `frontend/components/CartoesSection.tsx` | ~1019 | Section + Card + ProjecaoBlock + CompraForm + FaturaExtratoModal + CartaoForm |
| `frontend/lib/types.ts` | ~1007 | **todos** os tipos do app (financas, auth, prospector, pessoal…) |
| `frontend/components/TransacoesSection.tsx` | ~988 | Section + filtros + Lista + LancamentoForm (com split/auto-split/PIX) |
| `frontend/components/RecorrenciasSection.tsx` | ~661 | Section + form + lista + status |

**Backend**
| Arquivo | Linhas | O que tem dentro |
|---|---|---|
| `backend/app/api/schemas/financas.py` | ~836 | **todos** os Pydantic do módulo financeiro (conta, transação, cartão, recorrência, orçamento, resumo, pix…) |
| `backend/app/api/services/financas/transacao_service.py` | ~788 | lançar/editar/listar/pagar/excluir/transferir + helpers |
| `backend/app/api/services/financas/bot_service.py` | ~547 | dispatch do Telegram + NLU + cards + comandos + arquivo |

---

## 2. Por que isso trava escala e refatoração

1. **Achar e mexer custa caro.** Um campo novo de transação encosta em
   `schemas/financas.py` (836), `transacao_service.py` (788), `api.ts` (1070) e
   `types.ts` (1007) — quatro arquivos gigantes, cada um com dezenas de coisas
   não relacionadas.
2. **Conflitos de merge.** Vários trabalhos em paralelo tocam os mesmos
   arquivos-deus (`api.ts`, `types.ts`, `financas.py`) → conflito quase certo.
3. **Componentes com N responsabilidades.** `CartoesSection.tsx` tem 6
   componentes num arquivo; reusar o `FaturaExtratoModal` ou testá-lo isolado é
   inviável sem carregar o resto.
4. **Risco ao refatorar.** Sem testes de front e com lógica de negócio dentro de
   componentes grandes (cálculo de encargos, parcelas, datas), qualquer mexida é
   "no escuro".
5. **Onboarding lento.** Um arquivo de 1000 linhas não cabe na cabeça; o mapa
   mental do módulo não é óbvio pela estrutura de pastas.

---

## 3. Outros problemas estruturais (além do tamanho)

- **`api.ts` é um objeto único gigante.** Deveria ser um cliente fino +
  módulos por domínio (`api/financas.ts`, `api/auth.ts`, …) com um `request`
  compartilhado.
- **`types.ts` global.** Tipos deviam morar perto do domínio
  (`lib/types/financas.ts`, …) ou serem **gerados** do OpenAPI do FastAPI
  (fonte única de verdade backend↔front — hoje os tipos são duplicados à mão e
  podem divergir).
- **Helpers duplicados.** `_uuid`, `_iso`, `_intervalo_mes` aparecem copiados em
  vários services de `financas/`. Extrair pra um `financas/_common.py`.
- **Testes só "smoke via `__main__`".** Os testes rodam com
  `python -m tests.x` e `assert`, não com pytest/CI. Não há teste de front.
  Faltam: runner único (`pytest`), fixtures de banco, e algum E2E/visual
  (Playwright — já está no backlog §6).
- **Single-user embutido no front.** `FINANCAS_USUARIO_ID` fixo no cliente; a
  multiusuário real (§2 do MELHORIAS) vai exigir tirar isso do front.
- **Lógica de negócio no componente.** Cálculo de encargos/parcelas/datas
  aparece tanto no back (`encargos.py`) quanto espelhado no front
  (`lib/encargos.ts`) — risco de divergência; idealmente o back é a fonte e o
  front só exibe.
- **Migrations versus deploy por rsync.** O VPS não é repo git (deploy por
  rsync), então o estado do servidor não é rastreável pelo git — fácil
  desalinhar. (Fora do escopo de código, mas pesa na operação.)

---

## 4. Estrutura-alvo (vertical slices por domínio)

**Frontend** — uma pasta por feature, com co-localização:
```
components/financas/
  cartoes/  CartoesSection.tsx  CartaoCard.tsx  CompraForm.tsx
            FaturaExtratoModal.tsx  CartaoForm.tsx  ProjecaoBlock.tsx
  transacoes/  TransacoesSection.tsx  TransacoesLista.tsx  LancamentoForm.tsx
  reservas/  ...
lib/api/  client.ts  financas.ts  auth.ts  prospector.ts   (+ index.ts barrel)
lib/types/  financas.ts  auth.ts  ...                        (+ index.ts barrel)
```

**Backend** — quebrar os pacotes grandes mantendo o import público:
```
app/api/schemas/financas/  __init__.py (re-exporta)  conta.py  transacao.py
                           cartao.py  recorrencia.py  orcamento.py  resumo.py
app/api/services/financas/  transacao/  lancar.py  pagar.py  listar.py  transferir.py
                            _common.py  (helpers _uuid/_iso/intervalos)
```

---

## 5. Plano incremental (ordem sugerida, baixo risco)

1. ✅ **`frontend/lib/types.ts` → `lib/types/<dominio>.ts` + barrel** *(feito
   2026-06-14)* — quebrado em `core.ts` (Agent + `ApiError`), `prospector.ts`,
   `auth.ts`, `copywriter.ts`, `pessoal.ts` (perfil/vagas/candidatura) e
   `financas.ts`, com `index.ts` re-exportando tudo (`export *`). Os 42 imports
   `from '@/lib/types'` seguem válidos sem tocar em nada. Zero lógica movida;
   typecheck + build verdes. **Pendência herdada:** `financas.ts` ficou com ~620
   linhas (domínio único, mas acima do teto) — sub-dividir depois em
   `types/financas/` (conta / transacao / cartao / recorrencia / orcamento /
   resumo / boleto). (Alternativa de longo prazo: **gerar do OpenAPI**.)
2. ✅ **`frontend/lib/api.ts` → `lib/api/<dominio>.ts`** *(feito 2026-06-14)* —
   `client.ts` com o `request`/CSRF/timeout compartilhado + módulos
   `core/prospector/outreach/pessoal/financas/auth.ts`, cada um exportando um
   objeto (`coreApi`, `financasApi`, …). O `index.ts` compõe o `api` plano por
   união (`{ ...coreApi, ...financasApi }`), então `api.financasContas(...)`
   segue igual. **Paridade verificada:** 92 métodos antes = 92 depois (diff
   vazio). typecheck + build verdes. *Gotcha de dev:* ao trocar um arquivo por
   uma pasta de mesmo nome, reinicie o `next dev` com `.next` limpo **antes** de
   subir (não apague `.next` com o server rodando — corrompe o cache e o dev
   passa a procurar o arquivo velho).
3. ✅ **Quebrar os 3 componentes-deus** *(feito 2026-06-14)* —
   `CartoesSection` (1019) → `components/financas/cartoes/`
   (CartoesSection + CartaoCard + CartaoForm + CompraForm + FaturaExtratoModal +
   ProjecaoBlock); `TransacoesSection` (988) → `components/financas/transacoes/`
   (TransacoesSection + TransacoesLista + LancamentoForm + `types.ts` com
   `LancamentoInicial`); `RecorrenciasSection` (661) →
   `components/financas/recorrencias/` (RecorrenciasSection + RecorrenciaRow +
   RecorrenciaForm + **PagarRecorrenciaModal** — renomeado do `PagarMesModal`
   interno pra não colidir com o `components/PagarMesModal.tsx` global). Único
   consumidor (`FinancasScreen.tsx`) repontado. Imports usam o alias `@/`, então
   a profundidade da pasta não muda nada. typecheck + build verdes.
4. ✅ **`schemas/financas.py` → pacote `schemas/financas/`** *(feito 2026-06-14)*
   — quebrado nos 12 subdomínios que o próprio arquivo já demarcava (conta,
   categoria, transacao, cartao, recorrencia, orcamento, pagamento_mes, nlu,
   boleto, comprovante, leitura, resumo), com `__init__.py` fazendo
   `from .x import *`. Os 32 arquivos que faziam `from app.api.schemas.financas
   import X` seguem válidos. **Paridade verificada:** 80 classes antes = 80
   depois (forward-refs entre modelos do mesmo subdomínio, então resolvem no
   import). Smokes `test_financas_auth_api` e `test_financas_transacoes_pagar_api`
   verdes.
5. ✅ **`transacao_service.py` → pacote** + `_common.py` *(feito 2026-06-14)* —
   `transacao_service/` com `_base.py` (imports + `TransacaoError` + 8 helpers
   privados) e submódulos por responsabilidade: `lancar.py`, `transferir.py`,
   `consultas.py`, `editar.py`, `pagar.py`, `excluir.py`. `__init__.py` re-exporta
   a API pública (14 símbolos) — `transacao_service.X(...)` e
   `from ...transacao_service import TransacaoError` seguem válidos.
   **`_common.py`:** extraído só o `iso()` (era idêntico em ~9 services e foi
   centralizado neles). ⚠️ **`_uuid` NÃO foi centralizado** de propósito: cada
   service levanta a sua própria exceção (`ContaError`/`TransacaoError`/…) que o
   router mapeia pra HTTP — unificá-lo mudaria o tipo do erro. `_intervalo_mes`
   também ficou local (assinaturas diferentes entre transacao e resumo). Import
   da app + bateria de 9 smokes financas verdes.
6. ✅ **`bot_service.py` → pacote** *(feito 2026-06-14)* — `bot_service/` com
   `_base.py` (config/`mapa_chat_usuario`/`_responder`/helpers puros),
   `comandos.py` (/gasto /ganho /saldo /resumo /contas /conta /desfazer),
   `nlu.py` (texto livre → card → `_confirmar`) e `arquivo.py` (boleto por
   foto/PDF). O **roteamento** (`processar_update`/`_callback`) ficou no
   `__init__.py` de propósito: os smokes fazem `monkeypatch` de
   `bot_service.mapa_chat_usuario`, então o roteador precisa lê-lo **deste**
   namespace (senão o patch não chega numa cópia importada em submódulo). Os
   patches de `tg.*` (módulo) funcionam de qualquer jeito. 7 smokes do bot
   verdes.
7. ✅ **Infra de teste** *(feito 2026-06-14)* — **pytest** como runner único:
   `backend/pytest.ini` + `tests/test_smoke_suite.py` parametriza os 60 smokes
   históricos e roda **cada um num subprocesso** (`python -m tests.x`), porque
   rodar in-process quebra (cada `main()` chama `asyncio.run()` e o engine async
   global do SQLAlchemy fica preso ao 1º event loop). Pula a suíte se a API
   (:8000) estiver fora; `_XFAIL` marca 2 falhas pré-existentes (auth logout sem
   CSRF; seed vs banco de dev com categoria extra). `pip install -r
   requirements-dev.txt` traz o pytest. Resultado: **58 passed, 2 xfailed**.
   **Playwright** mínimo (login + screenshot): `frontend/playwright.config.ts` +
   `e2e/login.spec.ts` + script `npm run e2e`. ⚠️ Precisa do install único
   (`npm i && npx playwright install chromium`) e do front na **:3000** (CORS).

> Cada item acima é independente e cabe em 1–3 commits. Nenhum muda
> comportamento — então o smoke/build verde é a rede de segurança.

---

## 6. O que **não** fazer agora

- Reescrever do zero / trocar framework — desnecessário e arriscado.
- Microsserviços — o monólito modular resolve; o problema é organização
  interna, não topologia.
- Refatorar e adicionar feature no mesmo commit — separar sempre.

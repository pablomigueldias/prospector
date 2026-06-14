# Continuação — onde paramos e como retomar

> Handoff geral do sistema. Última atualização: **2026-06-14**.
> Branch de trabalho: **`feat/financas`**.
> ✅ **2026-06-14: a leva inteira foi MERGEADA na `main` e empurrada pro GitHub**
> (`923330e`, merge `--no-ff`, sem conflitos). ⚠️ **Ainda NÃO deployado no VPS** —
> deploy é por **rsync** (não é git push), então a `main` no GitHub ≠ servidor.
> Quando for subir, rodar o deploy + as migrations (ver §0). Ver §0.

---

## 0.1. Sessão 2026-06-14 (tarde) — diagnóstico do front + refatoração

**"Front não funcionava" = não estava no ar (não era bug).** Só os containers
`db` e `minio` estavam de pé; **API (:8000) e web (:3000) não rodavam**. Subidos
em dev: typecheck limpo, build verde, rotas `/login` `/agents/prospector`
`/conta` todas 200. Para rodar local: `cd backend && source venv/bin/activate &&
python run.py serve --port 8000` + `cd frontend && npm run dev`.

**Login no dev "não logava" — causa: porta + CORS.** Se o `next dev` sobe na
**:3001** (acontece quando a :3000 já está ocupada), o login falha: o CORS do
backend (`backend/app/api/main.py:82`) só libera `localhost:3000` /
`127.0.0.1:3000`. Solução: rodar o front na **:3000**. A senha do admin no dev é
a `ADMIN_SENHA_INICIAL` do `backend/.env` (2FA desativado). *Melhoria opcional:*
adicionar `localhost:3001` ao CORS de dev pra um pulo de porta não quebrar login.

**Refatoração (plano `docs/ORGANIZACAO_REFATORACAO.md` §5) — passo 1 ✅:**
`frontend/lib/types.ts` (1007 linhas, 5 domínios misturados) quebrado em
`lib/types/{core,prospector,auth,copywriter,pessoal,financas}.ts` + barrel
`index.ts` (`export *`). Os 42 imports `@/lib/types` seguem iguais. Sem mudar
comportamento; typecheck + build verdes. Falta sub-dividir o `financas.ts`
(~620 linhas) e seguir os passos 2–7 (api.ts, componentes-deus, schemas/services
do back, infra de teste).

---

## 0. Onde paramos — na `main`, ainda NÃO deployado no VPS ⏸️

Tudo abaixo está **commitado, com smoke/build verde, e já na `main` no GitHub**
(mergeado em 2026-06-14). **Falta só o deploy no VPS** (rsync + migrations).

**Cartões (o campo da vez):**
- **Trio usável:** lançar compra parcelada/à vista (botão **+ Compra** no card), **extrato da fatura** (clicar na fatura → item a item) e **pagar a fatura** (debita conta, move saldo, vira despesa do mês). Migration `d4f0a1b2c3e5` (`faturas.transacao_id`).
- **Limite/disponível + projeção** no card (barra de uso colorida; lista das próximas faturas por mês).
- **Pagar o mês** (botão no painel *Contas a pagar*): junta **fatura do cartão + boletos do mês** num modal só, cada um na sua conta, e quita tudo de uma vez (`/pagar-mes/preview` + `/pagar-mes`).

**Recorrência ciente da forma de pagamento** (migration `e5a1b3c4d6f7`): conta/cartão/boleto; recorrência de cartão vira **compra na fatura** (cron forma-aware) e dá pra "marcar/lançar o mês"; boleto importado **se liga à conta fixa** (auto pelo beneficiário + manual). Resolve "Claude no cartão / aluguel no boleto".

**Orçamento por categoria** (migration `f6b2c8d4e7a9`): teto mensal × consumido com barras (seção **Orçamentos**) + **alerta no digest** do Telegram (`ORCAMENTO_ALERTA_PCT`, default 80).

**Paridade backend↔tela (§3b) fechada:** despesa dividida por N contas, **NLU no dashboard** (caixa "digite o gasto"), registrar leitura de consumo, botão "gerar previstas".

**Docs reorganizados:** `FINANCAS_FEITO.md` (o que está pronto, por categoria) × `MELHORIAS_FINANCAS.md` (só pendente).

**Hotfix de produção (esse SIM foi aplicado no VPS):** `GEMINI_API_KEY` estava vazia no `~/reative/deploy/.env` → importar boleto dava 500. Preenchida + `docker compose up -d api`. Funciona.

**Quando for deployar:** rodar as migrations novas (já no `02-deploy.sh` no boot): `a1c7e9d2b4f0`/`b2d8f1a3c6e1`/`c3e9a4d7b8f2` (boleto, de antes) + `d4f0a1b2c3e5`/`e5a1b3c4d6f7`/`f6b2c8d4e7a9` (cartão/recorrência/orçamento) + **`a7c3e1f9d2b8`** (`contas.meta` — reservas com objetivo, Onda 3). Conferir `ORCAMENTO_ALERTA_PCT` no `.env` do VPS (tem default).

**✅ Feito (2026-06-13, continuação):**
- Botão **"Pagar fatura" direto no card do cartão** — atalho ao lado do "+ Compra" que abre o pagamento direto no form (conta/data/valor) apontando pra fatura mais antiga em aberto. Surfacing do `pagar_fatura`, sem backend novo (`CartoesSection.tsx`, prop `iniciarPagando`).
- **Bot: cadastrar conta + desfazer** — `/contas` (lista), `/conta <nome> [tipo]` (cria) e `/desfazer` (apaga o último lançamento, reverte saldo). Tira o atrito de onboarding (não precisa mais do site pra criar a 1ª conta). Backend novo só `transacao_service.ultima_transacao`. Smoke `test_financas_bot_conta_desfazer_api.py`. *Nota:* se quiser no menu do BotFather, republicar `setMyCommands`.
- **Dashboard & relatórios (§3 fechado)** — 5 itens: (1) **filtrar o relatório por conta/categoria** (backend `?conta_id&categoria_id`, smoke novo); (2) **exportar o relatório em PDF** (`window.print()` + `@media print` isolando a seção); (3) **clicar num mês do gráfico** → abre a lista de Transações daquele mês; (4) **comparar com o ano anterior** (toggle "vs {ano-1}", reusa o endpoint); (5) **busca global** (atalho `/` ou botão na sub-nav, procura em todos os meses). Build do front verde. Ref `RelatorioSection.tsx`, `BuscaGlobalModal.tsx`, `FinancasScreen.tsx`. **Decisões:** dark mode **descartado**; "patrimônio no tempo" **adiado pro §10** (precisa de snapshots).
- **Cartões §3d (parte)** — 3 itens: (1) **projeção consolidada** das próximas faturas (todos os cartões, `GET /cartoes/projecao`, bloco no topo da seção Cartões); (2) **estornar compra** (✕ no extrato → `DELETE /compras/{id}`, abate das faturas, bloqueia se a fatura já foi paga) — fecha o buraco de apagar compra errada; (3) **auto-categoria por compra** (`GET /compras/sugestao-categoria`). 3 smokes novos, build verde. **Faltam no §3d:** boleto parcelado na tela (precisa surfaçar/pagar as parcelas — maior), antecipar parcelas (maior), ajustar valor de compra, anexar comprovante (depende MinIO/§6), importar fatura por IA (Pablo pediu pra pular).

- **Onda 1 do "resolver tudo" (2026-06-13)** — 4 ganhos rápidos: (1) **erro amigável** (400, não 500) quando falta a `GEMINI_API_KEY`, na web e no bot (§6); (2) **auto-split VR/VA na tela** (modo "esgota o VR" no form, §3b); (3) **ver parcelas de uma compra** (ⓘ no extrato, §3b); (4) **PIX copia-e-cola** (cola o BR Code → preenche valor+beneficiário, parser EMV sem IA, §9). 4 smokes novos, build verde.

**Backlog ainda grande** — o Pablo pediu pra "resolver todas as pendências do MELHORIAS". É um trabalho de várias ondas (~30 itens). **Bloqueados por coisa fora do código** (precisam de VPS/credenciais/decisão): MinIO atrás do Caddy 🔴 + monitoramento/restore (§6, precisam de deploy/VPS); Open Finance 🔴 (§9, precisa conta Pluggy/Belvo); importar fatura por IA (Pablo pediu pra pular); áudio no bot (§8, precisa Whisper/Groq). O resto é código auto-contido, sendo feito em ondas.

- **Onda 2 do "resolver tudo" (2026-06-13) — Bot §1:** (1) **/resumo por período** (`/resumo julho`, `07`, `MM/AAAA`, `AAAA-MM`); (2) **lançar despesa prevista** pelo NLU ("vou pagar 200 de luz dia 10" → prevista, não move saldo, vai pra "A pagar"). 2 smokes novos. `DespesaCreate` ganhou `data_vencimento`. **Falta no §1:** confirmação rica (trocar categoria/conta por botões — atenção ao teto de 64 bytes do callback_data + falta `edit_message` na integração) e apelidos de conta (🟢).

- **Onda 3 do "resolver tudo" (2026-06-13) — §4 Metas (fechado):** (1) **projeção de fim de mês** (card "sobra estimada" no dashboard, `GET /resumo/projecao`); (2) **alerta de saldo negativo** no digest; (3) **roll-up de orçamento** (categoria-mãe soma as filhas); (4) **reservas com objetivo** (meta + barra de progresso). 5 smokes novos, build verde. ⚠️ **Migration nova `a7c3e1f9d2b8`** (`contas.meta`) — roda no `02-deploy.sh` no deploy; já aplicada no dev.

- **Correções + reserva (2026-06-14):** (1) **fix dos gráficos** que não apareciam (barras do Consumo e da projeção de cartões — `bg-brand/80` sobre oklch + cor clara); (2) **guardar na reserva** — transferência entre contas (`POST /transacoes/transferencia`), debita origem/credita destino e **não conta no resumo**; botão "+ Guardar aqui" no card da reserva. Smoke novo. Migration nenhuma.
- **Doc novo `docs/ORGANIZACAO_REFATORACAO.md`** — diagnóstico de escalabilidade: arquivos-deus (>1000 linhas: `api.ts`, `CartoesSection.tsx`, `types.ts`, `TransacoesSection.tsx`; back: `schemas/financas.py`, `transacao_service.py`) + plano incremental de quebra por domínio (vertical slices). Pendência de refatoração separada das features.

**Próximas ondas sugeridas:** §1 (confirmação rica do bot); §8 IA (perguntas em linguagem natural 🔴, categorização que aprende 🔴, detector de assinaturas, anomalias, coach de metas); §7 segurança (exportar dados, 2FA obrigatório, auditoria no front); §10 patrimônio líquido; §5 importar extrato (OFX/CSV).

---

## 1. Estado atual — está NO AR ✅ (o que JÁ estava deployado antes desta sessão)

- **App em produção:** https://studio.reativesystems.com.br — login, sessão, RBAC, 2FA, headers de segurança, financeiro e dashboard ao vivo, todos funcionando pela internet.
- **VPS:** 5 containers de pé (`api`, `web`, `caddy`, `db` healthy, `minio` healthy). Migrations rodaram do zero (public/financas/auth). Admin seedado (`pablo.miguel.dias@gmail.com`, id `00…001`).
- **Bot do Telegram (@IqueFinBot):** ligado, webhook registrado, menu de comandos publicado. Comandos: `/gasto`, `/ganho`, `/saldo`, `/resumo`, `/help`, `/start` + linguagem natural + boleto por foto/PDF.
- **Pessoas no bot:** você (chat `925108560`) e a **Monique** (chat `8834370302`) — ambas apontando pro **mesmo** `usuario_id` (`00…001`), ou seja, **carteira compartilhada**.
- **Dashboard agora manipula tudo pela web (2026-06-10):** CRUD completo de **conta**, **categoria**, **transação** (lançar/excluir, com reversão de saldo), **recorrência** (contas fixas) e **cartão**, além da **lista de transações filtrável** (mês/conta/categoria/tipo/busca). Tudo por modal, sem depender de API/bot.
- **Editar transação + agilidade (2026-06-11):** cada linha tem **✎** que abre o form pré-preenchido e salva via `PATCH` reajustando o saldo (transação de uma conta; dividida orienta a excluir/relançar). E pra agilizar: **lançar de qualquer lugar** (FAB flutuante + atalho `N`/`Ctrl+K`), **sub-nav sticky** entre as seções e a lista **lembra os últimos filtros**.
- **Relatório mensal (2026-06-11):** seção **Relatório** no dashboard com a série de 3/6/12 meses (receitas × despesas em barras + linha de saldo, via **Recharts**), totais + despesa média, top categorias do período e **export CSV** (`GET /api/financas/resumo/relatorio`). Recharts (`recharts@^2`) é agora a lib de gráficos do front — pintar com os tokens `oklch`; ref `frontend/components/RelatorioSection.tsx`.
- **Importar boleto pela web (2026-06-13):** seção **Importar boleto** no dashboard — arraste/escolha um PDF ou foto, a IA (Gemini) lê as verbas e, se batem com o total, já cria a despesa **prevista**; senão guarda pra revisão manual. Categoria opcional. Consome o `POST /api/financas/importar/boleto` que já rodava no bot. Replica o "boleto por foto" do Telegram no desktop. Ref `frontend/components/ImportarBoletoSection.tsx`.
- **Boleto: lote, desconto, recorrência e anexos (2026-06-13):** importar **vários boletos de uma vez** (arrasta N arquivos, 1 card por arquivo); **desconto por antecipação** (IA lê "desconto até DD/MM", abate se pagar no prazo); botão **↻ tornar conta fixa** (cria recorrência do boleto sem duplicar o mês); e no editor da conta a pagar, **anexar/ver comprovantes** (boleto + recibos). ⚠️ Ver comprovante no navegador funciona em dev; **em produção precisa expor o MinIO atrás do Caddy** (pendência §6 do MELHORIAS — infra/deploy).
- **Categoria/conta por beneficiário (2026-06-13):** importar um boleto sem categoria reaproveita a do último boleto do mesmo beneficiário (card avisa "categoria reaproveitada"); e ao pagar um boleto sem conta, o modal já vem com a **última conta usada pra pagar esse beneficiário** (dica "Sugerida: X"). Para de recategorizar/reescolher conta todo mês.
- **Pagar valor diferente do boleto (2026-06-13):** no modal de pagamento dá pra marcar "Paguei um valor diferente" e informar o valor real (acordo/desconto/arredondamento) — o saldo desce por esse valor e o `valor_total` da transação passa a refletir o que saiu. `POST .../pagar` aceita `valor_pago` (sobrescreve o total calculado com encargos).
- **Lembrete de vencimento + cron diário (2026-06-13):** **APScheduler** dentro do container da API (liga no startup, `SCHEDULER_ENABLED`) roda 1x/dia às `LEMBRETES_HORA` (default 8h, tz America/Sao_Paulo) a `rotina_diaria`: (1) processa recorrências — gera previstas do mês + **marca atrasadas** (resolve o "cron das recorrências" que faltava); (2) manda um **digest no Telegram** com as contas a pagar vencidas e vencendo em até `LEMBRETES_DIAS_ANTES` dias (default 3), já com juros/multa. Pablo e Monique recebem (carteira junta). Teste manual: `POST /api/financas/recorrencias/lembretes/enviar`. Dep nova: `APScheduler==3.10.4`. Ref `app/jobs/lembretes.py`.
- **Editar a conta a pagar (2026-06-13):** botão ✎ nas contas a pagar abre um editor que detalha/corrige o boleto sem mexer no saldo (não foi paga): descrição, valor, vencimento, categoria, multa%/juros% e um **editor de verbas** (add/remover, com checagem soma×total). Resolve o caso "a IA não separou as verbas". `PATCH /api/financas/transacoes/{id}/conta-a-pagar`.
- **Linha digitável + detector de duplicado (2026-06-13):** a IA extrai a linha digitável do boleto (só dígitos) e grava na transação (`linha_digitavel`, migration `b2d8f1a3c6e1`). No painel A pagar aparece um **"copiar código"** pra colar no banco sem digitar. E na importação, antes de criar, o sistema checa se aquele boleto já foi lançado (mesma linha digitável, ou beneficiário+vencimento+valor) e **não duplica** — o card de import mostra "🔁 Boleto já lançado". Início da leva "deixar o boleto profissional".
- **Juros/multa de boleto vencido (2026-06-13):** a IA do importador agora lê os encargos do boleto (multa única % + juros de mora % ao mês) e grava em `transacoes` (`multa_percentual`, `juros_mensal_percentual`). O painel **A pagar** mostra os boletos vencidos já com os juros acumulados **até hoje** (no valor e no resumo), e o modal de pagamento desdobra **valor + multa + juros (N dias) = total**, recalculando se você muda a data. Ao confirmar, o pagamento sai com o total atualizado e o saldo desce por esse valor; o quanto foi de encargos fica em `encargos_pagos`. Fórmula em `app/api/services/financas/encargos.py` (espelhada em `frontend/lib/encargos.ts`). Migration `a1c7e9d2b4f0`. **Multa/juros editáveis no modal de pagamento** (campos "Encargos por atraso") — pra **corrigir o que a IA leu** ou **preencher boletos antigos** (importados antes desta feature, que não têm os percentuais): o que você digita recalcula o total na hora e **fica salvo** na transação (`POST .../pagar` aceita `multa_percentual`/`juros_mensal_percentual`).
- **Painel "Contas a pagar" + boleto nunca some (2026-06-13):** nova seção **A pagar** no dashboard (abas *A pagar* / *Pagas*), ordenada por vencimento, com os **vencidos em vermelho** e resumo (nº de contas, total, quantas vencidas) — botão **✓ Pagar** em cada uma. E o importador mudou: agora **todo boleto com valor vira uma despesa a pagar** (antes, se as verbas não batiam com o total, não criava nada e sumia); as verbas/itens só entram quando conferem, senão fica só o total pra detalhar depois. Filtro `status` (repetível) + `por_vencimento` no `GET /api/financas/transacoes`; `data_vencimento` agora vem na lista.
- **Marcar prevista como paga (2026-06-13):** toda transação não-paga (boleto importado, recorrência ou prevista lançada no form) ganhou um botão **✓ Pagar** na lista de Transações. Abre um modal: se a transação ainda não tem conta (boleto/recorrência nascem sem), escolhe a conta; senão usa a existente. Confirma → status vira `paga`, registra a data e **move o saldo**. Backend novo: `POST /api/financas/transacoes/{id}/pagar` (`transacao_service.pagar_transacao`). Fecha o furo do importador (antes o boleto virava prevista e não dava pra quitar pela tela). Smoke: `tests/test_financas_transacoes_pagar_api.py`.
- **Cartão usável de ponta a ponta (2026-06-13, em `feat/financas`, NÃO deployado):** **lançar compra** (parcelada ou à vista) em cada cartão (botão **+ Compra**), **ver o extrato da fatura** (clicar na fatura → compras/parcelas item a item) e **pagar a fatura** (debita uma conta, move o saldo e some do "em aberto"; a fatura paga vira uma despesa do mês ligada a ela). Migration `d4f0a1b2c3e5` (`faturas.transacao_id`).
- **Conta fixa sabe como é paga (2026-06-13, em `feat/financas`, NÃO deployado):** ao cadastrar/editar uma recorrência você diz a **forma de pagamento** (conta / cartão / boleto). Recorrência **no cartão** (ex.: Claude) vira **compra na fatura** — o sistema lança sozinho todo mês e você não vê mais "Claude a pagar" fantasma; dá pra **marcar/lançar o mês** na hora (badge de situação + botão na seção Contas fixas). Recorrência **no boleto** (ex.: aluguel): o boleto importado **se liga à conta fixa** automaticamente (pelo beneficiário) e dá pra ligar/desligar na mão no editor da conta a pagar. Migration `e5a1b3c4d6f7`. ⚠️ **Migrations `d4f0a1b2c3e5` e `e5a1b3c4d6f7` ainda não rodaram em prod** (o `02-deploy.sh` roda no deploy).
- **HOTFIX produção (2026-06-13):** importar boleto em prod dava erro porque a **`GEMINI_API_KEY` estava vazia** no `~/reative/deploy/.env` do VPS. Preenchida (mesma chave do dev), `docker compose up -d api`, health 200 — já funciona. Backup do `.env` antigo ficou em `~/reative/deploy/.env.bak.<timestamp>`.
- **Botão de dev "Puxar da produção"** no rodapé de Finanças (só no build de dev): copia o banco de produção pro dev (one-way). Gated por `DEV_TOOLS_ENABLED` — em produção a rota é 404. **Desde 2026-06-11** o sync **restaura a senha local do admin** no fim (o dump trazia a senha de produção e quebrava o login do dev) — agora você loga sempre com a mesma senha do `backend/.env`.

---

## 2. Git / código

- Padrão: 1 feature = 1 commit, sem co-author.
- ⚠️ **`feat/financas` está ADIANTE de `main`** desde a sessão 2026-06-13 (~19 commits locais, **sem push/merge** — ver §0). Até 2026-06-13 de manhã os dois estavam sincronizados; a leva de cartão/orçamento/pagar-o-mês ficou só local por decisão do Pablo. Quando for subir: push `feat/financas` → merge `--no-ff` na `main` → push → deploy.
- **Deploy é por `rsync`** pro VPS (`~/reative` não é repo git) + rebuild dos containers (`docker compose up -d --build api web` no `~/reative/deploy`). Ver §5. As migrations novas rodam no boot via `02-deploy.sh`.
- ⚠️ **2 arquivos `docs/AUTH_*.md`** seguem deletados no working tree de `feat/financas` (pré-existente, não commitado) — decidir se apaga de vez ou restaura.

---

## 3. Pendências e decisões abertas

Em ordem de "pega rápido":

1. **Primeiro acesso:** logar em `/conta`, **trocar a senha** do admin e (recomendado) **ativar 2FA**. A senha inicial está em `~/reative/deploy/.env` (`ADMIN_SENHA_INICIAL`).
2. **Criar a 1ª conta** no financeiro (pelo site) — o bot precisa de uma conta ativa pra lançar.
3. **Teste guiado do casal:** Monique manda *"gastei 30 na farmácia"* → confirma no card → você dá `/saldo` e confere que apareceu pra você.
4. **`test_auth_me_logout_api` falha** (pré-existente, fora de escopo): faz `logout` sem header CSRF, que o CSRF (B8) passou a exigir → 403. Correção trivial: o teste mandar `X-CSRF-Token` nos `logout`/`logout-all`.
5. **Renomear as vars `TELEGRAM_*_SANDRA` → algo neutro** (`_2`) pra não confundir (hoje guardam a Monique). Mexe em `config.py` + `bot_service.py` + `.env` do VPS + compose.
6. **Comprovantes no navegador:** o MinIO só escuta no localhost do VPS → URLs presignadas não abrem no browser. Expor o MinIO atrás do Caddy (ex.: `/s3/*`) + ajustar `S3_ENDPOINT` público e o `img-src` do CSP.
7. ✅ **"Double /api" resolvido (2026-06-10):** Caddy passou a usar `handle /api/*` (sem strip) e `NEXT_PUBLIC_API_URL` sem `/api`. **Pegadinha:** ao trocar o Caddyfile via rsync, precisa `docker restart reative-caddy` (não só `reload`) — bind-mount de arquivo único fica preso ao inode velho.
8. **Mais de 2 pessoas no bot:** hoje só há 2 slots (você + 1). Pra um terceiro chat, generalizar o mapa chat→usuário (lista no `.env` ou tabela).
9. ⏸️ **`feat/financas` ADIANTE de `main`** (sessão 2026-06-13, ~19 commits sem push/merge/deploy — ver §0). Estavam sincronizados até a manhã do dia 13; segurar foi decisão do Pablo.
10. ✅ **Senha do dev após sync resolvido (2026-06-11):** o botão "Puxar da produção" agora reseta o `senha_hash` do admin pra `ADMIN_SENHA_INICIAL` do `backend/.env` no fim do sync, então o login do dev não quebra mais. Se ainda precisar resetar à mão (ex.: sync rodado pelo terminal, fora do botão), use o `app.api.services.auth.senha_service.hash_senha` + `UPDATE auth.usuarios`. Trocar a senha no app revoga sessões; anote a nova.

---

## 4. Próximos blocos de produto

O que **já foi feito** está catalogado em **`docs/FINANCAS_FEITO.md`** (por
categoria); o **pendente** em **`docs/MELHORIAS_FINANCAS.md`** (priorizado).

Destaques do que ainda falta (🔴):
- **Importar a fatura do cartão por foto/PDF com IA** (igual ao boleto) — pedido do Pablo, §3d. Provável próximo passo no cartão.
- **Cadastrar conta + `/desfazer` no bot** (§1).
- **Perguntas em linguagem natural sobre os dados / categorização que aprende** (§8).
- **Expor o MinIO atrás do Caddy** (§6) — destrava ver comprovante no navegador em prod.
- **Open Finance / importar extrato** (§9).

Já entregues nesta leva (antes era "próximo"): metas/**orçamento por categoria**
+ alertas no Telegram, **lembrete de vencimento** (boleto e fatura), relatório
mensal — ver `FINANCAS_FEITO.md`.

---

## 5. Cola de comandos pra retomar

```bash
# entrar no servidor
ssh deploy@178.105.157.102

# ver tudo de pé
cd ~/reative/deploy && docker compose ps

# logs da API
docker compose logs -f api

# aplicar mudança de .env / reiniciar
docker compose up -d api          # após editar .env
docker compose restart caddy      # após editar Caddyfile

# deploy de atualização (do seu PC, raiz do repo)
rsync -az --exclude='.git/' --exclude='backend/venv/' --exclude='node_modules/' \
  --exclude='frontend/.next/' --exclude='backend/.env' --exclude='deploy/.env' \
  -e ssh ./ deploy@178.105.157.102:~/reative/
ssh deploy@178.105.157.102 'cd ~/reative/deploy && ./scripts/02-deploy.sh'

# rodar a bateria de smoke tests (local)
cd backend && source venv/bin/activate
python -m tests.test_auth_2fa_api && python -m tests.test_financas_auth_api
```

# Continuação — onde paramos e como retomar

> Handoff geral do sistema. Última atualização: **2026-06-13**.
> Branch de trabalho: **`feat/financas`** — agora **espelhado em `main`** (merge + push feitos; ver §2).

---

## 1. Estado atual — está NO AR ✅

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
- **Botão de dev "Puxar da produção"** no rodapé de Finanças (só no build de dev): copia o banco de produção pro dev (one-way). Gated por `DEV_TOOLS_ENABLED` — em produção a rota é 404. **Desde 2026-06-11** o sync **restaura a senha local do admin** no fim (o dump trazia a senha de produção e quebrava o login do dev) — agora você loga sempre com a mesma senha do `backend/.env`.

---

## 2. Git / código

- Trabalho todo commitado e **com push** em `origin/feat/financas` **e `origin/main`** (os dois sincronizados; `main` recebeu tudo via merges `--no-ff`). Padrão: 1 feature = 1 commit, sem co-author.
- **Deploy é por `rsync`** pro VPS (`~/reative` não é repo git) + rebuild dos containers (`docker compose up -d --build api web` no `~/reative/deploy`). Ver §5.
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
9. ✅ **Merge `feat/financas` → `main` feito.** Os dois branches seguem sincronizados a cada feature.
10. ✅ **Senha do dev após sync resolvido (2026-06-11):** o botão "Puxar da produção" agora reseta o `senha_hash` do admin pra `ADMIN_SENHA_INICIAL` do `backend/.env` no fim do sync, então o login do dev não quebra mais. Se ainda precisar resetar à mão (ex.: sync rodado pelo terminal, fora do botão), use o `app.api.services.auth.senha_service.hash_senha` + `UPDATE auth.usuarios`. Trocar a senha no app revoga sessões; anote a nova.

---

## 4. Próximos blocos de produto

Ideias de evolução do financeiro estão em **`docs/MELHORIAS_FINANCAS.md`** (priorizadas). Destaques rápidos: cadastrar conta pelo bot, metas/orçamento por categoria, alertas de vencimento, relatório mensal automático no Telegram.

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

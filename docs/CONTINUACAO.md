# Continuação — onde paramos e como retomar

> Handoff geral do sistema. Última atualização: **2026-06-10**.
> Branch de trabalho: **`feat/financas`** — agora **espelhado em `main`** (merge + push feitos; ver §2).

---

## 1. Estado atual — está NO AR ✅

- **App em produção:** https://studio.reativesystems.com.br — login, sessão, RBAC, 2FA, headers de segurança, financeiro e dashboard ao vivo, todos funcionando pela internet.
- **VPS:** 5 containers de pé (`api`, `web`, `caddy`, `db` healthy, `minio` healthy). Migrations rodaram do zero (public/financas/auth). Admin seedado (`pablo.miguel.dias@gmail.com`, id `00…001`).
- **Bot do Telegram (@IqueFinBot):** ligado, webhook registrado, menu de comandos publicado. Comandos: `/gasto`, `/ganho`, `/saldo`, `/resumo`, `/help`, `/start` + linguagem natural + boleto por foto/PDF.
- **Pessoas no bot:** você (chat `925108560`) e a **Monique** (chat `8834370302`) — ambas apontando pro **mesmo** `usuario_id` (`00…001`), ou seja, **carteira compartilhada**.
- **Dashboard agora manipula tudo pela web (2026-06-10):** CRUD completo de **conta**, **categoria**, **transação** (lançar/excluir, com reversão de saldo), **recorrência** (contas fixas) e **cartão**, além da **lista de transações filtrável** (mês/conta/categoria/tipo/busca). Tudo por modal, sem depender de API/bot.
- **Botão de dev "Puxar da produção"** no rodapé de Finanças (só no build de dev): copia o banco de produção pro dev (one-way). Gated por `DEV_TOOLS_ENABLED` — em produção a rota é 404.

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
10. **Senha do dev:** se travar o login local, a senha de dev fica em `backend/.env` (`ADMIN_SENHA_INICIAL`); resetar só pelo banco (`UPDATE auth.usuarios SET senha_hash=...`). Trocar a senha no app revoga sessões; anote a nova.

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

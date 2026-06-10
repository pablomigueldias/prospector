# Reative Systems — Plataforma de Agentes + Organizador Financeiro

Plataforma interna da Reative: um dashboard de **agentes de IA** (Prospector, etc.) **+** um **Organizador Financeiro pessoal** com bot no Telegram. Tudo atrás de **login** (sessão + permissões), rodando **em produção** num VPS com HTTPS.

> **Em produção:** https://studio.reativesystems.com.br
> **Bot do Telegram:** @IqueFinBot
> **Este README é o guia de operação** — como usar, liberar gente, fazer deploy e resolver problema. Guias de dev por camada: [`backend/README.md`](backend/README.md) e [`frontend/README.md`](frontend/README.md).

---

## 1. Acesso rápido

| O quê | Onde |
|---|---|
| App (login) | https://studio.reativesystems.com.br/login |
| Sua conta / trocar senha / 2FA | `/conta` |
| Admin de usuários | `/admin/usuarios` (precisa de `usuarios.gerenciar`) |
| Organizador Financeiro | abre pelo dashboard após login |
| Bot do Telegram | @IqueFinBot |
| Servidor (VPS) | `ssh deploy@178.105.157.102` (só do seu PC, por chave) |

**Login do admin:** email `pablo.miguel.dias@gmail.com`. A senha inicial foi gerada no deploy e está em `~/reative/deploy/.env` no VPS (`ADMIN_SENHA_INICIAL`). **Troque no 1º acesso** em `/conta` — depois disso esse valor no `.env` não vale mais (foi só pra criar o usuário).

> ⚠️ Dois "logins" diferentes: o **do app** é email+senha (no navegador). O **do servidor** é por **chave SSH** (`~/.ssh/id_ed25519` no seu PC) — sem senha, sem root.

---

## 2. O Organizador Financeiro — o que dá pra fazer

- **Contas** (corrente, dinheiro, reserva…) com saldo que se move sozinho a cada lançamento.
- **Categorias** em árvore (ex.: Condomínio com subverbas).
- **Lançar despesas e receitas** — simples, divididas entre contas, ou auto-split (esgota o VR/VA e joga o resto no dinheiro).
- **Cartões de crédito**: faturas, total em aberto, juros; **compras parceladas** geram N parcelas nas faturas certas; **boleto parcelado** também.
- **Recorrências** (contas fixas) com job que gera as previstas do mês e marca atrasadas.
- **Leituras de consumo** (água/gás/luz) com tendência.
- **Comprovantes/boletos**: sobe foto/PDF, guarda no storage e vincula à transação (galeria).
- **Importador de boleto com IA**: manda o boleto e ele lê e lança sozinho (Gemini).
- **Linguagem natural (NLU)**: *"gastei 80 no posto"* vira um card pra confirmar.
- **Dashboard ao vivo**: saldos, receita x despesa do mês, donut por categoria, cartões, consumo, galeria — atualiza em tempo real (SSE).

Tudo isso por **3 caminhos**: o **site**, o **bot do Telegram** e a **API HTTP**.

---

## 3. Bot do Telegram (@IqueFinBot)

### Comandos (também no menu "/" do Telegram)
| Comando | O que faz |
|---|---|
| `/start` | Boas-vindas + ajuda |
| `/help` (ou `/ajuda`) | Lista tudo que dá pra fazer |
| `/gasto 50 mercado` | Lança uma **despesa** (saída) |
| `/gasto 50 mercado vr` | Idem, escolhendo a **conta** (último token) |
| `/ganho 2000 salário` | Lança uma **receita** (entrada). Alias: `/receita` |
| `/saldo` | Saldo das contas |
| `/resumo` | Receitas x despesas do mês |

Além dos comandos:
- **Falar normal**: *"gastei 80 no posto"*, *"recebi 2000 de salário"* → o bot monta um **card** com ✅ Confirmar / ❌ Cancelar / ✏️ Editar.
- **Mandar boleto/comprovante** (foto ou PDF) → ele **lê e lança** sozinho.

> Pré-requisito: ter **pelo menos uma conta** cadastrada (o bot usa a 1ª conta ativa por padrão). Crie pelo site.

### Como liberar uma pessoa no bot
O bot é **privado** (só chats autorizados). Pra liberar alguém:

1. A pessoa manda **qualquer mensagem** ao @IqueFinBot. Ela recebe `🚫 Este bot é privado` **com o código (chat_id) dela**.
2. Você decide o perfil:
   - **Mesma carteira que a sua** (ex.: cônjuge — finanças juntas): use o `usuario_id` `00000000-0000-0000-0000-000000000001` (o seu).
   - **Carteira separada**: crie um usuário no `/admin/usuarios` e use o `id` dele.
3. No VPS, edite o `.env` e aplique:
   ```bash
   ssh deploy@178.105.157.102
   nano ~/reative/deploy/.env
   #   TELEGRAM_CHAT_ID_SANDRA=<chat_id da pessoa>
   #   TELEGRAM_USUARIO_ID_SANDRA=<usuario_id do perfil>
   cd ~/reative/deploy && docker compose up -d api   # aplica
   ```
   > O "slot 2" tem `_SANDRA` no nome (legado do plano antigo) — mas serve pra qualquer pessoa. Hoje a **Monique** usa esse slot apontando pro seu `usuario_id` (carteira compartilhada). Há só **2 slots** (você + 1) no formato atual.

### Configurar a "cara" do bot (nome, descrição, foto)
Fale com o **@BotFather** no Telegram → `/mybots` → escolha o bot → **Edit Bot**. O **menu de comandos** é registrado pelo script `set-telegram-webhook.sh` (`setMyCommands`); se editar no BotFather, a próxima execução do script sobrescreve.

---

## 4. Usuários e permissões

### Catálogo de permissões
| Permissão | Dá acesso a |
|---|---|
| `financas.ver` | Ver o financeiro (saldos, resumo, etc.) |
| `financas.editar` | Lançar/editar/excluir no financeiro |
| `comprovantes.ver` | Ver a galeria de comprovantes |
| `relatorios.ver` | Relatórios |
| `pessoal.ver` | Área pessoal (só você) |
| `usuarios.gerenciar` | Criar/editar usuários e papéis |

### Papéis (perfis)
- **admin** — todas as permissões (é o seu).
- **padrao** — tudo **menos** `pessoal.ver` e `usuarios.gerenciar`. (Ex.: um co-titular vê e edita o financeiro, mas não a área pessoal nem o admin.)

### Gerenciar usuários
- **Pelo site:** `/admin/usuarios` (precisa de `usuarios.gerenciar`) — criar, ativar/desativar, atribuir papéis.
- **Pela API:** `GET/POST/PATCH /api/admin/usuarios`, `GET /api/admin/papeis`.
- **Trava de segurança:** o admin não consegue se auto-rebaixar nem remover o próprio papel admin.

> Importante: o financeiro **deriva o dono dos dados da sessão logada**, não de parâmetro. Quem entra como `padrao` (carteira separada) **não vê** os dados de outro perfil. Já carteira compartilhada = mesmo `usuario_id` (caso Monique).

### Verificação em duas etapas (2FA)
Em `/conta` você pode **ativar 2FA** (TOTP — Google Authenticator/Authy): escaneia o QR, confirma o código, guarda os **backup codes** (aparecem uma vez). Depois o login pede o código. Pra desativar, exige senha + código.

---

## 5. Operação do sistema (produção no VPS)

### Arquitetura em produção
Tudo roda em **containers Docker** no VPS Hetzner (`178.105.157.102`):

| Container | Papel |
|---|---|
| `reative-caddy` | HTTPS automático (Let's Encrypt) + roteamento + headers de segurança |
| `reative-web` | Frontend Next.js |
| `reative-api` | Backend FastAPI (roda as migrations no start) |
| `reative-db` | **PostgreSQL** (o banco — fica no VPS, não no seu PC) |
| `reative-minio` | Storage dos comprovantes/boletos (só no localhost do VPS) |

> O banco e os arquivos vivem em **volumes Docker no disco do VPS** (`db_data`, `minio_data`) — sobrevivem a restart e redeploy. Seu PC pode ficar desligado: o app e o bot continuam no ar.

### Fazer deploy de uma atualização
O código vai pro VPS por **rsync** (o `~/reative` do VPS não é um repo git). Do seu PC, na raiz do repo:

```bash
# 1. manda o código pro VPS (preserva o .env do servidor)
rsync -az --exclude='.git/' --exclude='__pycache__/' --exclude='backend/venv/' \
  --exclude='node_modules/' --exclude='frontend/.next/' \
  --exclude='backend/.env' --exclude='deploy/.env' \
  -e ssh ./ deploy@178.105.157.102:~/reative/

# 2. rebuilda e sobe (no VPS)
ssh deploy@178.105.157.102 'cd ~/reative/deploy && ./scripts/02-deploy.sh'
```
- Mudou **só o backend Python**? Mais rápido: `docker compose up -d --build api`.
- Mudou o `.env`? **Sempre** rode `docker compose up -d api` depois (senão a API fica com os valores antigos).
- O Caddy **não** é recriado pelo deploy; se mexer no `Caddyfile`, faça `docker compose restart caddy`.

### Comandos do dia a dia (no VPS, em `~/reative/deploy`)
| Ação | Comando |
|---|---|
| Status dos containers | `docker compose ps` |
| Logs da API (ao vivo) | `docker compose logs -f api` |
| Reiniciar a API | `docker compose restart api` |
| Aplicar mudança de `.env` | `docker compose up -d api` |
| Rodar o seed do admin (idempotente) | `docker compose exec api python -m app.jobs.seed_admin` |
| Registrar webhook + menu do bot | `./scripts/set-telegram-webhook.sh` |
| Backup manual do banco | `./scripts/backup.sh` |
| Uso de recursos | `docker stats` |

### Banco de dados e backups
- **Um Postgres só** (`reative`), com 3 schemas: `public` (prospector), `financas`, `auth`. As migrations rodam **sozinhas** quando a API sobe (`alembic upgrade head`).
- **Backup automático**: cron das **3h** (`backup.sh`, dump + rotação de 14 dias em `~/backups`). **Teste o restore** de vez em quando — backup que nunca foi restaurado não é backup.

### Storage (comprovantes)
Os buckets (`boletos`, `comprovantes`, `notas`) se **criam sozinhos** no 1º upload. O console do MinIO fica só no localhost do VPS — acesse por túnel: `ssh -L 9001:localhost:9001 deploy@178.105.157.102` e abra `http://localhost:9001`.

---

## 6. Desenvolvimento local (opcional)

Pra rodar na sua máquina:
```bash
# backend
cd backend && python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # preencha; em dev use SESSION_COOKIE_SECURE=false
uvicorn app.api.main:app --reload      # http://localhost:8000 (docs em /docs)

# frontend (outro terminal)
cd frontend && npm install && npm run dev   # http://localhost:3000
```
- **Migrations:** `alembic upgrade head` (e `alembic check` deve dizer "No new upgrade operations detected").
- **Seed do admin local:** `python -m app.jobs.seed_admin`.
- **Testes (smoke, sem pytest):** `python -m tests.<nome>` — ex.: `python -m tests.test_auth_2fa_api`. Os de auth/financas-via-HTTP usam `TestClient(app, base_url="https://testserver")`.

---

## 7. Stack

| Camada | Tecnologia |
|---|---|
| Backend | Python 3.12 + FastAPI + SQLAlchemy (async) + Alembic |
| Banco | PostgreSQL 16 (pgvector) |
| Auth | Sessão opaca no servidor (cookie `__Host-`), senha Argon2id, RBAC, 2FA TOTP |
| Storage | MinIO (S3-compatível) via boto3 |
| IA | Google Gemini (importador de boleto, NLU) |
| Frontend | Next.js 14 + TypeScript + Tailwind (design system OKLCH) |
| Bot | Telegram (webhook manual, sem libs) |
| Infra | Docker Compose + Caddy (HTTPS) no VPS Hetzner |

---

## 8. Solução de problemas (quirks conhecidos)

- **Mexi no `.env` do VPS e nada mudou** → falta `docker compose up -d api` (env só entra ao recriar o container).
- **API dá 404 depois de mexer no Caddy** → `docker compose restart caddy` (o deploy não recria o Caddy).
- **Contrato de URL "double /api"**: o front usa `NEXT_PUBLIC_API_URL=.../api` + paths `/api/...`, e o Caddy (`handle_path /api/*`) remove **um** `/api`. Resultado: chamada manual à API precisa de `/api/api/...`. Funciona, mas confunde — candidato a limpeza (ver `docs/CONTINUACAO.md`).
- **Imagem de comprovante não abre no navegador** → o MinIO só escuta no localhost do VPS; as URLs presignadas apontam pra `minio:9000`. Pendência: expor o MinIO atrás do Caddy. (Uploads server-side funcionam.)
- **Bot diz "bot privado"** → o chat não está mapeado; veja §3 "Como liberar uma pessoa".

---

## 9. Segurança

- Nenhum segredo no Git: `.env`/`.env.local` são gitignored. Os segredos de produção vivem só em `~/reative/deploy/.env` no VPS (perm 600).
- Senhas em Argon2id; sessão como hash no banco; cookies httpOnly+Secure+SameSite; CSRF nas mutações; rate-limit + lockout no login; headers HSTS/CSP/X-Frame no Caddy; auditoria de eventos.
- ⚠️ **`TOTP_ENC_KEY`** (cifra os segredos de 2FA): **nunca** troque depois que alguém ativar 2FA — os segredos ficariam ilegíveis.

---

## Licença
Propriedade da Reative Systems. Uso interno.

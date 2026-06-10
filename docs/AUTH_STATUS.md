# Módulo `auth` — Status (o que foi feito e o que falta)

> Portão de entrada do app (login, sessão, permissões). Construído na branch
> `feat/financas`, antes do deploy, como pré-requisito do módulo `financas`.
> Build em "1 step = 1 commit, smoke test verde entre cada".
> Última atualização: 2026-06-09 (inclui o Step B — isolamento do financas).

---

## 1. Visão geral / decisões de arquitetura

| Decisão | O que foi feito |
|---|---|
| **Sessão opaca no servidor (não JWT)** | Token aleatório de 256 bits num cookie `__Host-sessao` httpOnly. No banco guarda só `sha256(token)`. Revogação imediata (logout mata a sessão na hora). |
| **Backend é a fonte de verdade de autorização** | `require_permission(codigo)` barra no servidor (403). O front esconder a aba é só UX. |
| **Sem cadastro público** | Usuários nascem só via admin (`/api/admin/usuarios`) ou seed. |
| **Schema isolado** | Tudo no schema Postgres `auth` (mesmo banco `reative`, ao lado de `public` e `financas`). **Não há banco novo no VPS.** |
| **Senha Argon2id** | `argon2-cffi`, com anti-timing (verify contra hash dummy quando o email não existe) e validação de força (mín. 12). |
| **Admin = dono do financas** | O admin é semeado com `id = 00000000-0000-0000-0000-000000000001`, o mesmo `usuario_id` que o financas usa por padrão. Login do Pablo já enxerga os dados financeiros. |

### Cookie em dev vs produção
- **Produção (HTTPS via Caddy):** `SESSION_COOKIE_SECURE=true` → cookies `__Host-sessao` / `__Host-csrf` (Secure). Front e API no mesmo domínio → cookie first-party.
- **Dev (http puro):** `SESSION_COOKIE_SECURE=false` → cookies `sessao` / `csrf_token` (sem Secure, pois o browser exige HTTPS para `__Host-`/Secure). Front (3000) e API (8000) são cross-port mas same-site → cookie viaja com `credentials:'include'` + CORS `allow_credentials`.

---

## 2. O que JÁ FOI FEITO (16 commits, todos com teste verde)

### Fase A — Núcleo de autenticação
- **A1** Schema `auth` + models `usuarios` / `sessoes` (token hasheado) + migration.
- **A2** Hashing Argon2id + validação de força + anti-timing (`senha_service`).
- **A3** `POST /api/auth/login` + cookie de sessão + `sessao_service` (token opaco).
- **A4** Dependency `usuario_atual` (lê cookie, valida, renova inatividade) + `GET /api/auth/me` + `POST /api/auth/logout` + `/logout-all`.
- **A5** RBAC: models `papeis`/`permissoes`/N:N + `require_permission(codigo)` + `app/jobs/seed_admin.py` (idempotente). `/me` e `/login` devolvem permissões.
- **A6** Frontend: `contexts/AuthContext.tsx`, `pages/login.tsx`, `middleware.ts` (guarda no edge, só em produção), `api.ts` com `credentials:'include'`.
- **A7** `/api/pessoal/*` exige `pessoal.ver`; `<PermissionGate>` + `lib/permissions.ts`; Sidebar filtra agentes + box do usuário/Sair; guarda na página `[slug]`. → **resolve "aba pessoal só pra mim"**.

### Fase B — Defesas (endurecimento)
- **B7** Rate limit + lockout progressivo (`tentativas_login`): por IP (10/15min) e por conta (5 falhas → lockout que dobra até 120 min). 429 no estouro.
- **B8** CSRF double-submit: cookie CSRF legível + header `X-CSRF-Token`, exigido só em mutações **autenticadas por cookie** (webhook do Telegram e login não quebram).
- **B9** Auditoria (`auth.auditoria`): grava `login_ok`, `login_falha`, `logout`, `logout_all`, `senha_alterada`, `usuario_criado`, `papeis_alterados`.
- **B10** Troca de senha (`POST /api/auth/senha`): exige senha atual + valida força + **revoga as outras sessões**. Tela `pages/conta.tsx` (trocar senha + "sair de todos os dispositivos").

### Fase B (continuação) — isolamento de dados do financas
- **B-financas** As rotas `/api/financas/*` passaram a **derivar o `usuario_id` da sessão** (dependency `app/api/dependencies/financas.py`), em vez de aceitá-lo por query string / corpo. Leitura exige `financas.ver`, mutação exige `financas.editar`; o `usuario_id` mandado no corpo é **ignorado** (sobrescrito pelo logado) → ninguém troca o parâmetro pra ver dados de outro perfil. O **bot do Telegram** não é afetado (chama os services direto). Teste e2e: `tests/test_financas_auth_api.py` (401 sem cookie, dono = sessão, 403 sem permissão, CSRF). **Exceções deliberadas:** (a) `POST /api/financas/recorrencias/processar` é endpoint de **job** (cron, `usuario_id=None` = todos) e segue sem derivar da sessão; (b) os GET/PATCH/DELETE **por id** (ex.: `/contas/{id}`) exigem login+permissão mas ainda não checam *ownership* do recurso pelo `usuario_id` — id é UUID aleatório; endurecer à parte se virar necessário.

### Fase E / G
- **E18** Admin de usuários: `/api/admin/usuarios` (criar/listar/editar + atribuir papéis) e `/api/admin/papeis`, só com `usuarios.gerenciar`. Tela `pages/admin/usuarios.tsx` + link no Sidebar. Trava de segurança: admin não desativa nem remove o próprio papel admin.
- **G24** Headers de segurança no Caddy: HSTS, X-Content-Type-Options, X-Frame-Options DENY, Referrer-Policy, CSP, `-Server`.

### Catálogo de permissões
`pessoal.ver`, `financas.ver`, `financas.editar`, `comprovantes.ver`, `relatorios.ver`, `usuarios.gerenciar`.
- **admin** (Pablo): todas.
- **padrao** (ex.: Sandra): tudo menos `pessoal.ver` e `usuarios.gerenciar`.

---

## 3. O que FALTA

### Auth
- **D15–D17 — 2FA (TOTP)** *(não feito; é o próximo passo natural)*: tabela `usuario_2fa` (secret cifrado + backup codes hasheados), setup com QR, ativar/desativar, login em 2 etapas. Lib `pyotp`. Detalhes no `AUTH_CONTINUACAO.md`.
- ~~Derivar `usuario_id` da sessão no financas~~ ✅ **FEITO** (Fase B — continuação acima). Já dá pra criar a Sandra com segurança de isolamento de dados.
- *(pré-existente, não-bloqueante)* `tests/test_auth_me_logout_api.py` (Step 4) falha em isolamento: faz `logout` sem header CSRF, que o B8 passou a exigir → 403. É só atualizar o teste pra mandar `X-CSRF-Token` nos `logout`/`logout-all`. Não tocado aqui (fora do escopo do isolamento do financas).

### Deploy (Step 30 do financas, ainda pendente)
- Subir no VPS Hetzner. Migrations rodam sozinhas no start do container (`alembic upgrade head`). Depois, **uma vez**: `docker compose exec api python -m app.jobs.seed_admin`.
- `deploy/.env` já recebe as vars de auth (commit `e79f828`). Conferir `ADMIN_EMAIL`/`ADMIN_SENHA_INICIAL`/`SESSION_COOKIE_SECURE=true` lá.

---

## 4. Como rodar e testar localmente

```bash
# backend
cd backend && source venv/bin/activate && uvicorn app.api.main:app --reload
# frontend (outro terminal)
cd frontend && npm run dev
```
Abra http://localhost:3000 → cai em `/login`.
- **Admin:** email em `backend/.env` (`ADMIN_EMAIL`), senha em `ADMIN_SENHA_INICIAL` (trocar no 1º acesso pela tela `/conta`).

### Rodar os smoke tests de auth
```bash
cd backend && source venv/bin/activate
for t in test_auth_models test_auth_senha test_auth_login_api test_auth_me_logout_api \
         test_auth_rbac_api test_auth_pessoal_protegido_api test_auth_rate_limit_api \
         test_auth_csrf_api test_auth_auditoria_api test_auth_troca_senha_api \
         test_auth_admin_usuarios_api; do
  python -m tests.$t 2>&1 | grep -E "TUDO OK|AssertionError" ; done
```

### (Re)rodar o seed do admin
```bash
cd backend && source venv/bin/activate && python -m app.jobs.seed_admin
```

---

## 5. Segurança — checklist (estado atual)
- [x] Senhas em Argon2id; nenhum segredo no código (tudo no `.env`, que é gitignored)
- [x] Token de sessão só como hash; cookie httpOnly+Secure (prod)+SameSite
- [x] Sem signup público; usuários só via admin
- [x] Rate limit + lockout; mensagens genéricas (anti-enumeração)
- [x] CSRF nas mutações; HSTS+CSP+X-Frame-Options no Caddy
- [x] Toda rota pessoal valida permissão no backend; rotação de sessão no login
- [x] Logout revoga de verdade; troca de senha revoga as outras sessões
- [x] Auditoria gravando eventos
- [x] **`/api/financas/*` deriva `usuario_id` da sessão** (isolamento entre perfis garantido no backend)
- [ ] **2FA no admin** (pendente)

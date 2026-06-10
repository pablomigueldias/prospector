# Módulo `auth` — Handoff para continuar

> Documento para retomar o trabalho exatamente de onde parou. Leia junto com
> `AUTH_STATUS.md` (visão geral). Branch: `feat/financas`.
> Última parada: **fiz o Step B (§4) e o 2FA TOTP D15–D17 (§3)** — ambos ✅.
> Próximo: **deploy (§5)**.

---

## 0. Onde exatamente parei

- Últimos commits: `auth: 2FA TOTP … (D15/D16)` + `auth: login em 2 etapas com 2FA … (D17)` (e antes `Step B`).
- Verde: toda a bateria de financas + os 2FA (`test_auth_2fa_api`, `test_auth_2fa_login_api`) + `test_financas_auth_api` + frontend `typecheck`/`build`. ⚠️ `test_auth_me_logout_api` falha por motivo **pré-existente** (logout sem CSRF; ver §4 — não relacionado ao 2FA).
- **Falta**: só o **deploy (Step 30, §5)**.

---

## 1. Mapa de arquivos do módulo `auth`

### Backend (`backend/`)
```
app/db/models/auth/
  usuario.py            Usuario (email único, senha_hash, ativo, twofa_ativado, ultimo_login)
  sessao.py             Sessao (token_hash sha256, expira_em, ultimo_uso, revogada, ip, ua)
  papel.py              Papel (nome único, descricao)
  permissao.py          Permissao (codigo único, descricao)
  usuario_papel.py      N:N usuario↔papel (PK composta)
  papel_permissao.py    N:N papel↔permissao (PK composta)
  tentativa_login.py    log de tentativas (email, ip, sucesso, created_at) — rate limit
  auditoria.py          trilha (usuario_id, evento, ip, ua, detalhe JSONB, created_at)

app/api/services/auth/
  senha_service.py      Argon2id: hash_senha, conferir_senha (anti-timing), validar_forca, SenhaFraca
  sessao_service.py     gerar/criar/validar/revogar sessão; hash_token; revogar_outras/_todas
  login_service.py      login() — rate_limit.checar → confere → registra tentativa → auditoria → cria sessão
  cookie.py             cookie_name(), set/clear_session_cookie (Secure/__Host- por settings)
  csrf.py               csrf_cookie_name(), set_csrf_cookie, valido(request) (double-submit)
  permissoes.py         CATALOGO, PADRAO, NOME_ADMIN/PADRAO, listar_codigos(session, usuario_id)
  rate_limit.py         checar() (por IP e por conta, lockout progressivo), registrar(); Bloqueado
  auditoria_service.py  registrar() + constantes de evento (LOGIN_OK, ...)
  usuario_service.py    to_response(), ip_do_request(), user_agent_do_request()
  admin_service.py      listar/criar/atualizar usuários + papéis; AdminError

app/api/dependencies/auth.py   usuario_atual (guarda), require_permission(codigo) (fábrica → 403)
app/api/routers/auth.py        /api/auth/login, /me, /logout, /logout-all, /senha
app/api/routers/admin_usuarios.py  /api/admin/usuarios (GET/POST/PATCH) + /api/admin/papeis
app/api/schemas/auth.py        LoginRequest, UsuarioResponse, TrocaSenhaRequest, MensagemResponse,
                               PapelItem, UsuarioAdminItem/Create/Update/ListResponse
app/jobs/seed_admin.py         seed idempotente (permissões, papéis, admin com id 00..001)

config.py            settings: session_cookie_secure, session_dias_absoluto,
                     session_horas_inatividade, admin_email, admin_senha_inicial
alembic/env.py       MANAGED_SCHEMAS inclui "auth"
alembic/versions/    a1f0c0de0001 (usuarios+sessoes), 807b832cd51c (rbac),
                     390ea0e0f51d (tentativas_login), f79aa7549280 (auditoria)
tests/test_auth_*.py 11 smoke tests
```

### Frontend (`frontend/`)
```
contexts/AuthContext.tsx   usuario+permissões em memória; login/logout/hasPermission/refresh;
                           guarda client-side (redireciona /login); FullScreenLoader
pages/login.tsx            form email+senha (erro genérico)
pages/conta.tsx            trocar senha + sair de todos os dispositivos
pages/admin/usuarios.tsx   CRUD de usuários (só usuarios.gerenciar)
middleware.ts              guarda no edge (SÓ em produção; em dev o cookie é cross-port)
lib/api.ts                 credentials:'include' + header X-CSRF-Token nas mutações; métodos auth*/admin*
lib/permissions.ts         AGENT_PERMISSAO (slug→permissão)
lib/types.ts               Usuario, PapelItem, UsuarioAdminItem
components/PermissionGate.tsx   <PermissionGate need="x">
components/Sidebar.tsx     filtra agentes por permissão; box do usuário→/conta + Sair; link Usuários
pages/_app.tsx             <AuthProvider>
pages/agents/[slug].tsx    guarda de permissão por agente
```

---

## 2. Convenções/padrões (SIGA para manter consistência)

1. **Migrations**: schema novo precisa de `op.execute("CREATE SCHEMA IF NOT EXISTS ...")` à mão (autogenerate não emite). Tabelas dentro de schema existente podem usar `alembic revision --autogenerate`. Sempre rode `alembic upgrade head` + `alembic check` (deve dar "No new upgrade operations detected"). Adicione schema novo em `MANAGED_SCHEMAS` no `alembic/env.py`. Registre todo model em `app/db/models/__init__.py` (import + `__all__`).
2. **Smoke tests** (não há pytest): arquivo `tests/test_*.py` com `smoke_test()` + `main()`, rodado por `python -m tests.<nome>`. Para auth, **use `TestClient(app, base_url="https://testserver")`** (senão o cookie Secure não entra no jar). Setup/cleanup de DB com **engine próprio** (`create_async_engine(settings.database_url)` + `asyncio.run`), porque o engine global fica preso ao loop do TestClient.
3. **CSRF nos testes**: mutações autenticadas precisam do header `X-CSRF-Token` = valor do cookie CSRF (`client.cookies.get("csrf_token")` em dev). Sem cookie de sessão, CSRF não é exigido.
4. **Roles nos testes**: vários testes assumem que `seed_admin` já rodou (papéis `admin`/`padrao` existem). Se um teste falhar com "papel não existe", rode `python -m app.jobs.seed_admin`.
5. **Nome de cookie** muda com `SESSION_COOKIE_SECURE`: dev = `sessao`/`csrf_token`; prod = `__Host-sessao`/`__Host-csrf`. Sempre derive de `cookie_name()` / `csrf_cookie_name()`, nunca hardcode.
6. **Auditoria/rate limit** gravam dentro da MESMA sessão/transação do login; quem chama dá o commit.
7. **Commits**: 1 step = 1 commit, **sem** trailer Co-Authored-By (preferência do Pablo). Prefixo `auth:` / `deploy:` / `fix(testes):`.
8. **`.env` é gitignored** (root `.gitignore` + `deploy/.gitignore`). Nunca colocar segredo em arquivo rastreado; `.env.example` só com chaves vazias.

### Pegadinhas de ambiente já encontradas
- O `cwd` do shell volta pra raiz do repo depois de um `git`/`cd` — sempre `cd backend` antes de rodar testes.
- `pkill ... && git ...`: o `pkill` retorna 1 se não achar processo e corta o `&&`. Separe com `;`.
- Testes do bot (`test_financas_bot_*`) zeram `settings.telegram_webhook_secret` durante o teste (o `.env` tem secret real agora). Mantido no commit `1cbcc7d`.

---

## 3. ✅ FEITO — 2FA (TOTP) [D15–D17]

**Implementado** (commits `c173bb7` D15/D16 + `ccba280` D17). O que ficou no código:
- Model `app/db/models/auth/usuario_2fa.py` (PK = usuario_id, FK CASCADE); secret cifrado com **Fernet** (`TOTP_ENC_KEY`); `backup_codes_hash` = ARRAY de sha256 (uso único); `ativado_em`.
- `app/api/services/auth/twofa_service.py`: `gerar_setup` (otpauth URI + **QR PNG data-URI** gerado no backend), `confirmar_ativacao`, `validar_codigo` (TOTP `valid_window=1` **ou** consome backup), `desativar`. Exceção `TwoFAError`.
- Rotas `/api/auth/2fa/{setup,ativar,desativar}` em `auth.py`; auditoria `2fa_ativado`/`2fa_desativado`.
- Login 2 etapas: `login_service` levanta `DoisFatoresRequerido` → router devolve 401 `detail="2fa_requerido"`. Código errado conta no rate limit. `LoginRequest.codigo_2fa`.
- Front: `pages/login.tsx` (2º passo), `pages/conta.tsx` (`SecaoDoisFatores`: QR + secret manual + backup codes uma vez; desativar com senha+código), `lib/api.ts` + `AuthContext`.
- Deps: `pyotp==2.9.0`, `qrcode[pil]==7.4.2` no `requirements.txt`. Settings `totp_enc_key`. `TOTP_ENC_KEY` no `.env`/`.env.example` (dev) e injetado no `deploy/docker-compose.yml` + `deploy/.env.example`.
- Testes: `test_auth_2fa_api.py` (gestão) e `test_auth_2fa_login_api.py` (login 2 etapas) — ambos calculam o TOTP com `pyotp`, como o app autenticador.

> Pegadinha encontrada: o cookie CSRF **rotaciona a cada `/me`** (a rota chama `set_csrf_cookie`); nos testes, releia `csrf_token` do jar antes de cada mutação em vez de guardar o valor do login.

<details><summary>Plano original (referência)</summary>

Objetivo: 2º fator opcional, ligado já no admin. **Não refaz nada** do que existe.

### D15 — model + setup
- `pip install pyotp==2.9.0` (+ `qrcode[pil]` se quiser gerar o PNG do QR no backend; ou só devolver a `otpauth://` URI e o front renderiza o QR).
- Model `app/db/models/auth/usuario_2fa.py` (schema auth):
  - `usuario_id` (UUID, PK, FK auth.usuarios ondelete CASCADE)
  - `totp_secret_cifrado` (String) — **cifrado**, não em texto. Chave em `.env` (`TOTP_ENC_KEY`, gerar `openssl rand -base64 32`). Use `cryptography.fernet.Fernet`.
  - `backup_codes_hash` (ARRAY(String) ou JSONB) — cada código guardado como hash (Argon2 ou sha256), uso único.
  - `ativado_em` (DateTime nullable), timestamps.
- Settings: `totp_enc_key: str = ""`. Migration (autogen, schema auth já existe).
- `app/api/services/auth/twofa_service.py`:
  - `gerar_setup(usuario_id)` → cria/atualiza secret cifrado (ainda NÃO ativado), devolve `otpauth://totp/Reative:<email>?secret=...&issuer=Reative` (use `pyotp.TOTP(secret).provisioning_uri`).
  - `confirmar_ativacao(usuario_id, codigo)` → valida `pyotp.TOTP(secret).verify(codigo)`, marca `usuario.twofa_ativado=True`, gera 10 backup codes (retorna em texto UMA vez, guarda hash).
  - `desativar(usuario_id, senha, codigo)` → exige senha + código.
  - `validar_codigo(usuario_id, codigo)` → TOTP OU consome um backup code.
- Rotas em `auth.py`: `POST /auth/2fa/setup`, `POST /auth/2fa/ativar`, `POST /auth/2fa/desativar`.

### D16 — backup codes
- Geração (10), exibição única, hash no banco, consumo de uso único na validação.

### D17 — login em 2 etapas
- Alterar `login_service.login`: se `usuario.twofa_ativado`, **não cria sessão** na 1ª chamada; sinaliza que precisa de 2FA.
- Opção simples: `LoginRequest` ganha `codigo_2fa: Optional[str]`. Se 2FA ativo e código ausente/errado → 401 com um marcador (ex.: `detail="2fa_requerido"` e status 401, ou um campo no corpo). O front, ao ver isso, mostra o campo de código e reenvia email+senha+codigo.
- Atenção: a tentativa com 2FA pendente conta no rate limit? Decida (sugestão: senha correta + 2FA pendente NÃO conta como falha de senha).
- Frontend: `pages/login.tsx` ganha o 2º passo (campo de código). `pages/conta.tsx` ganha a seção "Ativar 2FA" (mostra QR via lib JS de QR a partir da URI, confirma código, mostra backup codes).
- Teste: `tests/test_auth_2fa_api.py` (setup→ativar→login 2 etapas→backup code).

</details>

---

## 4. ✅ FEITO — financas deriva `usuario_id` da sessão (Step B)

**Por quê:** antes `/api/financas/*` recebia `usuario_id` por query string / corpo. Com só o Pablo, ok; mas a Sandra poderia trocar o parâmetro e ver dados de outro perfil. Agora o dono é **sempre o logado**.

**O que foi feito:**
- Nova dependency `app/api/dependencies/financas.py`: `usuario_financas` (login + `financas.ver`), `financas_usuario_id` (→ `str(usuario.id)` da sessão) e `exige_editar` (`financas.editar`).
- Todos os 13 routers de `financas/*` endurecidos: GET de listagem usa `Depends(financas_usuario_id)`; POST/Form **sobrescrevem `body.usuario_id`** com o da sessão (corpo forjado é ignorado) e exigem `exige_editar`; GET/PATCH/DELETE por id exigem login+permissão.
- **Bot do Telegram intacto** (chama os services direto, com `usuario_id` do `mapa_chat_usuario`; não passa pelos routers HTTP).
- Front (`lib/financas.ts`): valor `FINANCAS_USUARIO_ID` agora é só payload — o backend ignora. Build/typecheck verdes, sem mudança funcional.
- Testes: helper `tests/_financas_auth.py` (override de auth via `app.dependency_overrides`) aplicado nos ~16 smoke tests de financas; novo `tests/test_financas_auth_api.py` cobre o fluxo real (login/cookie/CSRF, 401, forja ignorada, 403).

**Exceções deliberadas (não feitas de propósito):**
- `POST /api/financas/recorrencias/processar` é endpoint de **job** (cron, `usuario_id=None` = todos os perfis) → segue **sem** derivar da sessão. Se um dia for exposto publicamente, endurecer à parte.
- GET/PATCH/DELETE **por id** (`/contas/{id}`, `/cartoes/{id}`, `/transacoes/{id}`, `/compras/{id}`) exigem login+permissão mas **não checam ownership** do recurso pelo `usuario_id` (id é UUID aleatório). Endurecer (checar dono no service) se a Sandra precisar de garantia mais forte.

**Pendência pré-existente avistada:** `tests/test_auth_me_logout_api.py` (Step 4) falha em isolamento — faz `logout` sem `X-CSRF-Token`, que o B8 passou a exigir. É só atualizar o teste pra mandar o header. Não tocado aqui.

---

## 5. Deploy (Step 30 do financas) — checklist

Banco: **um Postgres só** (`reative-db`), database `reative`, schemas `public`/`financas`/`auth`. Não há banco novo.

1. No VPS, em `deploy/.env`: conferir `ADMIN_EMAIL`, `ADMIN_SENHA_INICIAL`, `SESSION_COOKIE_SECURE=true`, `TELEGRAM_USUARIO_ID`, e **gerar `TOTP_ENC_KEY`** (`python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`). ⚠️ Não troque essa chave depois que alguém ativar o 2FA. O compose já injeta a var.
2. `./scripts/02-deploy.sh` (build api+web). O container da API roda `alembic upgrade head` no start → cria os schemas/tabelas sozinho.
3. Uma vez: `docker compose exec api python -m app.jobs.seed_admin`.
4. `./scripts/set-telegram-webhook.sh` (liga o webhook HTTPS do bot).
5. Criar buckets no MinIO (comprovantes) — ver RUNBOOK.
6. Logar em `https://<DOMINIO>/login`, **trocar a senha** do admin na tela `/conta`, e (recomendado) ativar 2FA quando estiver pronto.
7. Conferir os headers de segurança (`curl -I https://<DOMINIO>`) — HSTS/CSP/X-Frame-Options.

> Nota: comprovantes do financas usam URL presignada do MinIO; o MinIO está exposto só no localhost do VPS. Se as imagens não carregarem no browser em produção, expor o MinIO atrás do Caddy (ex.: `/s3/*`) e ajustar `S3_ENDPOINT` público + o `img-src` do CSP. (Pendência pré-existente do financas, não do auth.)

---

## 6. Comando rápido para validar tudo de auth

```bash
cd backend && source venv/bin/activate
alembic upgrade head && alembic check
for t in test_auth_models test_auth_senha test_auth_login_api test_auth_me_logout_api \
         test_auth_rbac_api test_auth_pessoal_protegido_api test_auth_rate_limit_api \
         test_auth_csrf_api test_auth_auditoria_api test_auth_troca_senha_api \
         test_auth_admin_usuarios_api; do
  echo -n "$t → "; python -m tests.$t 2>&1 | grep -E "TUDO OK|AssertionError" | head -1; done
cd ../frontend && npm run typecheck && npm run build
```

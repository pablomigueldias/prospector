from __future__ import annotations

import asyncio
import uuid

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.api.main import app
from app.api.services.auth import senha_service
from app.config import settings

LOGIN = "/api/auth/login"
USUARIOS = "/api/admin/usuarios"
PAPEIS = "/api/admin/papeis"

SENHA = "adminUsersTeste-2026"
EMAIL_ADMIN = f"adm_{uuid.uuid4().hex[:8]}@x.com"
EMAIL_SANDRA = f"sandra_{uuid.uuid4().hex[:8]}@x.com"
SENHA_SANDRA = "sandraSenhaForte-2026"


def _csrf(client) -> str:
    return client.cookies.get("csrf_token") or client.cookies.get("__Host-csrf")


async def _criar_admin() -> str:
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.begin() as conn:
            uid = (await conn.execute(
                text("INSERT INTO auth.usuarios (email, senha_hash, nome) "
                     "VALUES (:e,:h,:n) RETURNING id"),
                {"e": EMAIL_ADMIN, "h": senha_service.hash_senha(SENHA), "n": "Admin"},
            )).scalar_one()
            pid = (await conn.execute(
                text("SELECT id FROM auth.papeis WHERE nome='admin'")
            )).scalar_one_or_none()
            assert pid, "rode o seed_admin (papel admin não existe)"
            await conn.execute(
                text("INSERT INTO auth.usuario_papeis (usuario_id,papel_id) VALUES (:u,:p)"),
                {"u": uid, "p": pid},
            )
            return str(uid)
    finally:
        await eng.dispose()


async def _cleanup(ids: list[str], emails: list[str]) -> None:
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.begin() as conn:
            await conn.execute(text("DELETE FROM auth.tentativas_login"))
            for e in emails:
                await conn.execute(text("DELETE FROM auth.usuarios WHERE email=:e"), {"e": e})
            for uid in ids:
                await conn.execute(text("DELETE FROM auth.usuarios WHERE id=:u"), {"u": uid})
    finally:
        await eng.dispose()


def smoke_test() -> None:
    print("━" * 60)
    print("Smoke test — auth Step E18 (admin de usuários)")
    print("━" * 60)

    id_admin = asyncio.run(_criar_admin())
    sandra_id = None

    with TestClient(app, base_url="https://testserver") as client:
        try:
            client.post(LOGIN, json={"email": EMAIL_ADMIN, "senha": SENHA})
            csrf = _csrf(client)

            # ── 1. papéis ─────────────────────────────────────────────
            print("\n→ Test 1: GET /papeis")
            r = client.get(PAPEIS)
            assert r.status_code == 200, r.text
            nomes = {p["nome"] for p in r.json()}
            assert {"admin", "padrao"} <= nomes, nomes
            print(f"   papéis: {sorted(nomes)}")

            # ── 2. cria Sandra (padrao) ───────────────────────────────
            print("\n→ Test 2: POST cria Sandra (padrao)")
            r = client.post(USUARIOS, headers={"X-CSRF-Token": csrf}, json={
                "email": EMAIL_SANDRA, "nome": "Sandra", "senha": SENHA_SANDRA,
                "papeis": ["padrao"],
            })
            assert r.status_code == 201, r.text
            sandra_id = r.json()["id"]
            assert r.json()["papeis"] == ["padrao"]
            print(f"   criada id={sandra_id} papeis={r.json()['papeis']}")

            # ── 3. email duplicado → 409 ──────────────────────────────
            print("\n→ Test 3: email duplicado → 409")
            r = client.post(USUARIOS, headers={"X-CSRF-Token": csrf}, json={
                "email": EMAIL_SANDRA, "nome": "Clone", "senha": SENHA_SANDRA,
            })
            assert r.status_code == 409, r.status_code

            # ── 4. senha fraca → 400 ──────────────────────────────────
            print("→ Test 4: senha fraca → 400")
            r = client.post(USUARIOS, headers={"X-CSRF-Token": csrf}, json={
                "email": f"x_{uuid.uuid4().hex[:6]}@x.com", "nome": "X", "senha": "fraca",
            })
            assert r.status_code == 400, r.status_code

            # ── 5. lista inclui Sandra ────────────────────────────────
            print("→ Test 5: GET lista")
            r = client.get(USUARIOS)
            emails = {u["email"] for u in r.json()["items"]}
            assert EMAIL_SANDRA in emails

            # ── 6. PATCH muda nome ────────────────────────────────────
            print("→ Test 6: PATCH nome")
            r = client.patch(f"{USUARIOS}/{sandra_id}", headers={"X-CSRF-Token": csrf},
                             json={"nome": "Sandra Silva"})
            assert r.status_code == 200 and r.json()["nome"] == "Sandra Silva", r.text

            # ── 7. Sandra (padrao) não acessa o admin → 403 ───────────
            print("→ Test 7: não-admin → 403")
            client.cookies.clear()
            client.post(LOGIN, json={"email": EMAIL_SANDRA, "senha": SENHA_SANDRA})
            assert client.get(USUARIOS).status_code == 403
            print("   Sandra barrada do admin ✓")

        finally:
            asyncio.run(_cleanup([id_admin], [EMAIL_SANDRA]))

    print("\n" + "━" * 60)
    print("TUDO OK — auth Step E18 funcionando!")
    print("━" * 60)


def main() -> None:
    smoke_test()


if __name__ == "__main__":
    main()

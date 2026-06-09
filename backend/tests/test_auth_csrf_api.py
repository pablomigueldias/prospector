from __future__ import annotations

import asyncio
import uuid

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.api.main import app
from app.api.services.auth import senha_service
from app.api.services.auth.cookie import cookie_name
from app.api.services.auth.csrf import csrf_cookie_name
from app.config import settings

LOGIN = "/api/auth/login"
LOGOUT = "/api/auth/logout"
EMAIL = f"csrf_{uuid.uuid4().hex[:8]}@x.com"
SENHA = "csrfTeste-Senha-2026"


async def _criar() -> str:
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.begin() as conn:
            return str((await conn.execute(
                text(
                    "INSERT INTO auth.usuarios (email, senha_hash, nome) "
                    "VALUES (:e, :h, :n) RETURNING id"
                ),
                {"e": EMAIL, "h": senha_service.hash_senha(SENHA), "n": "CSRF"},
            )).scalar_one())
    finally:
        await eng.dispose()


async def _cleanup(uid: str) -> None:
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.begin() as conn:
            await conn.execute(text("DELETE FROM auth.tentativas_login"))
            await conn.execute(text("DELETE FROM auth.usuarios WHERE id = :u"), {"u": uid})
    finally:
        await eng.dispose()


def smoke_test() -> None:
    print("━" * 60)
    print("Smoke test — auth Step B8 (CSRF double-submit)")
    print("━" * 60)

    uid = asyncio.run(_criar())

    with TestClient(app, base_url="https://testserver") as client:
        try:
            # ── login: não exige CSRF (sem cookie de sessão ainda) ────
            print("\n→ Test 1: login passa sem CSRF (não é alvo)")
            r = client.post(LOGIN, json={"email": EMAIL, "senha": SENHA})
            assert r.status_code == 200, r.text
            assert client.cookies.get(cookie_name())
            csrf = client.cookies.get(csrf_cookie_name())
            assert csrf, "login deveria setar o cookie CSRF"
            print(f"   login ok; cookies {cookie_name()} + {csrf_cookie_name()} setados")

            # ── mutação autenticada SEM header → 403 ──────────────────
            print("\n→ Test 2: POST autenticado sem X-CSRF-Token → 403")
            r = client.post(LOGOUT)
            assert r.status_code == 403, (r.status_code, r.text)
            assert "csrf" in r.json()["detail"].lower()
            print(f"   barrou: {r.json()['detail']!r}")

            # ── header errado → 403 ───────────────────────────────────
            print("\n→ Test 3: header CSRF errado → 403")
            r = client.post(LOGOUT, headers={"X-CSRF-Token": "valor-errado"})
            assert r.status_code == 403
            print("   header divergente barrado ✓")

            # ── header certo (== cookie) → 200 ────────────────────────
            print("\n→ Test 4: header CSRF correto → 200")
            r = client.post(LOGOUT, headers={"X-CSRF-Token": csrf})
            assert r.status_code == 200, (r.status_code, r.text)
            print("   logout com CSRF correto passou ✓")

        finally:
            asyncio.run(_cleanup(uid))

    print("\n" + "━" * 60)
    print("TUDO OK — auth Step B8 funcionando!")
    print("━" * 60)


def main() -> None:
    smoke_test()


if __name__ == "__main__":
    main()

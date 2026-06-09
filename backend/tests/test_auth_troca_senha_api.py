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
SENHA_URL = "/api/auth/senha"
ME = "/api/auth/me"
EMAIL = f"troca_{uuid.uuid4().hex[:8]}@x.com"
SENHA = "trocaSenhaTeste-2026"
NOVA = "novaSenhaForte-2026"


def _csrf(client) -> str:
    return client.cookies.get("csrf_token") or client.cookies.get("__Host-csrf")


async def _criar() -> str:
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.begin() as conn:
            return str((await conn.execute(
                text(
                    "INSERT INTO auth.usuarios (email, senha_hash, nome) "
                    "VALUES (:e, :h, :n) RETURNING id"
                ),
                {"e": EMAIL, "h": senha_service.hash_senha(SENHA), "n": "Troca"},
            )).scalar_one())
    finally:
        await eng.dispose()


async def _ativas(uid: str) -> int:
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.begin() as conn:
            return int((await conn.execute(
                text("SELECT count(*) FROM auth.sessoes WHERE usuario_id=:u AND revogada=false"),
                {"u": uid},
            )).scalar_one())
    finally:
        await eng.dispose()


async def _cleanup(uid: str) -> None:
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.begin() as conn:
            await conn.execute(text("DELETE FROM auth.tentativas_login"))
            await conn.execute(text("DELETE FROM auth.auditoria WHERE usuario_id=:u"), {"u": uid})
            await conn.execute(text("DELETE FROM auth.usuarios WHERE id=:u"), {"u": uid})
    finally:
        await eng.dispose()


def smoke_test() -> None:
    print("━" * 60)
    print("Smoke test — auth Step B10 (troca de senha)")
    print("━" * 60)

    asyncio.run(_cleanup_pre())
    uid = asyncio.run(_criar())

    with TestClient(app, base_url="https://testserver") as client:
        try:
            # duas sessões (dois "dispositivos")
            client.post(LOGIN, json={"email": EMAIL, "senha": SENHA})   # sessão A
            client.cookies.clear()
            client.post(LOGIN, json={"email": EMAIL, "senha": SENHA})   # sessao B (atual)
            assert asyncio.run(_ativas(uid)) == 2
            csrf = _csrf(client)
            print("\n→ 2 sessões ativas (A e B)")

            # ── 1. senha atual errada → 400 ───────────────────────────
            print("→ Test 1: senha atual errada → 400")
            r = client.post(SENHA_URL, json={"senha_atual": "errada", "senha_nova": NOVA},
                            headers={"X-CSRF-Token": csrf})
            assert r.status_code == 400, r.text

            # ── 2. nova senha fraca → 400 ─────────────────────────────
            print("→ Test 2: nova senha fraca → 400")
            r = client.post(SENHA_URL, json={"senha_atual": SENHA, "senha_nova": "curta"},
                            headers={"X-CSRF-Token": csrf})
            assert r.status_code == 400, r.text

            # ── 3. troca válida → 200, revoga a OUTRA sessão ──────────
            print("→ Test 3: troca válida → revoga outras, mantém a atual")
            r = client.post(SENHA_URL, json={"senha_atual": SENHA, "senha_nova": NOVA},
                            headers={"X-CSRF-Token": csrf})
            assert r.status_code == 200, r.text
            assert asyncio.run(_ativas(uid)) == 1  # só a atual (B) sobrou
            assert client.get(ME).status_code == 200  # sessão atual segue válida
            print(f"   {r.json()['mensagem']}")

            # ── 4. senha nova funciona; antiga não ────────────────────
            print("→ Test 4: login com a nova senha (e antiga falha)")
            client.cookies.clear()
            assert client.post(LOGIN, json={"email": EMAIL, "senha": NOVA}).status_code == 200
            client.cookies.clear()
            assert client.post(LOGIN, json={"email": EMAIL, "senha": SENHA}).status_code == 401
            print("   nova senha OK, antiga rejeitada ✓")

        finally:
            asyncio.run(_cleanup(uid))

    print("\n" + "━" * 60)
    print("TUDO OK — auth Step B10 funcionando!")
    print("━" * 60)


async def _cleanup_pre() -> None:
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.begin() as conn:
            await conn.execute(text("DELETE FROM auth.tentativas_login"))
    finally:
        await eng.dispose()


def main() -> None:
    smoke_test()


if __name__ == "__main__":
    main()

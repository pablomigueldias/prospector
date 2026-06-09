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
LOGOUT = "/api/auth/logout"
EMAIL = f"audit_{uuid.uuid4().hex[:8]}@x.com"
SENHA = "auditoriaTeste-2026"


async def _criar() -> str:
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.begin() as conn:
            return str((await conn.execute(
                text(
                    "INSERT INTO auth.usuarios (email, senha_hash, nome) "
                    "VALUES (:e, :h, :n) RETURNING id"
                ),
                {"e": EMAIL, "h": senha_service.hash_senha(SENHA), "n": "Audit"},
            )).scalar_one())
    finally:
        await eng.dispose()


async def _eventos(usuario_id: str) -> list[str]:
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.begin() as conn:
            rows = await conn.execute(
                text(
                    "SELECT evento FROM auth.auditoria "
                    "WHERE usuario_id = :u OR detalhe->>'email' = :e "
                    "ORDER BY created_at"
                ),
                {"u": usuario_id, "e": EMAIL},
            )
            return [r[0] for r in rows.fetchall()]
    finally:
        await eng.dispose()


async def _cleanup(uid: str) -> None:
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.begin() as conn:
            await conn.execute(text("DELETE FROM auth.tentativas_login"))
            await conn.execute(
                text("DELETE FROM auth.auditoria WHERE usuario_id = :u OR detalhe->>'email' = :e"),
                {"u": uid, "e": EMAIL},
            )
            await conn.execute(text("DELETE FROM auth.usuarios WHERE id = :u"), {"u": uid})
    finally:
        await eng.dispose()


def smoke_test() -> None:
    print("━" * 60)
    print("Smoke test — auth Step B9 (auditoria de eventos)")
    print("━" * 60)

    uid = asyncio.run(_criar())

    with TestClient(app, base_url="https://testserver") as client:
        try:
            # falha → login_falha
            print("\n→ Test 1: login falho grava login_falha")
            client.post(LOGIN, json={"email": EMAIL, "senha": "errada"})
            # sucesso → login_ok
            print("→ Test 2: login ok grava login_ok")
            client.post(LOGIN, json={"email": EMAIL, "senha": SENHA})
            csrf = client.cookies.get("csrf_token") or client.cookies.get("__Host-csrf")
            # logout → logout
            print("→ Test 3: logout grava logout")
            client.post(LOGOUT, headers={"X-CSRF-Token": csrf})

            eventos = asyncio.run(_eventos(uid))
            assert "login_falha" in eventos, eventos
            assert "login_ok" in eventos, eventos
            assert "logout" in eventos, eventos
            print(f"   eventos gravados: {eventos}")

        finally:
            asyncio.run(_cleanup(uid))

    print("\n" + "━" * 60)
    print("TUDO OK — auth Step B9 funcionando!")
    print("━" * 60)


def main() -> None:
    smoke_test()


if __name__ == "__main__":
    main()

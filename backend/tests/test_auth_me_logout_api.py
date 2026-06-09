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
ME = "/api/auth/me"
LOGOUT = "/api/auth/logout"
LOGOUT_ALL = "/api/auth/logout-all"

EMAIL = f"me_{uuid.uuid4().hex[:8]}@reativesystems.com.br"
SENHA = "meLogoutTeste-2026"


async def _criar_usuario() -> str:
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.begin() as conn:
            row = await conn.execute(
                text(
                    "INSERT INTO auth.usuarios (email, senha_hash, nome) "
                    "VALUES (:e, :h, :n) RETURNING id"
                ),
                {"e": EMAIL, "h": senha_service.hash_senha(SENHA), "n": "Me Teste"},
            )
            return str(row.scalar_one())
    finally:
        await eng.dispose()


async def _sessoes_ativas(usuario_id: str) -> int:
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.begin() as conn:
            row = await conn.execute(
                text(
                    "SELECT count(*) FROM auth.sessoes "
                    "WHERE usuario_id = :u AND revogada = false"
                ),
                {"u": usuario_id},
            )
            return int(row.scalar_one())
    finally:
        await eng.dispose()


async def _cleanup(usuario_id: str) -> None:
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.begin() as conn:
            await conn.execute(
                text("DELETE FROM auth.usuarios WHERE id = :u"), {"u": usuario_id}
            )
    finally:
        await eng.dispose()


def smoke_test() -> None:
    print("━" * 60)
    print("Smoke test — auth Step 4 (usuario_atual + /me + logout)")
    print("━" * 60)

    usuario_id = asyncio.run(_criar_usuario())

    with TestClient(app, base_url="https://testserver") as client:
        try:
            # ── 1. /me sem cookie → 401 ───────────────────────────────
            print("\n→ Test 1: /me sem sessão → 401")
            assert client.get(ME).status_code == 401
            print("   barrou anônimo ✓")

            # ── 2. login → /me devolve o usuário ──────────────────────
            print("\n→ Test 2: login + /me")
            assert client.post(LOGIN, json={"email": EMAIL, "senha": SENHA}).status_code == 200
            rme = client.get(ME)
            assert rme.status_code == 200, rme.text
            assert rme.json()["email"] == EMAIL
            assert rme.json()["permissoes"] == []  # RBAC ainda não
            print(f"   /me ok: {rme.json()['nome']!r}")

            # ── 3. logout revoga e /me volta 401 ──────────────────────
            print("\n→ Test 3: logout → /me 401")
            assert client.post(LOGOUT).status_code == 200
            client.cookies.clear()
            assert client.get(ME).status_code == 401
            assert asyncio.run(_sessoes_ativas(usuario_id)) == 0
            print("   sessão revogada, /me 401 ✓")

            # ── 4. duas sessões + logout-all revoga todas ─────────────
            print("\n→ Test 4: logout-all (sair de todos os dispositivos)")
            client.post(LOGIN, json={"email": EMAIL, "senha": SENHA})  # sessão 1
            tok1 = client.cookies.get("__Host-sessao") or client.cookies.get("sessao")
            client.cookies.clear()
            client.post(LOGIN, json={"email": EMAIL, "senha": SENHA})  # sessão 2 (cookie atual)
            assert asyncio.run(_sessoes_ativas(usuario_id)) == 2
            r = client.post(LOGOUT_ALL)
            assert r.status_code == 200, r.text
            assert asyncio.run(_sessoes_ativas(usuario_id)) == 0
            print(f"   {r.json()['mensagem']} — 0 sessões ativas ✓")
            _ = tok1

        finally:
            asyncio.run(_cleanup(usuario_id))

    print("\n" + "━" * 60)
    print("TUDO OK — auth Step 4 funcionando!")
    print("━" * 60)


def main() -> None:
    smoke_test()


if __name__ == "__main__":
    main()

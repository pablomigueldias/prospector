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
SENHA = "rateLimitTeste-2026"
EMAIL = f"rl_{uuid.uuid4().hex[:8]}@x.com"


async def _criar_usuario() -> str:
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.begin() as conn:
            return str((await conn.execute(
                text(
                    "INSERT INTO auth.usuarios (email, senha_hash, nome) "
                    "VALUES (:e, :h, :n) RETURNING id"
                ),
                {"e": EMAIL, "h": senha_service.hash_senha(SENHA), "n": "RL"},
            )).scalar_one())
    finally:
        await eng.dispose()


async def _limpar(usuario_id: str | None = None) -> None:
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.begin() as conn:
            await conn.execute(text("DELETE FROM auth.tentativas_login"))
            if usuario_id:
                await conn.execute(
                    text("DELETE FROM auth.usuarios WHERE id = :u"), {"u": usuario_id}
                )
    finally:
        await eng.dispose()


def smoke_test() -> None:
    print("━" * 60)
    print("Smoke test — auth Step B7 (rate limit + lockout)")
    print("━" * 60)

    asyncio.run(_limpar())
    usuario_id = asyncio.run(_criar_usuario())

    with TestClient(app, base_url="https://testserver") as client:
        try:
            # ── 1. Lockout por conta: 5 falhas → 6ª barra (mesmo c/ senha certa)
            print("\n→ Test 1: 5 falhas na conta → lockout (429)")
            for i in range(5):
                r = client.post(LOGIN, json={"email": EMAIL, "senha": "errada-xyz"})
                assert r.status_code == 401, (i, r.status_code)
            # 6ª tentativa, AGORA com a senha CERTA → ainda bloqueado
            r = client.post(LOGIN, json={"email": EMAIL, "senha": SENHA})
            assert r.status_code == 429, (r.status_code, r.text)
            print(f"   5×401 e depois 429 (lockout vence até senha certa): {r.json()['detail']!r}")

            # ── 2. Limite por IP: 10 falhas (emails distintos) → 11ª barra ──
            print("\n→ Test 2: 10 falhas do mesmo IP (emails distintos) → 429 por IP")
            asyncio.run(_limpar())  # zera contadores
            for i in range(10):
                r = client.post(
                    LOGIN, json={"email": f"naoexiste_{i}@x.com", "senha": "errada"}
                )
                assert r.status_code == 401, (i, r.status_code)
            r = client.post(LOGIN, json={"email": "naoexiste_11@x.com", "senha": "errada"})
            assert r.status_code == 429, (r.status_code, r.text)
            print(f"   10×401 e 11ª → 429 por IP: {r.json()['detail']!r}")

        finally:
            asyncio.run(_limpar(usuario_id))

    print("\n" + "━" * 60)
    print("TUDO OK — auth Step B7 funcionando!")
    print("━" * 60)


def main() -> None:
    smoke_test()


if __name__ == "__main__":
    main()

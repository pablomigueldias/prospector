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
PERFIL = "/api/pessoal/perfil"
VAGAS = "/api/pessoal/vagas"

SENHA = "pessoalTeste-2026"
EMAIL_ADMIN = f"pess_admin_{uuid.uuid4().hex[:8]}@x.com"
EMAIL_PADRAO = f"pess_padrao_{uuid.uuid4().hex[:8]}@x.com"


async def _criar(email: str, papel: str) -> str:
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.begin() as conn:
            uid = (await conn.execute(
                text(
                    "INSERT INTO auth.usuarios (email, senha_hash, nome) "
                    "VALUES (:e, :h, :n) RETURNING id"
                ),
                {"e": email, "h": senha_service.hash_senha(SENHA), "n": email},
            )).scalar_one()
            pid = (await conn.execute(
                text("SELECT id FROM auth.papeis WHERE nome = :p"), {"p": papel}
            )).scalar_one_or_none()
            assert pid is not None, f"papel {papel!r} não existe — rode o seed_admin"
            await conn.execute(
                text("INSERT INTO auth.usuario_papeis (usuario_id, papel_id) VALUES (:u,:p)"),
                {"u": uid, "p": pid},
            )
            return str(uid)
    finally:
        await eng.dispose()


async def _cleanup(ids: list[str]) -> None:
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.begin() as conn:
            for uid in ids:
                await conn.execute(
                    text("DELETE FROM auth.usuarios WHERE id = :u"), {"u": uid}
                )
    finally:
        await eng.dispose()


def smoke_test() -> None:
    print("━" * 60)
    print("Smoke test — auth Step 7 (/api/pessoal/* exige pessoal.ver)")
    print("━" * 60)

    id_admin = asyncio.run(_criar(EMAIL_ADMIN, "admin"))
    id_padrao = asyncio.run(_criar(EMAIL_PADRAO, "padrao"))

    with TestClient(app, base_url="https://testserver") as client:
        try:
            # ── 1. anônimo → 401 ──────────────────────────────────────
            print("\n→ Test 1: anônimo → 401")
            assert client.get(PERFIL).status_code == 401
            assert client.get(VAGAS).status_code == 401
            print("   perfil e vagas barram anônimo ✓")

            # ── 2. padrao (sem pessoal.ver) → 403 ─────────────────────
            print("\n→ Test 2: 'padrao' → 403")
            client.post(LOGIN, json={"email": EMAIL_PADRAO, "senha": SENHA})
            assert client.get(PERFIL).status_code == 403
            assert client.get(VAGAS).status_code == 403
            print("   Sandra (padrao) NÃO vê a área pessoal ✓")

            # ── 3. admin (com pessoal.ver) → 200 ──────────────────────
            print("\n→ Test 3: 'admin' → 200")
            client.cookies.clear()
            client.post(LOGIN, json={"email": EMAIL_ADMIN, "senha": SENHA})
            assert client.get(PERFIL).status_code == 200
            assert client.get(VAGAS).status_code == 200
            print("   Pablo (admin) vê a área pessoal ✓")

        finally:
            asyncio.run(_cleanup([id_admin, id_padrao]))

    print("\n" + "━" * 60)
    print("TUDO OK — auth Step 7 funcionando!")
    print("━" * 60)


def main() -> None:
    smoke_test()


if __name__ == "__main__":
    main()

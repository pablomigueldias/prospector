from __future__ import annotations

import asyncio
import uuid

from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.api.dependencies.auth import require_permission
from app.api.main import app
from app.api.services.auth import senha_service
from app.api.services.auth.permissoes import PADRAO
from app.config import settings

LOGIN = "/api/auth/login"
ME = "/api/auth/me"
# Rota protegida só pra este teste (exige pessoal.ver).
TEST_PATH = "/api/_test_rbac_pessoal"

SENHA = "rbacTeste-Senha-2026"
EMAIL_ADMIN = f"rbac_admin_{uuid.uuid4().hex[:8]}@x.com"
EMAIL_PADRAO = f"rbac_padrao_{uuid.uuid4().hex[:8]}@x.com"


async def _protegido() -> dict:
    return {"ok": True}


app.add_api_route(
    TEST_PATH, _protegido, methods=["GET"],
    dependencies=[Depends(require_permission("pessoal.ver"))],
)


async def _criar_usuario_com_papel(email: str, papel_nome: str) -> str:
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
                text("SELECT id FROM auth.papeis WHERE nome = :p"), {"p": papel_nome}
            )).scalar_one_or_none()
            assert pid is not None, f"papel {papel_nome!r} não existe — rode o seed_admin"
            await conn.execute(
                text(
                    "INSERT INTO auth.usuario_papeis (usuario_id, papel_id) "
                    "VALUES (:u, :p)"
                ),
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
    print("Smoke test — auth Step 5 (RBAC: require_permission + /me)")
    print("━" * 60)

    id_admin = asyncio.run(_criar_usuario_com_papel(EMAIL_ADMIN, "admin"))
    id_padrao = asyncio.run(_criar_usuario_com_papel(EMAIL_PADRAO, "padrao"))

    with TestClient(app, base_url="https://testserver") as client:
        try:
            # ── 1. padrao: /me sem pessoal.ver ────────────────────────
            print("\n→ Test 1: usuário 'padrao' — permissões e 403")
            assert client.post(LOGIN, json={"email": EMAIL_PADRAO, "senha": SENHA}).status_code == 200
            perms = client.get(ME).json()["permissoes"]
            assert set(perms) == PADRAO, perms
            assert "pessoal.ver" not in perms
            assert "usuarios.gerenciar" not in perms
            r = client.get(TEST_PATH)
            assert r.status_code == 403, (r.status_code, r.text)
            print(f"   permissoes={sorted(perms)} ; rota protegida → 403 ✓")

            # ── 2. admin: tem tudo, passa na rota ─────────────────────
            print("\n→ Test 2: usuário 'admin' — permissões e 200")
            client.cookies.clear()
            rlogin = client.post(LOGIN, json={"email": EMAIL_ADMIN, "senha": SENHA})
            assert rlogin.status_code == 200
            # o próprio login já devolve as permissões (não só o /me)
            assert "pessoal.ver" in rlogin.json()["permissoes"], rlogin.json()["permissoes"]
            perms_admin = client.get(ME).json()["permissoes"]
            assert "pessoal.ver" in perms_admin
            assert "usuarios.gerenciar" in perms_admin
            assert client.get(TEST_PATH).status_code == 200
            print(f"   admin tem {len(perms_admin)} permissões ; rota protegida → 200 ✓")

            # ── 3. anônimo na rota protegida → 401 ────────────────────
            print("\n→ Test 3: anônimo → 401 (antes da checagem de permissão)")
            client.cookies.clear()
            assert client.get(TEST_PATH).status_code == 401
            print("   anônimo barrado ✓")

        finally:
            asyncio.run(_cleanup([id_admin, id_padrao]))

    print("\n" + "━" * 60)
    print("TUDO OK — auth Step 5 funcionando!")
    print("━" * 60)


def main() -> None:
    smoke_test()


if __name__ == "__main__":
    main()

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
EMAIL = f"login_{uuid.uuid4().hex[:8]}@reativesystems.com.br"
SENHA = "loginTest-Senha-2026"


async def _criar_usuario() -> str:
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.begin() as conn:
            row = await conn.execute(
                text(
                    "INSERT INTO auth.usuarios (email, senha_hash, nome) "
                    "VALUES (:e, :h, :n) RETURNING id"
                ),
                {"e": EMAIL, "h": senha_service.hash_senha(SENHA), "n": "Login Teste"},
            )
            return str(row.scalar_one())
    finally:
        await eng.dispose()


async def _conta_sessoes(usuario_id: str) -> int:
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.begin() as conn:
            row = await conn.execute(
                text("SELECT count(*) FROM auth.sessoes WHERE usuario_id = :u"),
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
    print("Smoke test — auth Step 3 (login + cookie + sessão opaca)")
    print("━" * 60)

    usuario_id = asyncio.run(_criar_usuario())
    cookie_name = "__Host-sessao" if settings.session_cookie_secure else "sessao"

    # base_url https → o cookie Secure entra no cookie jar do cliente.
    with TestClient(app, base_url="https://testserver") as client:
        try:
            # ── 1. Login correto seta cookie + cria sessão ────────────
            print("\n→ Test 1: login correto")
            r = client.post(LOGIN, json={"email": EMAIL, "senha": SENHA})
            assert r.status_code == 200, (r.status_code, r.text)
            assert r.json()["email"] == EMAIL
            set_cookie = r.headers.get("set-cookie", "")
            assert cookie_name in set_cookie, set_cookie
            assert "httponly" in set_cookie.lower(), set_cookie
            assert client.cookies.get(cookie_name), "cookie não entrou no jar"
            assert asyncio.run(_conta_sessoes(usuario_id)) == 1
            print(f"   200, cookie {cookie_name} httpOnly setado, 1 sessão no banco")

            # ── 2. Token guardado como HASH, não em texto ─────────────
            print("\n→ Test 2: token no banco é hash (não o do cookie)")
            token_cookie = client.cookies.get(cookie_name)
            eng = create_async_engine(settings.database_url)
            try:
                got = asyncio.run(_token_hash_no_banco(eng, usuario_id))
            finally:
                pass
            assert token_cookie not in got, "token em texto não pode estar no banco"
            assert len(got[0]) == 64, "token_hash deveria ser sha256 hex (64)"
            print("   banco guarda só o sha256 ✓")

            # ── 3. Senha errada → 401 genérico ────────────────────────
            print("\n→ Test 3: senha errada → 401")
            client.cookies.clear()
            rbad = client.post(LOGIN, json={"email": EMAIL, "senha": "errada-demais-123"})
            assert rbad.status_code == 401, rbad.status_code
            assert rbad.json()["detail"] == "Email ou senha inválidos."
            print(f"   barrou: {rbad.json()['detail']!r}")

            # ── 4. Email inexistente → 401 (mesma mensagem) ───────────
            print("\n→ Test 4: email inexistente → 401 (anti-enumeração)")
            rno = client.post(
                LOGIN, json={"email": "naoexiste@x.com", "senha": SENHA}
            )
            assert rno.status_code == 401
            assert rno.json()["detail"] == "Email ou senha inválidos."
            print("   mesma mensagem genérica ✓")

        finally:
            asyncio.run(_cleanup(usuario_id))

    print("\n" + "━" * 60)
    print("TUDO OK — auth Step 3 funcionando!")
    print("━" * 60)


async def _token_hash_no_banco(eng, usuario_id: str) -> list[str]:
    async with eng.begin() as conn:
        rows = await conn.execute(
            text("SELECT token_hash FROM auth.sessoes WHERE usuario_id = :u"),
            {"u": usuario_id},
        )
        out = [r[0] for r in rows.fetchall()]
    await eng.dispose()
    return out


def main() -> None:
    smoke_test()


if __name__ == "__main__":
    main()

"""Smoke test do login em 2 etapas com 2FA ativo (Step D17).

Ativa o 2FA pela API (como o usuário faria na tela /conta), desloga e então
exercita o /login: sem código → 401 2fa_requerido; código errado → 401;
TOTP correto → 200; backup code → 200 e de uso único.
"""
from __future__ import annotations

import asyncio
import uuid

import pyotp
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.api.main import app
from app.api.services.auth import senha_service
from app.api.services.auth.csrf import csrf_cookie_name
from app.config import settings

LOGIN = "/api/auth/login"
EMAIL = f"twofalogin_{uuid.uuid4().hex[:8]}@x.com"
SENHA = "Login2Etapas-Senha-2026"


async def _criar() -> str:
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.begin() as conn:
            return str((await conn.execute(
                text("INSERT INTO auth.usuarios (email, senha_hash, nome) "
                     "VALUES (:e, :h, :n) RETURNING id"),
                {"e": EMAIL, "h": senha_service.hash_senha(SENHA), "n": "TwoFALogin"},
            )).scalar_one())
    finally:
        await eng.dispose()


async def _cleanup(uid: str) -> None:
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.begin() as conn:
            await conn.execute(text("DELETE FROM auth.usuario_2fa WHERE usuario_id = :u"), {"u": uid})
            await conn.execute(text("DELETE FROM auth.tentativas_login"))
            await conn.execute(text("DELETE FROM auth.usuarios WHERE id = :u"), {"u": uid})
    finally:
        await eng.dispose()


def smoke_test() -> None:
    print("━" * 60)
    print("Smoke test — auth Step D17 (login em 2 etapas com 2FA)")
    print("━" * 60)

    uid = asyncio.run(_criar())

    with TestClient(app, base_url="https://testserver") as client:
        try:
            # ── ativa o 2FA pela API ──────────────────────────────────
            client.post(LOGIN, json={"email": EMAIL, "senha": SENHA})

            def csrf() -> dict:
                return {"X-CSRF-Token": client.cookies.get(csrf_cookie_name())}

            secret = client.post("/api/auth/2fa/setup", headers=csrf()).json()["secret"]
            codes = client.post(
                "/api/auth/2fa/ativar",
                json={"codigo": pyotp.TOTP(secret).now()}, headers=csrf(),
            ).json()["backup_codes"]
            client.post("/api/auth/logout", headers=csrf())
            client.cookies.clear()
            print("   2FA ativado; deslogado")

            # ── 1. login só com senha → 401 2fa_requerido ─────────────
            print("\n→ Test 1: login sem código → 401 2fa_requerido")
            r = client.post(LOGIN, json={"email": EMAIL, "senha": SENHA})
            assert r.status_code == 401, r.text
            assert r.json()["detail"] == "2fa_requerido", r.json()
            assert not client.cookies.get("sessao"), "não devia abrir sessão"
            print("   marcador 2fa_requerido ✓ (sem sessão)")
            client.cookies.clear()

            # ── 2. senha + código errado → 401 ────────────────────────
            print("\n→ Test 2: código errado → 401")
            r = client.post(LOGIN, json={"email": EMAIL, "senha": SENHA, "codigo_2fa": "000000"})
            assert r.status_code == 401, r.text
            assert r.json()["detail"] != "2fa_requerido"
            print(f"   barrou: {r.json()['detail']!r}")
            client.cookies.clear()

            # ── 3. senha + TOTP correto → 200 ─────────────────────────
            print("\n→ Test 3: senha + TOTP correto → 200")
            r = client.post(LOGIN, json={
                "email": EMAIL, "senha": SENHA, "codigo_2fa": pyotp.TOTP(secret).now(),
            })
            assert r.status_code == 200, r.text
            assert r.json()["twofa_ativado"] is True
            assert client.cookies.get("sessao"), "deveria abrir sessão"
            print("   logou com TOTP ✓")
            client.cookies.clear()

            # ── 4. backup code → 200, e de uso único ──────────────────
            print("\n→ Test 4: login com backup code (uso único)")
            r = client.post(LOGIN, json={"email": EMAIL, "senha": SENHA, "codigo_2fa": codes[0]})
            assert r.status_code == 200, r.text
            client.cookies.clear()
            # reusar o mesmo backup code → 401
            r = client.post(LOGIN, json={"email": EMAIL, "senha": SENHA, "codigo_2fa": codes[0]})
            assert r.status_code == 401, r.text
            print("   backup code logou e não vale 2ª vez ✓")

        finally:
            asyncio.run(_cleanup(uid))

    print("\n" + "━" * 60)
    print("TUDO OK — auth Step D17 (login em 2 etapas) funcionando!")
    print("━" * 60)


def main() -> None:
    smoke_test()


if __name__ == "__main__":
    main()

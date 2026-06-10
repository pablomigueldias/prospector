"""Smoke test do 2FA (TOTP) — gestão: setup, ativar, backup codes, desativar.

O login em 2 etapas é coberto em `test_auth_2fa_login_api.py` (Step D17).
Usa login real (cookie + CSRF) e calcula o TOTP com pyotp, como faria o app
autenticador.
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

SETUP = "/api/auth/2fa/setup"
ATIVAR = "/api/auth/2fa/ativar"
DESATIVAR = "/api/auth/2fa/desativar"
ME = "/api/auth/me"
EMAIL = f"twofa_{uuid.uuid4().hex[:8]}@x.com"
SENHA = "DoisFatores-Senha-2026"


async def _criar() -> str:
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.begin() as conn:
            return str((await conn.execute(
                text("INSERT INTO auth.usuarios (email, senha_hash, nome) "
                     "VALUES (:e, :h, :n) RETURNING id"),
                {"e": EMAIL, "h": senha_service.hash_senha(SENHA), "n": "TwoFA"},
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


def _login(client: TestClient) -> str:
    r = client.post("/api/auth/login", json={"email": EMAIL, "senha": SENHA})
    assert r.status_code == 200, r.text
    return client.cookies.get(csrf_cookie_name())


def smoke_test() -> None:
    print("━" * 60)
    print("Smoke test — auth Step D15/D16 (2FA: setup/ativar/backup/desativar)")
    print("━" * 60)

    uid = asyncio.run(_criar())

    with TestClient(app, base_url="https://testserver") as client:
        try:
            _login(client)
            # o cookie CSRF rotaciona a cada /me, então leia sempre o atual
            def h() -> dict:
                return {"X-CSRF-Token": client.cookies.get(csrf_cookie_name())}

            # ── 1. setup devolve secret + otpauth + QR (ainda pendente) ─
            print("\n→ Test 1: POST /2fa/setup")
            r = client.post(SETUP, headers=h())
            assert r.status_code == 200, r.text
            dados = r.json()
            secret = dados["secret"]
            assert dados["otpauth_uri"].startswith("otpauth://totp/")
            assert dados["qr_data_uri"].startswith("data:image/png;base64,")
            # ainda NÃO ativo
            assert client.get(ME).json()["twofa_ativado"] is False
            print(f"   secret recebido; QR {len(dados['qr_data_uri'])} bytes; pendente ✓")

            # ── 2. código errado → 400 ────────────────────────────────
            print("\n→ Test 2: ativar com código errado → 400")
            r = client.post(ATIVAR, json={"codigo": "000000"}, headers=h())
            assert r.status_code == 400, r.text
            print(f"   barrou: {r.json()['detail']!r}")

            # ── 3. ativar com TOTP correto → backup codes ─────────────
            print("\n→ Test 3: ativar com TOTP correto")
            codigo = pyotp.TOTP(secret).now()
            r = client.post(ATIVAR, json={"codigo": codigo}, headers=h())
            assert r.status_code == 200, r.text
            codes = r.json()["backup_codes"]
            assert len(codes) == 10, codes
            assert client.get(ME).json()["twofa_ativado"] is True
            print(f"   ativo ✓ ; {len(codes)} backup codes (ex.: {codes[0]})")

            # ── 4. setup de novo (já ativo) → 400 ─────────────────────
            print("\n→ Test 4: setup com 2FA já ativo → 400")
            assert client.post(SETUP, headers=h()).status_code == 400
            print("   recusou re-setup ✓")

            # ── 5. desativar: senha errada → 400, código errado → 400 ─
            print("\n→ Test 5: desativar barra senha/código errados")
            assert client.post(DESATIVAR, json={
                "senha": "errada", "codigo": pyotp.TOTP(secret).now()}, headers=h()
            ).status_code == 400
            assert client.post(DESATIVAR, json={
                "senha": SENHA, "codigo": "000000"}, headers=h()
            ).status_code == 400
            print("   senha errada e código errado barrados ✓")

            # ── 6. desativar com senha + BACKUP code (uso único) ──────
            print("\n→ Test 6: desativar com senha + backup code")
            r = client.post(DESATIVAR, json={"senha": SENHA, "codigo": codes[0]}, headers=h())
            assert r.status_code == 200, r.text
            assert client.get(ME).json()["twofa_ativado"] is False
            print("   2FA desativado via backup code ✓")

        finally:
            asyncio.run(_cleanup(uid))

    print("\n" + "━" * 60)
    print("TUDO OK — auth Step D15/D16 (2FA gestão) funcionando!")
    print("━" * 60)


def main() -> None:
    smoke_test()


if __name__ == "__main__":
    main()

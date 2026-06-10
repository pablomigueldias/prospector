"""Smoke test do endurecimento do financas (Step B do AUTH_CONTINUACAO).

Cobre o fluxo REAL (com login/cookie/CSRF), complementando os demais testes
de financas que usam `dependency_overrides`:

1. Sem cookie de sessão → 401 nas rotas de financas.
2. Logado: o dono dos dados é a SESSÃO — `usuario_id` forjado no corpo é
   ignorado (a conta nasce com o id do logado).
3. Usuário sem permissão `financas.ver` → 403.
4. Mutação logada exige CSRF (header X-CSRF-Token).
"""
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

# NB: assume que `python -m app.jobs.seed_admin` já rodou (papel 'padrao' +
# permissões financas.* existem) — mesmo pressuposto dos demais testes de auth.
# Não chamamos seed() aqui de propósito: ele usa o engine global e prenderia o
# pool ao loop temporário (ver convenção #2 do AUTH_CONTINUACAO.md).
CONTAS = "/api/financas/contas"
SENHA = "Financas-Endurece-2026"


async def _criar_usuario(*, com_papel: bool) -> tuple[str, str]:
    """Cria um usuário; se ``com_papel``, liga ao papel 'padrao' (tem financas.*)."""
    email = f"finauth_{uuid.uuid4().hex[:8]}@x.com"
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.begin() as conn:
            uid = str((await conn.execute(
                text(
                    "INSERT INTO auth.usuarios (email, senha_hash, nome) "
                    "VALUES (:e, :h, :n) RETURNING id"
                ),
                {"e": email, "h": senha_service.hash_senha(SENHA), "n": "FinAuth"},
            )).scalar_one())
            if com_papel:
                await conn.execute(
                    text(
                        "INSERT INTO auth.usuario_papeis (usuario_id, papel_id) "
                        "SELECT :u, id FROM auth.papeis WHERE nome = 'padrao'"
                    ),
                    {"u": uid},
                )
        return uid, email
    finally:
        await eng.dispose()


async def _cleanup(uids: list[str]) -> None:
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.begin() as conn:
            for uid in uids:
                await conn.execute(
                    text("DELETE FROM financas.contas WHERE usuario_id = :u"), {"u": uid}
                )
            await conn.execute(text("DELETE FROM auth.tentativas_login"))
            for uid in uids:
                await conn.execute(
                    text("DELETE FROM auth.usuarios WHERE id = :u"), {"u": uid}
                )
    finally:
        await eng.dispose()


def _login(client: TestClient, email: str) -> str:
    r = client.post("/api/auth/login", json={"email": email, "senha": SENHA})
    assert r.status_code == 200, r.text
    assert client.cookies.get(cookie_name())
    return client.cookies.get(csrf_cookie_name())


def smoke_test() -> None:
    print("━" * 60)
    print("Smoke test — financas Step B (usuario_id derivado da sessão)")
    print("━" * 60)

    uid, email = asyncio.run(_criar_usuario(com_papel=True))
    uid_sem, email_sem = asyncio.run(_criar_usuario(com_papel=False))

    with TestClient(app, base_url="https://testserver") as client:
        try:
            # ── 1. Sem login → 401 ────────────────────────────────────
            print("\n→ Test 1: GET sem cookie → 401")
            r = client.get(CONTAS)
            assert r.status_code == 401, (r.status_code, r.text)
            print("   401 ok")

            # ── 2. Logado: dono = sessão (ignora usuario_id do corpo) ──
            print("\n→ Test 2: POST forjando usuario_id → nasce com o id do logado")
            csrf = _login(client, email)
            forjado = str(uuid.uuid4())
            r = client.post(CONTAS, json={
                "usuario_id": forjado, "nome": "Nubank",
                "tipo": "corrente", "saldo_atual": 10,
            }, headers={"X-CSRF-Token": csrf})
            assert r.status_code == 201, r.text
            assert r.json()["usuario_id"] == uid, (r.json()["usuario_id"], uid)
            assert r.json()["usuario_id"] != forjado
            print(f"   conta nasceu com usuario_id={uid[:8]} (forjado {forjado[:8]} ignorado)")

            # a listagem (também derivada da sessão) enxerga a conta
            rl = client.get(CONTAS)
            assert rl.status_code == 200 and rl.json()["total"] == 1, rl.text
            print("   GET lista pela sessão ✓")

            # ── 3. Mutação logada sem CSRF → 403 ──────────────────────
            print("\n→ Test 3: POST logado sem X-CSRF-Token → 403")
            r = client.post(CONTAS, json={
                "usuario_id": uid, "nome": "X", "tipo": "dinheiro",
            })
            assert r.status_code == 403, (r.status_code, r.text)
            print("   403 (CSRF) ok")

            # ── 4. Usuário sem financas.ver → 403 ─────────────────────
            print("\n→ Test 4: usuário sem permissão → 403")
            client.post("/api/auth/logout", headers={"X-CSRF-Token": csrf})
            _login(client, email_sem)
            r = client.get(CONTAS)
            assert r.status_code == 403, (r.status_code, r.text)
            print("   403 (permissão) ok")

        finally:
            asyncio.run(_cleanup([uid, uid_sem]))

    print("\n" + "━" * 60)
    print("TUDO OK — financas Step B (endurecimento do usuario_id) funcionando!")
    print("━" * 60)


def main() -> None:
    smoke_test()


if __name__ == "__main__":
    main()

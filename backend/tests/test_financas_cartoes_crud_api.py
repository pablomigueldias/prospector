"""Smoke test — editar e excluir cartão pela web.

Cobre:
  PATCH  /api/financas/cartoes/{id}
  DELETE /api/financas/cartoes/{id}
"""
from __future__ import annotations

import asyncio
import uuid

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.api.main import app
from app.config import settings
from tests._financas_auth import limpar_override, usar_usuario

CART = "/api/financas/cartoes"


async def _cleanup(ids: list[str]) -> None:
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.begin() as conn:
            for cid in ids:
                await conn.execute(
                    text("DELETE FROM financas.cartoes WHERE id = :id"),
                    {"id": cid},
                )
    finally:
        await eng.dispose()


def smoke_test() -> None:
    print("━" * 60)
    print("Smoke test — cartões: editar + excluir")
    print("━" * 60)

    usuario_id = str(uuid.uuid4())
    ids: list[str] = []

    with TestClient(app) as client:
        usar_usuario(usuario_id)
        try:
            r = client.post(CART, json={
                "usuario_id": usuario_id, "nome": "Nubank",
                "dia_fechamento": 28, "dia_vencimento": 5, "limite": 3000,
            })
            assert r.status_code == 201, r.text
            cid = r.json()["id"]
            ids.append(cid)
            assert r.json()["ativo"] is True
            print("\n→ criado (Nubank, fech 28, venc 5, limite 3000)")

            # ── 1. Edita limite + dias + inativa ──────────────────────
            print("→ Test 1: PATCH limite/dias/ativo")
            up = client.patch(f"{CART}/{cid}", json={
                "limite": 5000, "dia_fechamento": 20, "dia_vencimento": 1,
                "bandeira": "Mastercard", "ativo": False,
            })
            assert up.status_code == 200, up.text
            assert float(up.json()["limite"]) == 5000.0
            assert up.json()["dia_fechamento"] == 20
            assert up.json()["bandeira"] == "Mastercard"
            assert up.json()["ativo"] is False
            print("   ok: 5000 / fech 20 / venc 1 / Mastercard / inativo")

            # ── 2. Dia inválido → 422 ─────────────────────────────────
            print("→ Test 2: dia inválido → 422")
            assert client.patch(f"{CART}/{cid}", json={"dia_fechamento": 99}).status_code == 422

            # ── 3. Exclui ─────────────────────────────────────────────
            print("→ Test 3: DELETE")
            assert client.delete(f"{CART}/{cid}").status_code == 204
            assert client.get(CART).json()["total"] == 0
            ids.clear()
            print("   excluído; lista vazia")

            # ── 4. Excluir inexistente → 404 ──────────────────────────
            assert client.delete(f"{CART}/{uuid.uuid4()}").status_code == 404

        finally:
            limpar_override()
            asyncio.run(_cleanup(ids))

    print("\n" + "━" * 60)
    print("TUDO OK — editar/excluir cartão funcionando!")
    print("━" * 60)


def main() -> None:
    smoke_test()


if __name__ == "__main__":
    main()

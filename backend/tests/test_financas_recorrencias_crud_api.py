"""Smoke test — CRUD de recorrências pela web (editar + excluir, além de criar).

Cobre os endpoints novos:
  PATCH  /api/financas/recorrencias/{id}
  DELETE /api/financas/recorrencias/{id}
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

REC = "/api/financas/recorrencias"


async def _cleanup(rec_ids: list[str], usuario_id: str | None = None) -> None:
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.begin() as conn:
            for rid in rec_ids:
                await conn.execute(
                    text("DELETE FROM financas.recorrencias WHERE id = :id"),
                    {"id": rid},
                )
            if usuario_id:
                await conn.execute(
                    text("DELETE FROM financas.cartoes WHERE usuario_id = :u"),
                    {"u": usuario_id},
                )
    finally:
        await eng.dispose()


def smoke_test() -> None:
    print("━" * 60)
    print("Smoke test — recorrências: editar + excluir")
    print("━" * 60)

    usuario_id = str(uuid.uuid4())
    rec_ids: list[str] = []

    with TestClient(app) as client:
        usar_usuario(usuario_id)
        try:
            # ── Cria uma recorrência ──────────────────────────────────
            r = client.post(REC, json={
                "usuario_id": usuario_id, "descricao": "Aluguel",
                "tipo": "despesa", "valor_estimado": 1500, "dia_vencimento": 10,
            })
            assert r.status_code == 201, r.text
            rid = r.json()["id"]
            rec_ids.append(rid)
            assert r.json()["ativa"] is True
            print("\n→ criada (Aluguel, dia 10, R$1500, ativa)")

            # ── 1. Edita valor + dia + inativa ────────────────────────
            print("→ Test 1: PATCH valor/dia/ativa")
            up = client.patch(f"{REC}/{rid}", json={
                "valor_estimado": 1650, "dia_vencimento": 5, "ativa": False,
            })
            assert up.status_code == 200, up.text
            assert float(up.json()["valor_estimado"]) == 1650.0
            assert up.json()["dia_vencimento"] == 5
            assert up.json()["ativa"] is False
            print("   ok: 1650 / dia 5 / inativa")

            # ── 2. Validação: dia fora de faixa → 422 ─────────────────
            print("→ Test 2: dia inválido → 422")
            bad = client.patch(f"{REC}/{rid}", json={"dia_vencimento": 40})
            assert bad.status_code == 422, bad.status_code

            # ── 3. Lista reflete a edição ─────────────────────────────
            lst = client.get(REC).json()
            assert lst["total"] == 1
            assert lst["items"][0]["ativa"] is False

            # ── 4. Exclui ─────────────────────────────────────────────
            print("→ Test 3: DELETE")
            d = client.delete(f"{REC}/{rid}")
            assert d.status_code == 204, d.text
            assert client.get(REC).json()["total"] == 0
            rec_ids.clear()
            print("   excluída; lista vazia")

            # ── 5. Excluir inexistente → 404 ──────────────────────────
            assert client.delete(f"{REC}/{uuid.uuid4()}").status_code == 404

            # ── 6. Recorrência no cartão (forma_pagamento + cartao_id) ─
            print("→ Test 4: recorrência paga no cartão")
            cartao_id = client.post("/api/financas/cartoes", json={
                "usuario_id": usuario_id, "nome": "Nubank",
                "dia_fechamento": 20, "dia_vencimento": 10,
            }).json()["id"]
            rc = client.post(REC, json={
                "usuario_id": usuario_id, "descricao": "Claude",
                "tipo": "despesa", "valor_estimado": 100, "dia_vencimento": 15,
                "forma_pagamento": "cartao", "cartao_id": cartao_id,
            })
            assert rc.status_code == 201, rc.text
            assert rc.json()["forma_pagamento"] == "cartao"
            assert rc.json()["cartao_id"] == cartao_id
            rec_ids.append(rc.json()["id"])
            # forma inválida → 400
            assert client.post(REC, json={
                "usuario_id": usuario_id, "descricao": "X", "valor_estimado": 1,
                "dia_vencimento": 1, "forma_pagamento": "pix",
            }).status_code == 400
            print("   ok: Claude no cartão Nubank; forma inválida → 400")

        finally:
            limpar_override()
            asyncio.run(_cleanup(rec_ids, usuario_id))

    print("\n" + "━" * 60)
    print("TUDO OK — CRUD de recorrências funcionando!")
    print("━" * 60)


def main() -> None:
    smoke_test()


if __name__ == "__main__":
    main()

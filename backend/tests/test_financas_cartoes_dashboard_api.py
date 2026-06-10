from __future__ import annotations

import asyncio
import uuid
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.api.main import app
from tests._financas_auth import usar_usuario
from app.config import settings

CARTOES = "/api/financas/cartoes"
COMPRAS = "/api/financas/compras"


async def _cleanup(usuario_id: str, cartao_ids: list[str], compra_ids: list[str]) -> None:
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.begin() as conn:
            for cid in compra_ids:
                await conn.execute(text("DELETE FROM financas.compras WHERE id = :id"), {"id": cid})
            for cid in cartao_ids:
                await conn.execute(text("DELETE FROM financas.cartoes WHERE id = :id"), {"id": cid})
    finally:
        await eng.dispose()


def smoke_test() -> None:
    print("━" * 60)
    print("Smoke test — financas Step 24 (cartões no dashboard)")
    print("━" * 60)

    usuario_id = str(uuid.uuid4())
    cartao_ids: list[str] = []
    compra_ids: list[str] = []

    with TestClient(app) as client:
        usar_usuario(usuario_id)  # dono = sessão (override de auth)
        try:
            cartao_id = client.post(CARTOES, json={
                "usuario_id": usuario_id, "nome": "Nubank",
                "dia_fechamento": 20, "dia_vencimento": 10,
            }).json()["id"]
            cartao_ids.append(cartao_id)
            r = client.post(COMPRAS, json={
                "usuario_id": usuario_id, "cartao_id": cartao_id,
                "descricao": "Geladeira", "valor_total": 300, "total_parcelas": 3,
                "valor_juros_total": 30, "data_compra": "2026-06-15",
            })
            compra_ids.append(r.json()["id"])

            # ── 1. Lista de cartões ───────────────────────────────────
            print("\n→ Test 1: GET /cartoes")
            rl = client.get(CARTOES, params={"usuario_id": usuario_id})
            assert rl.status_code == 200, rl.text
            assert rl.json()["total"] == 1
            assert rl.json()["items"][0]["nome"] == "Nubank"
            print(f"   {rl.json()['total']} cartão")

            # ── 2. Faturas + total em aberto + juros ──────────────────
            print("\n→ Test 2: GET /cartoes/{id}/faturas")
            rf = client.get(f"{CARTOES}/{cartao_id}/faturas")
            assert rf.status_code == 200, rf.text
            b = rf.json()
            assert len(b["faturas"]) == 3, len(b["faturas"])
            assert Decimal(b["total_em_aberto"]) == Decimal("300.00"), b["total_em_aberto"]
            assert Decimal(b["total_juros"]) == Decimal("30.00"), b["total_juros"]
            # faturas em ordem decrescente de mês
            meses = [f["mes_referencia"] for f in b["faturas"]]
            assert meses == sorted(meses, reverse=True), meses
            print(f"   3 faturas, em aberto {b['total_em_aberto']}, juros {b['total_juros']}")

            # ── 3. Cartão inexistente → 404 ───────────────────────────
            print("\n→ Test 3: faturas de cartão inexistente → 404")
            assert client.get(f"{CARTOES}/{uuid.uuid4()}/faturas").status_code == 404
            print("   404 ok")

        finally:
            asyncio.run(_cleanup(usuario_id, cartao_ids, compra_ids))

    print("\n" + "━" * 60)
    print("TUDO OK — financas Step 24 (backend) funcionando!")
    print("━" * 60)


def main() -> None:
    smoke_test()


if __name__ == "__main__":
    main()

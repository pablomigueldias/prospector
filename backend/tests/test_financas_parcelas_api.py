from __future__ import annotations

import asyncio
import uuid
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.api.main import app
from tests._financas_auth import limpar_override, usar_usuario
from app.config import settings

CARTOES = "/api/financas/cartoes"
COMPRAS = "/api/financas/compras"


async def _cleanup(cartao_ids: list[str], compra_ids: list[str]) -> None:
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.begin() as conn:
            for cid in compra_ids:   # cascata nas parcelas
                await conn.execute(
                    text("DELETE FROM financas.compras WHERE id = :id"), {"id": cid}
                )
            for cid in cartao_ids:   # cascata nas faturas
                await conn.execute(
                    text("DELETE FROM financas.cartoes WHERE id = :id"), {"id": cid}
                )
    finally:
        await eng.dispose()


def smoke_test() -> None:
    print("━" * 60)
    print("Smoke test — financas Step 10 (cartão + compra parcelada)")
    print("━" * 60)

    usuario_id = str(uuid.uuid4())
    outro = str(uuid.uuid4())
    cartao_ids: list[str] = []
    compra_ids: list[str] = []

    with TestClient(app) as client:
        usar_usuario(usuario_id)  # dono = sessão (override de auth)
        try:
            # ── Cartão: fecha dia 20, vence dia 10 (→ vencimento no mês seguinte) ─
            rc = client.post(CARTOES, json={
                "usuario_id": usuario_id, "nome": "Nubank",
                "dia_fechamento": 20, "dia_vencimento": 10, "limite": 5000,
            })
            assert rc.status_code == 201, rc.text
            cartao_id = rc.json()["id"]
            cartao_ids.append(cartao_id)
            print(f"\n   cartão {cartao_id} (fecha 20, vence 10)")

            # ── 1. Compra 300 em 3x, comprada 2026-06-15 ──────────────
            print("\n→ Test 1: 300 em 3x → parcelas + faturas + vencimentos")
            r1 = client.post(COMPRAS, json={
                "usuario_id": usuario_id, "cartao_id": cartao_id,
                "descricao": "Geladeira", "valor_total": 300, "total_parcelas": 3,
                "data_compra": "2026-06-15",
            })
            assert r1.status_code == 201, r1.text
            compra_ids.append(r1.json()["id"])
            parcelas = r1.json()["parcelas"]
            assert [p["numero"] for p in parcelas] == [1, 2, 3]
            assert [float(p["valor"]) for p in parcelas] == [100.0, 100.0, 100.0]
            # fecha jun/jul/ago → vence jul/ago/set, dia 10
            assert [p["vencimento"] for p in parcelas] == [
                "2026-07-10", "2026-08-10", "2026-09-10",
            ], [p["vencimento"] for p in parcelas]
            # 3 faturas distintas
            faturas = {p["fatura_id"] for p in parcelas}
            assert len(faturas) == 3, faturas
            print(f"   vencimentos {[p['vencimento'] for p in parcelas]} ; {len(faturas)} faturas")

            # ── 2. Split de centavo: 100 em 3x → 33.33/33.33/33.34 ────
            print("\n→ Test 2: 100 em 3x (centavo certo)")
            r2 = client.post(COMPRAS, json={
                "usuario_id": usuario_id, "cartao_id": cartao_id,
                "descricao": "Tênis", "valor_total": 100, "total_parcelas": 3,
                "data_compra": "2026-06-15",
            })
            assert r2.status_code == 201, r2.text
            compra_ids.append(r2.json()["id"])
            vals = [Decimal(p["valor"]) for p in r2.json()["parcelas"]]
            assert vals == [Decimal("33.33"), Decimal("33.33"), Decimal("33.34")], vals
            assert sum(vals) == Decimal("100.00")
            print(f"   {vals} (soma {sum(vals)})")

            # ── 3. Com juros: 120 total, 30 de juros, 3x ──────────────
            print("\n→ Test 3: 120 em 3x com 30 de juros")
            r3 = client.post(COMPRAS, json={
                "usuario_id": usuario_id, "cartao_id": cartao_id,
                "descricao": "Fone", "valor_total": 120, "total_parcelas": 3,
                "valor_juros_total": 30, "data_compra": "2026-06-15",
            })
            assert r3.status_code == 201, r3.text
            compra_ids.append(r3.json()["id"])
            ps = r3.json()["parcelas"]
            assert all(p["tem_juros"] is True for p in ps)
            assert [float(p["valor_juros"]) for p in ps] == [10.0, 10.0, 10.0]
            print(f"   juros por parcela {[float(p['valor_juros']) for p in ps]}")

            # ── 4. Erros ──────────────────────────────────────────────
            print("\n→ Test 4: validações")
            r404 = client.post(COMPRAS, json={
                "usuario_id": usuario_id, "cartao_id": str(uuid.uuid4()),
                "descricao": "x", "valor_total": 50, "total_parcelas": 2,
            })
            assert r404.status_code == 404, r404.status_code
            usar_usuario(outro)  # outra sessão não compra no cartão deste usuário
            rmix = client.post(COMPRAS, json={
                "usuario_id": outro, "cartao_id": cartao_id,
                "descricao": "x", "valor_total": 50, "total_parcelas": 2,
            })
            assert rmix.status_code == 400, rmix.status_code
            usar_usuario(usuario_id)  # volta pro dono
            rjuros = client.post(COMPRAS, json={
                "usuario_id": usuario_id, "cartao_id": cartao_id,
                "descricao": "x", "valor_total": 50, "total_parcelas": 2,
                "valor_juros_total": 60,
            })
            assert rjuros.status_code == 400, rjuros.status_code
            print("   404 cartão ; 400 dono errado ; 400 juros>total")

        finally:
            limpar_override()
            asyncio.run(_cleanup(cartao_ids, compra_ids))

    print("\n" + "━" * 60)
    print("TUDO OK — financas Step 10 funcionando!")
    print("━" * 60)


def main() -> None:
    smoke_test()


if __name__ == "__main__":
    main()

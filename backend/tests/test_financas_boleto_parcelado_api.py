from __future__ import annotations

import asyncio
import uuid

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.api.main import app
from app.config import settings

COMPRAS = "/api/financas/compras"
CATS = "/api/financas/categorias"


async def _cleanup(compra_ids: list[str]) -> None:
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.begin() as conn:
            for cid in compra_ids:
                await conn.execute(
                    text("DELETE FROM financas.compras WHERE id = :id"), {"id": cid}
                )
    finally:
        await eng.dispose()


def _subverba_reforma(client: TestClient) -> str:
    for raiz in client.get(CATS).json()["items"]:
        if raiz["nome"] == "Condomínio":
            for f in raiz["filhos"]:
                if f["nome"] == "Reforma infiltração (parcelada)":
                    return f["id"]
    raise AssertionError("subverba da reforma não achada no seed")


def smoke_test() -> None:
    print("━" * 60)
    print("Smoke test — financas Step 11 (boleto parcelado)")
    print("━" * 60)

    usuario_id = str(uuid.uuid4())
    compra_ids: list[str] = []

    with TestClient(app) as client:
        try:
            reforma_id = _subverba_reforma(client)

            # ── Reforma infiltração: 600 em 6x, 1º vence 2026-06-10 ───
            print("\n→ Test 1: boleto 600 em 6x (reforma do condomínio)")
            r = client.post(f"{COMPRAS}/boleto", json={
                "usuario_id": usuario_id,
                "descricao": "Reforma infiltração",
                "valor_total": 600, "total_parcelas": 6,
                "primeiro_vencimento": "2026-06-10",
                "categoria_id": reforma_id,
            })
            assert r.status_code == 201, r.text
            compra_ids.append(r.json()["id"])
            b = r.json()
            assert b["origem"] == "boleto"
            assert b["cartao_id"] is None
            assert b["categoria_id"] == reforma_id
            ps = b["parcelas"]
            assert len(ps) == 6
            assert all(float(p["valor"]) == 100.0 for p in ps)
            assert all(p["fatura_id"] is None for p in ps)  # boleto não tem fatura
            assert [p["vencimento"] for p in ps] == [
                "2026-06-10", "2026-07-10", "2026-08-10",
                "2026-09-10", "2026-10-10", "2026-11-10",
            ], [p["vencimento"] for p in ps]
            print(f"   6 parcelas de 100, venc {ps[0]['vencimento']}..{ps[-1]['vencimento']}, sem fatura")

            # ── Mesma rota GET de compra serve pro boleto ─────────────
            rd = client.get(f"{COMPRAS}/{compra_ids[0]}")
            assert rd.status_code == 200 and rd.json()["origem"] == "boleto"
            print("   GET /compras/{id} ok pro boleto")

            # ── Erros ─────────────────────────────────────────────────
            print("\n→ Test 2: validações")
            r404 = client.post(f"{COMPRAS}/boleto", json={
                "usuario_id": usuario_id, "descricao": "x", "valor_total": 50,
                "total_parcelas": 2, "primeiro_vencimento": "2026-06-10",
                "categoria_id": str(uuid.uuid4()),
            })
            assert r404.status_code == 404, r404.status_code
            rjuros = client.post(f"{COMPRAS}/boleto", json={
                "usuario_id": usuario_id, "descricao": "x", "valor_total": 50,
                "total_parcelas": 2, "primeiro_vencimento": "2026-06-10",
                "valor_juros_total": 60,
            })
            assert rjuros.status_code == 400, rjuros.status_code
            print("   404 categoria ; 400 juros>total")

        finally:
            asyncio.run(_cleanup(compra_ids))

    print("\n" + "━" * 60)
    print("TUDO OK — financas Step 11 funcionando!")
    print("━" * 60)


def main() -> None:
    smoke_test()


if __name__ == "__main__":
    main()

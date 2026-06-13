"""Smoke test — pagar o mês (boletos a pagar + fatura de cartão de uma vez).

GET /pagar-mes/preview lista as pendências do mês (boleto + fatura); POST
/pagar-mes quita os itens escolhidos, cada um debitando a conta indicada.
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.api.main import app
from app.config import settings
from tests._financas_auth import limpar_override, usar_usuario

PM = "/api/financas/pagar-mes"
CARTOES = "/api/financas/cartoes"
COMPRAS = "/api/financas/compras"
CONTAS = "/api/financas/contas"
TX = "/api/financas/transacoes"


async def _cleanup(usuario_id: str) -> None:
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.begin() as conn:
            for tbl in ("transacoes", "compras", "cartoes", "contas"):
                await conn.execute(
                    text(f"DELETE FROM financas.{tbl} WHERE usuario_id = :u"),
                    {"u": uuid.UUID(usuario_id)},
                )
    finally:
        await eng.dispose()


def smoke_test() -> None:
    print("━" * 60)
    print("Smoke test — pagar o mês (boletos + fatura juntos)")
    print("━" * 60)

    # A fatura que fecha em jun vence em 10/jul, então "pagar o mês" de julho
    # junta a fatura + o boleto que venceu (10/jun, ainda pendente).
    usuario_id = str(uuid.uuid4())
    comp = "2026-07"

    with TestClient(app) as client:
        usar_usuario(usuario_id)
        try:
            conta_id = client.post(CONTAS, json={
                "usuario_id": usuario_id, "nome": "Nubank", "tipo": "corrente",
                "saldo_atual": 5000,
            }).json()["id"]

            # boleto a pagar (prevista) vencendo no mês
            boleto_id = client.post(f"{TX}/despesa", json={
                "usuario_id": usuario_id, "descricao": "Luz", "valor_total": 200,
                "conta_id": conta_id, "data_competencia": "2026-06-01",
                "status": "prevista",
            }).json()["id"]
            # dá um vencimento no mês ao boleto (o form não seta vencimento)
            asyncio.run(_set_vencimento(boleto_id, "2026-06-10"))

            # cartão + compra à vista → fatura do mês
            cartao_id = client.post(CARTOES, json={
                "usuario_id": usuario_id, "nome": "Visa",
                "dia_fechamento": 20, "dia_vencimento": 10,
            }).json()["id"]
            client.post(COMPRAS, json={
                "usuario_id": usuario_id, "cartao_id": cartao_id,
                "descricao": "Compras", "valor_total": 300, "total_parcelas": 1,
                "data_compra": "2026-06-05",
            })

            # ── 1. Preview do mês ─────────────────────────────────────
            print("\n→ Test 1: GET /pagar-mes/preview")
            pv = client.get(f"{PM}/preview", params={"competencia": comp}).json()
            tipos = sorted(i["tipo"] for i in pv["itens"])
            assert tipos == ["boleto", "fatura"], pv["itens"]
            assert Decimal(pv["total"]) == Decimal("500.00"), pv["total"]
            print(f"   2 pendências, total {pv['total']}")

            fatura_item = next(i for i in pv["itens"] if i["tipo"] == "fatura")
            boleto_item = next(i for i in pv["itens"] if i["tipo"] == "boleto")

            # ── 2. Paga as duas de uma vez ────────────────────────────
            print("\n→ Test 2: POST /pagar-mes (boleto + fatura)")
            r = client.post(PM, json={
                "data_pagamento": "2026-06-10",
                "itens": [
                    {"tipo": "boleto", "id": boleto_item["id"], "conta_id": conta_id},
                    {"tipo": "fatura", "id": fatura_item["id"], "conta_id": conta_id},
                ],
            })
            assert r.status_code == 200, r.text
            assert r.json()["pagos"] == 2 and not r.json()["falhas"], r.json()
            assert Decimal(r.json()["total_pago"]) == Decimal("500.00"), r.json()
            print(f"   pagos {r.json()['pagos']}, total {r.json()['total_pago']}")

            # saldo caiu 500 (200 + 300)
            saldo = next(c["saldo_atual"] for c in client.get(CONTAS, params={"usuario_id": usuario_id}).json()["items"] if c["id"] == conta_id)
            assert Decimal(saldo) == Decimal("4500.00"), saldo
            # preview agora vazio (nada mais a pagar no mês)
            pv2 = client.get(f"{PM}/preview", params={"competencia": comp}).json()
            assert pv2["itens"] == [], pv2
            # a fatura paga virou transação na lista (histórico)
            lst = client.get(TX, params={"usuario_id": usuario_id}).json()
            assert any("Fatura Visa" in t["descricao"] and t["status"] == "paga" for t in lst["items"]), lst
            print(f"   saldo {saldo}, fatura paga aparece em Transações")

        finally:
            limpar_override()
            asyncio.run(_cleanup(usuario_id))

    print("\n" + "━" * 60)
    print("TUDO OK — pagar o mês funcionando!")
    print("━" * 60)


async def _set_vencimento(transacao_id: str, venc: str) -> None:
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.begin() as conn:
            await conn.execute(
                text("UPDATE financas.transacoes SET data_vencimento = :v WHERE id = :id"),
                {"v": date.fromisoformat(venc), "id": transacao_id},
            )
    finally:
        await eng.dispose()


def main() -> None:
    smoke_test()


if __name__ == "__main__":
    main()

"""Smoke test — marcar/lançar recorrência no mês, ligada ao lançamento.

Cobre:
  GET  /api/financas/recorrencias/status
  POST /api/financas/recorrencias/{id}/pagar-mes
para recorrência no cartão (vira compra na fatura) e na conta (vira
despesa paga, move o saldo).
"""
from __future__ import annotations

import asyncio
import uuid
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.api.main import app
from app.config import settings
from tests._financas_auth import limpar_override, usar_usuario

REC = "/api/financas/recorrencias"
CARTOES = "/api/financas/cartoes"
CONTAS = "/api/financas/contas"


async def _cleanup(usuario_id: str) -> None:
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.begin() as conn:
            await conn.execute(text("DELETE FROM financas.transacoes WHERE usuario_id = :u"), {"u": usuario_id})
            await conn.execute(text("DELETE FROM financas.compras WHERE usuario_id = :u"), {"u": usuario_id})
            await conn.execute(text("DELETE FROM financas.recorrencias WHERE usuario_id = :u"), {"u": usuario_id})
            await conn.execute(text("DELETE FROM financas.cartoes WHERE usuario_id = :u"), {"u": usuario_id})
            await conn.execute(text("DELETE FROM financas.contas WHERE usuario_id = :u"), {"u": usuario_id})
    finally:
        await eng.dispose()


def smoke_test() -> None:
    print("━" * 60)
    print("Smoke test — recorrência: status do mês + marcar/lançar pago")
    print("━" * 60)

    usuario_id = str(uuid.uuid4())
    comp = "2026-06"

    with TestClient(app) as client:
        usar_usuario(usuario_id)
        try:
            cartao_id = client.post(CARTOES, json={
                "usuario_id": usuario_id, "nome": "Nubank",
                "dia_fechamento": 20, "dia_vencimento": 10,
            }).json()["id"]
            conta_id = client.post(CONTAS, json={
                "usuario_id": usuario_id, "nome": "Conta", "tipo": "corrente",
                "saldo_atual": 1000,
            }).json()["id"]

            # recorrência no cartão (Claude) e na conta (Luz)
            claude = client.post(REC, json={
                "usuario_id": usuario_id, "descricao": "Claude", "valor_estimado": 100,
                "dia_vencimento": 15, "forma_pagamento": "cartao", "cartao_id": cartao_id,
            }).json()["id"]
            luz = client.post(REC, json={
                "usuario_id": usuario_id, "descricao": "Luz", "valor_estimado": 200,
                "dia_vencimento": 10, "forma_pagamento": "conta", "conta_id": conta_id,
            }).json()["id"]

            # ── 1. Status inicial: nenhuma lançada ────────────────────
            print("\n→ Test 1: status do mês (nada lançado)")
            st = client.get(f"{REC}/status", params={"competencia": comp}).json()
            sit = {i["recorrencia_id"]: i["situacao"] for i in st["items"]}
            assert sit[claude] == "nenhuma" and sit[luz] == "nenhuma", sit
            print("   ambas 'nenhuma'")

            # ── 2. Cartão: pagar-mes → vira compra na fatura ──────────
            print("\n→ Test 2: pagar-mes do Claude (cartão)")
            rp = client.post(f"{REC}/{claude}/pagar-mes", json={
                "competencia": comp, "data_pagamento": "2026-06-15",
            })
            assert rp.status_code == 200, rp.text
            assert rp.json()["situacao"] == "lancada_cartao", rp.json()
            assert rp.json()["compra_id"], rp.json()
            # entrou na fatura (em aberto = 100), e a conta NÃO mexeu
            faturas = client.get(f"{CARTOES}/{cartao_id}/faturas").json()
            assert Decimal(faturas["total_em_aberto"]) == Decimal("100.00"), faturas
            saldo = next(c["saldo_atual"] for c in client.get(CONTAS, params={"usuario_id": usuario_id}).json()["items"] if c["id"] == conta_id)
            assert Decimal(saldo) == Decimal("1000.00"), saldo
            print(f"   na fatura (em aberto {faturas['total_em_aberto']}), saldo intacto {saldo}")
            # idempotência: de novo → 400
            assert client.post(f"{REC}/{claude}/pagar-mes", json={"competencia": comp}).status_code == 400
            print("   2ª vez → 400 ok")

            # ── 3. Conta: pagar-mes → despesa paga, move saldo ────────
            print("\n→ Test 3: pagar-mes da Luz (conta)")
            rp2 = client.post(f"{REC}/{luz}/pagar-mes", json={"competencia": comp})
            assert rp2.status_code == 200, rp2.text
            assert rp2.json()["situacao"] == "paga", rp2.json()
            tid = rp2.json()["transacao_id"]
            assert tid, rp2.json()
            saldo2 = next(c["saldo_atual"] for c in client.get(CONTAS, params={"usuario_id": usuario_id}).json()["items"] if c["id"] == conta_id)
            assert Decimal(saldo2) == Decimal("800.00"), saldo2
            # virou transação ligada à recorrência
            lst = client.get("/api/financas/transacoes", params={"usuario_id": usuario_id}).json()
            paga = next(t for t in lst["items"] if t["id"] == tid)
            assert paga["status"] == "paga", paga
            print(f"   despesa paga, saldo {saldo2}")

            # ── 4. Status final reflete tudo ──────────────────────────
            print("\n→ Test 4: status final")
            st2 = {i["recorrencia_id"]: i["situacao"] for i in client.get(f"{REC}/status", params={"competencia": comp}).json()["items"]}
            assert st2[claude] == "lancada_cartao" and st2[luz] == "paga", st2
            print(f"   Claude={st2[claude]}, Luz={st2[luz]}")

        finally:
            limpar_override()
            asyncio.run(_cleanup(usuario_id))

    print("\n" + "━" * 60)
    print("TUDO OK — status do mês + marcar/lançar pago funcionando!")
    print("━" * 60)


def main() -> None:
    smoke_test()


if __name__ == "__main__":
    main()

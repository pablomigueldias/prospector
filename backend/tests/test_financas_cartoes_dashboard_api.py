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
CONTAS = "/api/financas/contas"


async def _cleanup(usuario_id: str, cartao_ids: list[str], compra_ids: list[str]) -> None:
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.begin() as conn:
            # despesas geradas ao pagar fatura (e seus pagamentos via cascade)
            await conn.execute(
                text("DELETE FROM financas.transacoes WHERE usuario_id = :u"),
                {"u": usuario_id},
            )
            for cid in compra_ids:
                await conn.execute(text("DELETE FROM financas.compras WHERE id = :id"), {"id": cid})
            for cid in cartao_ids:
                await conn.execute(text("DELETE FROM financas.cartoes WHERE id = :id"), {"id": cid})
            await conn.execute(
                text("DELETE FROM financas.contas WHERE usuario_id = :u"),
                {"u": usuario_id},
            )
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

            # ── 4. Extrato de uma fatura ──────────────────────────────
            print("\n→ Test 4: GET /cartoes/{id}/faturas/{fatura_id} (extrato)")
            primeira = sorted(b["faturas"], key=lambda f: f["mes_referencia"])[0]
            re = client.get(f"{CARTOES}/{cartao_id}/faturas/{primeira['id']}")
            assert re.status_code == 200, re.text
            ext = re.json()
            assert ext["cartao_nome"] == "Nubank", ext["cartao_nome"]
            assert len(ext["itens"]) == 1, ext["itens"]
            it = ext["itens"][0]
            assert it["descricao"] == "Geladeira", it
            assert it["total_parcelas"] == 3, it
            assert Decimal(it["valor"]) == Decimal("100.00"), it["valor"]
            print(f"   extrato: {it['descricao']} {it['numero']}/{it['total_parcelas']} R${it['valor']}")
            # fatura inexistente → 404
            assert client.get(f"{CARTOES}/{cartao_id}/faturas/{uuid.uuid4()}").status_code == 404
            print("   fatura inexistente → 404 ok")

            # ── 5. Pagar a fatura ─────────────────────────────────────
            print("\n→ Test 5: POST /cartoes/{id}/faturas/{fatura_id}/pagar")
            conta_id = client.post(CONTAS, json={
                "usuario_id": usuario_id, "nome": "Nubank conta",
                "tipo": "corrente", "saldo_atual": 1000,
            }).json()["id"]
            rp = client.post(
                f"{CARTOES}/{cartao_id}/faturas/{primeira['id']}/pagar",
                json={"conta_id": conta_id},
            )
            assert rp.status_code == 200, rp.text
            assert rp.json()["status"] == "paga", rp.json()
            # a fatura sai do "em aberto"
            rf2 = client.get(f"{CARTOES}/{cartao_id}/faturas").json()
            assert Decimal(rf2["total_em_aberto"]) == Decimal("200.00"), rf2["total_em_aberto"]
            # saldo da conta caiu pelo valor da fatura (100)
            saldo = next(
                c["saldo_atual"] for c in
                client.get(CONTAS, params={"usuario_id": usuario_id}).json()["items"]
                if c["id"] == conta_id
            )
            assert Decimal(saldo) == Decimal("900.00"), saldo
            # virou despesa na lista de transações, ligada à fatura
            lst = client.get("/api/financas/transacoes", params={"usuario_id": usuario_id}).json()
            assert any("Fatura Nubank" in t["descricao"] for t in lst["items"]), lst
            print(f"   fatura paga, em aberto {rf2['total_em_aberto']}, saldo {saldo}")
            # pagar de novo → 400 (já paga)
            assert client.post(
                f"{CARTOES}/{cartao_id}/faturas/{primeira['id']}/pagar",
                json={"conta_id": conta_id},
            ).status_code == 400
            print("   pagar de novo → 400 ok")

        finally:
            asyncio.run(_cleanup(usuario_id, cartao_ids, compra_ids))

    print("\n" + "━" * 60)
    print("TUDO OK — financas Step 24 (backend) funcionando!")
    print("━" * 60)


def main() -> None:
    smoke_test()


if __name__ == "__main__":
    main()

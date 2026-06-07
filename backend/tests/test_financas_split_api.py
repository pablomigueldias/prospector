from __future__ import annotations

import asyncio
import uuid

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.api.main import app
from app.config import settings

CONTAS = "/api/financas/contas"
TX = "/api/financas/transacoes"


async def _cleanup(conta_ids: list[str], tx_ids: list[str]) -> None:
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.begin() as conn:
            for tid in tx_ids:
                await conn.execute(
                    text("DELETE FROM financas.transacoes WHERE id = :id"), {"id": tid}
                )
            for cid in conta_ids:
                await conn.execute(
                    text("DELETE FROM financas.contas WHERE id = :id"), {"id": cid}
                )
    finally:
        await eng.dispose()


def smoke_test() -> None:
    print("━" * 60)
    print("Smoke test — financas Step 8 (pagamento dividido)")
    print("━" * 60)

    usuario_id = str(uuid.uuid4())
    conta_ids: list[str] = []
    tx_ids: list[str] = []

    def saldo(cid: str, client: TestClient) -> float:
        return float(client.get(f"{CONTAS}/{cid}").json()["saldo_atual"])

    with TestClient(app) as client:
        try:
            rv = client.post(CONTAS, json={
                "usuario_id": usuario_id, "nome": "VR Caju",
                "tipo": "vr", "saldo_atual": 100,
            })
            rc = client.post(CONTAS, json={
                "usuario_id": usuario_id, "nome": "Carteira",
                "tipo": "dinheiro", "saldo_atual": 500,
            })
            vr_id, cash_id = rv.json()["id"], rc.json()["id"]
            conta_ids += [vr_id, cash_id]
            print(f"\n   VR={saldo(vr_id, client)} ; Dinheiro={saldo(cash_id, client)}")

            # ── 1. Split explícito (30 VR + 100 dinheiro = 130) ───────
            print("\n→ Test 1: split explícito 130")
            r1 = client.post(f"{TX}/despesa/dividida", json={
                "usuario_id": usuario_id, "descricao": "Mercado grande",
                "valor_total": 130,
                "pagamentos": [
                    {"conta_id": vr_id, "valor": 30},
                    {"conta_id": cash_id, "valor": 100},
                ],
            })
            assert r1.status_code == 201, r1.text
            tx_ids.append(r1.json()["id"])
            assert len(r1.json()["pagamentos"]) == 2
            assert saldo(vr_id, client) == 70.0
            assert saldo(cash_id, client) == 400.0
            print(f"   VR={saldo(vr_id, client)} ; Dinheiro={saldo(cash_id, client)}")

            # ── 2. Split com soma errada → 400 ────────────────────────
            print("\n→ Test 2: soma errada → 400")
            rbad = client.post(f"{TX}/despesa/dividida", json={
                "usuario_id": usuario_id, "descricao": "x", "valor_total": 100,
                "pagamentos": [{"conta_id": vr_id, "valor": 10},
                               {"conta_id": cash_id, "valor": 50}],
            })
            assert rbad.status_code == 400, rbad.status_code
            print(f"   barrou: {rbad.json()['detail']}")

            # ── 3. Auto-split parcial: 125 → VR(70) esgota, resto(55) cash ─
            print("\n→ Test 3: auto-split 125 (VR esgota → resto dinheiro)")
            r3 = client.post(f"{TX}/despesa/auto-split", json={
                "usuario_id": usuario_id, "descricao": "Mercado",
                "valor_total": 125,
                "conta_vr_id": vr_id, "conta_fallback_id": cash_id,
            })
            assert r3.status_code == 201, r3.text
            tx_ids.append(r3.json()["id"])
            pags = {p["conta_id"]: float(p["valor"]) for p in r3.json()["pagamentos"]}
            assert pags == {vr_id: 70.0, cash_id: 55.0}, pags
            assert saldo(vr_id, client) == 0.0
            assert saldo(cash_id, client) == 345.0
            print(f"   pagamentos={pags} ; VR={saldo(vr_id, client)} ; Dinheiro={saldo(cash_id, client)}")

            # ── 4. Auto-split com VR zerado → tudo no dinheiro ────────
            print("\n→ Test 4: auto-split 20 com VR=0 → só dinheiro")
            r4 = client.post(f"{TX}/despesa/auto-split", json={
                "usuario_id": usuario_id, "descricao": "Pão",
                "valor_total": 20,
                "conta_vr_id": vr_id, "conta_fallback_id": cash_id,
            })
            assert r4.status_code == 201, r4.text
            tx_ids.append(r4.json()["id"])
            assert len(r4.json()["pagamentos"]) == 1
            assert r4.json()["pagamentos"][0]["conta_id"] == cash_id
            assert saldo(cash_id, client) == 325.0
            print(f"   1 pagamento (dinheiro) ; Dinheiro={saldo(cash_id, client)}")

            # ── 5. VR == fallback → 400 ───────────────────────────────
            print("\n→ Test 5: VR == fallback → 400")
            r5 = client.post(f"{TX}/despesa/auto-split", json={
                "usuario_id": usuario_id, "descricao": "x", "valor_total": 10,
                "conta_vr_id": vr_id, "conta_fallback_id": vr_id,
            })
            assert r5.status_code == 400, r5.status_code
            print(f"   barrou: {r5.json()['detail']}")

        finally:
            asyncio.run(_cleanup(conta_ids, tx_ids))

    print("\n" + "━" * 60)
    print("TUDO OK — financas Step 8 funcionando!")
    print("━" * 60)


def main() -> None:
    smoke_test()


if __name__ == "__main__":
    main()

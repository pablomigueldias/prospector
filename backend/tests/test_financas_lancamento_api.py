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
    # Engine próprio e descartável: o engine global do app está preso ao loop
    # do TestClient; aqui rodamos num loop novo (asyncio.run), então criamos
    # uma conexão independente só pra limpar.
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.begin() as conn:
            # tx primeiro (cascade nos pagamentos), depois as contas
            for tid in tx_ids:
                await conn.execute(
                    text("DELETE FROM financas.transacoes WHERE id = :id"),
                    {"id": tid},
                )
            for cid in conta_ids:
                await conn.execute(
                    text("DELETE FROM financas.contas WHERE id = :id"),
                    {"id": cid},
                )
    finally:
        await eng.dispose()


def _saldo(client: TestClient, conta_id: str) -> float:
    return float(client.get(f"{CONTAS}/{conta_id}").json()["saldo_atual"])


def smoke_test() -> None:
    print("━" * 60)
    print("Smoke test — financas Step 7 (lançamento de despesa + saldo)")
    print("━" * 60)

    usuario_id = str(uuid.uuid4())
    outro_usuario = str(uuid.uuid4())
    conta_ids: list[str] = []
    tx_ids: list[str] = []

    with TestClient(app) as client:
        try:
            # ── Conta com saldo de abertura 1000 ──────────────────────
            r = client.post(CONTAS, json={
                "usuario_id": usuario_id, "nome": "Nubank",
                "tipo": "corrente", "saldo_atual": 1000,
            })
            assert r.status_code == 201, r.text
            conta_id = r.json()["id"]
            conta_ids.append(conta_id)
            assert _saldo(client, conta_id) == 1000.0
            print(f"\n   conta criada, saldo abertura = {_saldo(client, conta_id)}")

            # ── 1. Despesa PAGA derruba o saldo ───────────────────────
            print("\n→ Test 1: despesa paga (150) → saldo 850")
            r1 = client.post(f"{TX}/despesa", json={
                "usuario_id": usuario_id, "descricao": "Mercado",
                "valor_total": 150, "conta_id": conta_id,
            })
            assert r1.status_code == 201, r1.text
            tx_ids.append(r1.json()["id"])
            assert r1.json()["tipo"] == "despesa"
            assert r1.json()["status"] == "paga"
            assert len(r1.json()["pagamentos"]) == 1
            assert float(r1.json()["pagamentos"][0]["valor"]) == 150.0
            assert _saldo(client, conta_id) == 850.0, _saldo(client, conta_id)
            print(f"   saldo agora = {_saldo(client, conta_id)}")

            # ── 2. Despesa PREVISTA não mexe no saldo ─────────────────
            print("\n→ Test 2: despesa prevista (100) → saldo segue 850")
            r2 = client.post(f"{TX}/despesa", json={
                "usuario_id": usuario_id, "descricao": "Luz (futura)",
                "valor_total": 100, "conta_id": conta_id, "status": "prevista",
            })
            assert r2.status_code == 201, r2.text
            tx_ids.append(r2.json()["id"])
            assert r2.json()["data_pagamento"] is None
            assert _saldo(client, conta_id) == 850.0, _saldo(client, conta_id)
            print(f"   saldo intacto = {_saldo(client, conta_id)}")

            # ── 3. GET detalhe ────────────────────────────────────────
            print("\n→ Test 3: GET detalhe")
            rd = client.get(f"{TX}/{tx_ids[0]}")
            assert rd.status_code == 200
            assert rd.json()["descricao"] == "Mercado"
            print("   detalhe ok")

            # ── 4. Erros ──────────────────────────────────────────────
            print("\n→ Test 4: validações")
            # valor <= 0 → 422 (pydantic gt=0)
            rneg = client.post(f"{TX}/despesa", json={
                "usuario_id": usuario_id, "descricao": "x",
                "valor_total": 0, "conta_id": conta_id,
            })
            assert rneg.status_code == 422, rneg.status_code
            # conta inexistente → 404
            r404 = client.post(f"{TX}/despesa", json={
                "usuario_id": usuario_id, "descricao": "x",
                "valor_total": 10, "conta_id": str(uuid.uuid4()),
            })
            assert r404.status_code == 404, r404.status_code
            # conta de outro usuário → 400
            rmix = client.post(f"{TX}/despesa", json={
                "usuario_id": outro_usuario, "descricao": "x",
                "valor_total": 10, "conta_id": conta_id,
            })
            assert rmix.status_code == 400, rmix.status_code
            # status inválido → 400
            rst = client.post(f"{TX}/despesa", json={
                "usuario_id": usuario_id, "descricao": "x",
                "valor_total": 10, "conta_id": conta_id, "status": "zumbi",
            })
            assert rst.status_code == 400, rst.status_code
            print("   422 valor<=0 ; 404 conta ; 400 dono errado ; 400 status")

        finally:
            asyncio.run(_cleanup(conta_ids, tx_ids))

    print("\n" + "━" * 60)
    print("TUDO OK — financas Step 7 funcionando!")
    print("━" * 60)


def main() -> None:
    smoke_test()


if __name__ == "__main__":
    main()

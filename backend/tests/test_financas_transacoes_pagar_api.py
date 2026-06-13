"""Smoke test — quitar (marcar como paga) uma transação prevista.

Cobre o endpoint novo:
  POST /api/financas/transacoes/{id}/pagar

Dois caminhos:
  1. Prevista lançada COM conta (form): só efetiva, move o saldo da conta.
  2. Prevista SEM conta (boleto importado / recorrência): exige conta_id,
     cria o pagamento e move o saldo.
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.api.main import app
from app.config import settings
from tests._financas_auth import limpar_override, usar_usuario

CONTAS = "/api/financas/contas"
TX = "/api/financas/transacoes"


async def _inserir_prevista_sem_conta(
    usuario_id: str, tx_id: str, valor: float
) -> None:
    """Simula um boleto importado / recorrência: transação prevista sem
    nenhum pagamento (sem conta)."""
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.begin() as conn:
            await conn.execute(
                text(
                    "INSERT INTO financas.transacoes "
                    "(id, usuario_id, tipo, descricao, valor_total, "
                    " data_competencia, status, origem) "
                    "VALUES (:id, :uid, 'despesa', 'Condomínio', :v, "
                    " :comp, 'prevista', 'importacao_boleto')"
                ),
                {
                    "id": tx_id, "uid": usuario_id, "v": valor,
                    "comp": date.today().replace(day=1),
                },
            )
    finally:
        await eng.dispose()


async def _cleanup(conta_ids: list[str], tx_ids: list[str]) -> None:
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.begin() as conn:
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
    print("Smoke test — pagar (marcar prevista como paga)")
    print("━" * 60)

    usuario_id = str(uuid.uuid4())
    conta_ids: list[str] = []
    tx_ids: list[str] = []

    with TestClient(app) as client:
        usar_usuario(usuario_id)
        try:
            # ── Conta com saldo de abertura 1000 ──────────────────────
            r = client.post(CONTAS, json={
                "usuario_id": usuario_id, "nome": "Nubank",
                "tipo": "corrente", "saldo_atual": 1000,
            })
            assert r.status_code == 201, r.text
            conta_id = r.json()["id"]
            conta_ids.append(conta_id)

            # ══ Caminho 1: prevista lançada COM conta ════════════════
            print("\n→ Test 1: lançar prevista com conta → saldo intacto (1000)")
            r1 = client.post(f"{TX}/despesa", json={
                "usuario_id": usuario_id, "descricao": "Luz",
                "valor_total": 200, "conta_id": conta_id,
                "status": "prevista",
            })
            assert r1.status_code == 201, r1.text
            tx1 = r1.json()["id"]
            tx_ids.append(tx1)
            assert r1.json()["status"] == "prevista"
            assert _saldo(client, conta_id) == 1000.0, _saldo(client, conta_id)

            print("→ Test 2: pagar (sem conta no body) → paga, saldo 800")
            rp = client.post(f"{TX}/{tx1}/pagar", json={})
            assert rp.status_code == 200, rp.text
            assert rp.json()["status"] == "paga", rp.json()
            assert rp.json()["data_pagamento"], rp.json()
            assert _saldo(client, conta_id) == 800.0, _saldo(client, conta_id)

            print("→ Test 3: pagar de novo → 400 (já paga)")
            assert client.post(f"{TX}/{tx1}/pagar", json={}).status_code == 400

            # ══ Caminho 2: prevista SEM conta (boleto) ═══════════════
            print("\n→ Test 4: boleto sem conta → pagar sem conta_id → 400")
            tx2 = str(uuid.uuid4())
            asyncio.run(_inserir_prevista_sem_conta(usuario_id, tx2, 50))
            tx_ids.append(tx2)
            assert client.post(f"{TX}/{tx2}/pagar", json={}).status_code == 400

            print("→ Test 5: pagar com conta_id → paga, saldo 750, cria pagamento")
            rp2 = client.post(f"{TX}/{tx2}/pagar", json={"conta_id": conta_id})
            assert rp2.status_code == 200, rp2.text
            assert rp2.json()["status"] == "paga"
            assert len(rp2.json()["pagamentos"]) == 1, rp2.json()
            assert _saldo(client, conta_id) == 750.0, _saldo(client, conta_id)

            print("→ Test 6: pagar inexistente → 404")
            assert client.post(
                f"{TX}/{uuid.uuid4()}/pagar", json={"conta_id": conta_id}
            ).status_code == 404

        finally:
            limpar_override()
            asyncio.run(_cleanup(conta_ids, tx_ids))

    print("\n" + "━" * 60)
    print("TUDO OK — pagar prevista (com e sem conta) funcionando!")
    print("━" * 60)


def main() -> None:
    smoke_test()


if __name__ == "__main__":
    main()

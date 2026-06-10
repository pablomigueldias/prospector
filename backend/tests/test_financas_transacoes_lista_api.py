"""Smoke test — lista filtrável de transações + exclusão (com reversão de saldo).

Cobre os endpoints novos:
  GET    /api/financas/transacoes        (filtros: tipo, conta, busca, mês)
  DELETE /api/financas/transacoes/{id}   (reverte o saldo se a transação era paga)
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
    print("Smoke test — transações: lista filtrável + exclusão")
    print("━" * 60)

    usuario_id = str(uuid.uuid4())
    hoje = date.today()
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

            # ── Lança 2 despesas + 1 receita ──────────────────────────
            r1 = client.post(f"{TX}/despesa", json={
                "usuario_id": usuario_id, "descricao": "Mercado Pão de Açúcar",
                "valor_total": 150, "conta_id": conta_id,
            })
            assert r1.status_code == 201, r1.text
            tx_ids.append(r1.json()["id"])

            r2 = client.post(f"{TX}/despesa", json={
                "usuario_id": usuario_id, "descricao": "Uber",
                "valor_total": 30, "conta_id": conta_id,
            })
            assert r2.status_code == 201, r2.text
            tx_ids.append(r2.json()["id"])

            r3 = client.post(f"{TX}/receita", json={
                "usuario_id": usuario_id, "descricao": "Salário",
                "valor_total": 500, "conta_id": conta_id,
            })
            assert r3.status_code == 201, r3.text
            tx_ids.append(r3.json()["id"])

            # saldo: 1000 - 150 - 30 + 500 = 1320
            assert _saldo(client, conta_id) == 1320.0, _saldo(client, conta_id)

            # ── 1. Lista sem filtro → 3 itens ─────────────────────────
            print("\n→ Test 1: lista sem filtro → 3")
            l = client.get(TX).json()
            assert l["total"] == 3, l
            assert len(l["items"]) == 3
            # mais novas primeiro + nomes resolvidos
            assert l["items"][0]["contas"] == ["Nubank"], l["items"][0]
            print("   3 itens, conta resolvida =", l["items"][0]["contas"])

            # ── 2. Filtro por tipo ────────────────────────────────────
            print("\n→ Test 2: tipo=despesa → 2 ; tipo=receita → 1")
            assert client.get(f"{TX}?tipo=despesa").json()["total"] == 2
            assert client.get(f"{TX}?tipo=receita").json()["total"] == 1

            # ── 3. Busca por texto ────────────────────────────────────
            print("\n→ Test 3: busca='mercado' → 1")
            b = client.get(f"{TX}?busca=mercado").json()
            assert b["total"] == 1, b
            assert b["items"][0]["descricao"].startswith("Mercado")

            # ── 4. Filtro por conta + por mês ─────────────────────────
            print("\n→ Test 4: conta_id → 3 ; mês atual → 3 ; outro mês → 0")
            assert client.get(f"{TX}?conta_id={conta_id}").json()["total"] == 3
            assert client.get(
                f"{TX}?ano={hoje.year}&mes={hoje.month}"
            ).json()["total"] == 3
            outro_mes = 1 if hoje.month != 1 else 2
            outro_ano = hoje.year - 1  # garante sem competência aqui
            assert client.get(
                f"{TX}?ano={outro_ano}&mes={outro_mes}"
            ).json()["total"] == 0

            # ── 5. Exclui a despesa paga → reverte saldo ──────────────
            print("\n→ Test 5: excluir Mercado (150) → saldo volta +150")
            rdel = client.delete(f"{TX}/{tx_ids[0]}")
            assert rdel.status_code == 204, rdel.text
            tx_ids.pop(0)
            assert _saldo(client, conta_id) == 1470.0, _saldo(client, conta_id)
            assert client.get(TX).json()["total"] == 2
            print("   saldo agora =", _saldo(client, conta_id))

            # ── 6. Excluir inexistente → 404 ──────────────────────────
            print("\n→ Test 6: excluir inexistente → 404")
            assert client.delete(f"{TX}/{uuid.uuid4()}").status_code == 404

        finally:
            limpar_override()
            asyncio.run(_cleanup(conta_ids, tx_ids))

    print("\n" + "━" * 60)
    print("TUDO OK — lista filtrável + exclusão funcionando!")
    print("━" * 60)


def main() -> None:
    smoke_test()


if __name__ == "__main__":
    main()

"""Smoke test — orçamento por categoria (teto mensal + consumido do mês).

CRUD + GET /status: cria um teto numa categoria, lança despesas no mês e
confere que o consumido/restante/percentual batem.
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

ORC = "/api/financas/orcamentos"
CATS = "/api/financas/categorias"
CONTAS = "/api/financas/contas"
TX = "/api/financas/transacoes"


async def _cleanup(usuario_id: str) -> None:
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.begin() as conn:
            for tbl in ("orcamentos", "transacoes", "contas"):
                await conn.execute(
                    text(f"DELETE FROM financas.{tbl} WHERE usuario_id = :u"),
                    {"u": uuid.UUID(usuario_id)},
                )
    finally:
        await eng.dispose()


def smoke_test() -> None:
    print("━" * 60)
    print("Smoke test — orçamento por categoria")
    print("━" * 60)

    usuario_id = str(uuid.uuid4())
    comp = "2026-06"

    with TestClient(app) as client:
        usar_usuario(usuario_id)
        try:
            # pega uma categoria-folha do seed (qualquer uma serve)
            raiz = client.get(CATS).json()["items"][0]
            cat_id = (raiz["filhos"][0]["id"] if raiz.get("filhos") else raiz["id"])
            conta_id = client.post(CONTAS, json={
                "usuario_id": usuario_id, "nome": "Conta", "tipo": "corrente",
                "saldo_atual": 5000,
            }).json()["id"]

            # ── 1. Criar orçamento ────────────────────────────────────
            print("\n→ Test 1: POST /orcamentos")
            r = client.post(ORC, json={
                "usuario_id": usuario_id, "categoria_id": cat_id, "valor_mensal": 800,
            })
            assert r.status_code == 201, r.text
            oid = r.json()["id"]
            assert Decimal(r.json()["valor_mensal"]) == Decimal("800.00")
            print(f"   criado: teto 800 na categoria {r.json()['categoria_nome']}")

            # duplicado → 400
            assert client.post(ORC, json={
                "usuario_id": usuario_id, "categoria_id": cat_id, "valor_mensal": 100,
            }).status_code == 400
            print("   duplicado → 400 ok")

            # ── 2. Status sem gasto: consumido 0 ──────────────────────
            st = client.get(f"{ORC}/status", params={"competencia": comp}).json()
            item = next(i for i in st["items"] if i["orcamento_id"] == oid)
            assert Decimal(item["consumido"]) == Decimal("0.00"), item
            assert Decimal(item["restante"]) == Decimal("800.00"), item
            print("\n→ Test 2: status sem gasto → consumido 0, restante 800")

            # ── 3. Lança 2 despesas na categoria no mês ───────────────
            for v in (200, 350):
                client.post(f"{TX}/despesa", json={
                    "usuario_id": usuario_id, "descricao": f"Gasto {v}",
                    "valor_total": v, "conta_id": conta_id, "categoria_id": cat_id,
                    "data_competencia": "2026-06-10", "status": "paga",
                })
            print("\n→ Test 3: lança 200 + 350 na categoria")
            st2 = client.get(f"{ORC}/status", params={"competencia": comp}).json()
            it2 = next(i for i in st2["items"] if i["orcamento_id"] == oid)
            assert Decimal(it2["consumido"]) == Decimal("550.00"), it2
            assert Decimal(it2["restante"]) == Decimal("250.00"), it2
            assert abs(it2["percentual"] - 68.8) < 0.2, it2["percentual"]
            assert Decimal(st2["total_consumido"]) == Decimal("550.00"), st2
            print(f"   consumido {it2['consumido']}, restante {it2['restante']}, {it2['percentual']}%")

            # ── 4. Editar teto + desativar ────────────────────────────
            print("\n→ Test 4: PATCH teto 600")
            up = client.patch(f"{ORC}/{oid}", json={"valor_mensal": 600})
            assert up.status_code == 200 and Decimal(up.json()["valor_mensal"]) == Decimal("600.00")
            st3 = client.get(f"{ORC}/status", params={"competencia": comp}).json()
            it3 = next(i for i in st3["items"] if i["orcamento_id"] == oid)
            assert Decimal(it3["restante"]) == Decimal("50.00"), it3  # 600 − 550
            print(f"   teto 600 → restante {it3['restante']}")
            # desativa → some do status
            client.patch(f"{ORC}/{oid}", json={"ativo": False})
            st4 = client.get(f"{ORC}/status", params={"competencia": comp}).json()
            assert all(i["orcamento_id"] != oid for i in st4["items"]), "inativo não devia aparecer"
            print("   desativado → fora do status")

            # ── 5. Excluir ────────────────────────────────────────────
            print("\n→ Test 5: DELETE")
            assert client.delete(f"{ORC}/{oid}").status_code == 204
            assert client.get(ORC).json()["total"] == 0
            assert client.delete(f"{ORC}/{uuid.uuid4()}").status_code == 404
            print("   excluído; inexistente → 404")

        finally:
            limpar_override()
            asyncio.run(_cleanup(usuario_id))

    print("\n" + "━" * 60)
    print("TUDO OK — orçamento por categoria funcionando!")
    print("━" * 60)


def main() -> None:
    smoke_test()


if __name__ == "__main__":
    main()

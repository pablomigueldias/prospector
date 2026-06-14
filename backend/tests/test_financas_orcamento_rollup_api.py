from __future__ import annotations

import asyncio
import uuid
from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.api.main import app
from tests._financas_auth import usar_usuario
from app.config import settings

CATS = "/api/financas/categorias"
ORCS = "/api/financas/orcamentos"
DESPESA = "/api/financas/transacoes/despesa"
CONTAS = "/api/financas/contas"
STATUS = "/api/financas/orcamentos/status"


async def _limpar(usuario_id):
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.begin() as conn:
            for tab in ("orcamentos", "transacoes", "contas"):
                await conn.execute(text(f"DELETE FROM financas.{tab} WHERE usuario_id = :u"),
                                   {"u": uuid.UUID(usuario_id)})
            # categorias criadas no teste (pai 'Casa Teste' e filhas)
            await conn.execute(text(
                "DELETE FROM financas.categorias WHERE nome LIKE 'ZZ %'"
            ))
    finally:
        await eng.dispose()


def smoke_test() -> None:
    print("━" * 60)
    print("Smoke test — orçamento com roll-up de subcategorias")
    print("━" * 60)

    usuario_id = str(uuid.uuid4())
    comp = f"{date.today().year:04d}-{date.today().month:02d}"
    with TestClient(app) as client:
        usar_usuario(usuario_id)
        try:
            pai = client.post(CATS, json={"nome": "ZZ Casa", "tipo": "despesa"}).json()["id"]
            f1 = client.post(CATS, json={"nome": "ZZ Luz", "tipo": "despesa",
                                         "categoria_pai_id": pai}).json()["id"]
            f2 = client.post(CATS, json={"nome": "ZZ Água", "tipo": "despesa",
                                         "categoria_pai_id": pai}).json()["id"]
            conta = client.post(CONTAS, json={"usuario_id": usuario_id, "nome": "CC",
                                              "tipo": "corrente", "saldo_atual": 5000}).json()["id"]

            # orçamento de 1000 na categoria-mãe
            client.post(ORCS, json={"usuario_id": usuario_id, "categoria_id": pai,
                                    "valor_mensal": 1000})

            # gastos: 200 na mãe + 300 em Luz + 250 em Água = 750
            for cat, v in ((pai, 200), (f1, 300), (f2, 250)):
                r = client.post(DESPESA, json={
                    "usuario_id": usuario_id, "descricao": "x", "valor_total": v,
                    "conta_id": conta, "categoria_id": cat,
                    "data_competencia": f"{comp}-10", "status": "paga",
                })
                assert r.status_code == 201, r.text

            print("\n→ status do orçamento da mãe soma as filhas (750/1000)")
            b = client.get(STATUS, params={"usuario_id": usuario_id, "competencia": comp}).json()
            item = next(i for i in b["items"] if i["categoria_id"] == pai)
            assert Decimal(item["consumido"]) == Decimal("750"), item
            assert Decimal(item["restante"]) == Decimal("250"), item
            assert round(item["percentual"]) == 75, item
            print(f"   consumido={item['consumido']} restante={item['restante']} "
                  f"({item['percentual']}%)")

        finally:
            asyncio.run(_limpar(usuario_id))

    print("\n" + "━" * 60)
    print("TUDO OK — roll-up de orçamento funcionando!")
    print("━" * 60)


def main() -> None:
    smoke_test()


if __name__ == "__main__":
    main()

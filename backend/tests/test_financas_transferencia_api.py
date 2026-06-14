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

CONTAS = "/api/financas/contas"
TRANSF = "/api/financas/transacoes/transferencia"
RESUMO = "/api/financas/resumo"


async def _limpar(usuario_id):
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.begin() as conn:
            for tab in ("transacoes", "contas"):
                await conn.execute(text(f"DELETE FROM financas.{tab} WHERE usuario_id = :u"),
                                   {"u": uuid.UUID(usuario_id)})
    finally:
        await eng.dispose()


def _saldo(client, usuario_id, conta_id) -> Decimal:
    items = client.get(CONTAS, params={"usuario_id": usuario_id}).json()["items"]
    return Decimal(next(c["saldo_atual"] for c in items if c["id"] == conta_id))


def smoke_test() -> None:
    print("━" * 60)
    print("Smoke test — transferência (guardar na reserva)")
    print("━" * 60)

    usuario_id = str(uuid.uuid4())
    hoje = date.today()
    with TestClient(app) as client:
        usar_usuario(usuario_id)
        try:
            cc = client.post(CONTAS, json={"usuario_id": usuario_id, "nome": "CC",
                                           "tipo": "corrente", "saldo_atual": 1000}).json()["id"]
            reserva = client.post(CONTAS, json={"usuario_id": usuario_id, "nome": "Viagem",
                                                "tipo": "reserva", "saldo_atual": 0,
                                                "meta": 5000}).json()["id"]

            print("\n→ Test 1: guarda 300 na reserva → saldos movem")
            r = client.post(TRANSF, json={
                "usuario_id": usuario_id, "origem_conta_id": cc,
                "destino_conta_id": reserva, "valor": 300,
                "descricao": "Guardar viagem", "data": hoje.isoformat(),
            })
            assert r.status_code == 201, r.text
            assert _saldo(client, usuario_id, cc) == Decimal("700"), "CC devia cair p/ 700"
            assert _saldo(client, usuario_id, reserva) == Decimal("300"), "reserva devia ir p/ 300"
            print(f"   CC=700 reserva=300")

            print("\n→ Test 2: NÃO conta como receita/despesa no resumo")
            b = client.get(RESUMO, params={"usuario_id": usuario_id,
                                           "ano": hoje.year, "mes": hoje.month}).json()
            assert Decimal(b["total_despesas"]) == 0, b["total_despesas"]
            assert Decimal(b["total_receitas"]) == 0, b["total_receitas"]
            print(f"   resumo: despesas={b['total_despesas']} receitas={b['total_receitas']}")

            print("\n→ Test 3: origem == destino → 400")
            r = client.post(TRANSF, json={
                "usuario_id": usuario_id, "origem_conta_id": cc,
                "destino_conta_id": cc, "valor": 10,
            })
            assert r.status_code == 400, r.status_code
            print(f"   barrou: {r.json()['detail']}")

        finally:
            asyncio.run(_limpar(usuario_id))

    print("\n" + "━" * 60)
    print("TUDO OK — transferência funcionando!")
    print("━" * 60)


def main() -> None:
    smoke_test()


if __name__ == "__main__":
    main()

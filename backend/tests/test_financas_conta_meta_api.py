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

CONTAS = "/api/financas/contas"


async def _limpar(usuario_id):
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.begin() as conn:
            await conn.execute(text("DELETE FROM financas.contas WHERE usuario_id = :u"),
                               {"u": uuid.UUID(usuario_id)})
    finally:
        await eng.dispose()


def smoke_test() -> None:
    print("━" * 60)
    print("Smoke test — reserva com objetivo (meta na conta)")
    print("━" * 60)

    usuario_id = str(uuid.uuid4())
    with TestClient(app) as client:
        usar_usuario(usuario_id)
        try:
            print("\n→ Test 1: cria reserva com meta 5000")
            r = client.post(CONTAS, json={
                "usuario_id": usuario_id, "nome": "Viagem", "tipo": "reserva",
                "saldo_atual": 1500, "meta": 5000,
            })
            assert r.status_code == 201, r.text
            cid = r.json()["id"]
            assert Decimal(r.json()["meta"]) == Decimal("5000"), r.json()
            print(f"   meta={r.json()['meta']}")

            print("\n→ Test 2: aparece na listagem com a meta")
            items = client.get(CONTAS, params={"usuario_id": usuario_id}).json()["items"]
            conta = next(c for c in items if c["id"] == cid)
            assert Decimal(conta["meta"]) == Decimal("5000"), conta
            print(f"   saldo={conta['saldo_atual']} meta={conta['meta']}")

            print("\n→ Test 3: editar a meta pra 8000")
            r = client.patch(f"{CONTAS}/{cid}", json={"meta": 8000})
            assert r.status_code == 200, r.text
            assert Decimal(r.json()["meta"]) == Decimal("8000"), r.json()
            print(f"   meta={r.json()['meta']}")

            print("\n→ Test 4: conta normal nasce sem meta (null)")
            r = client.post(CONTAS, json={
                "usuario_id": usuario_id, "nome": "CC", "tipo": "corrente",
            })
            assert r.json()["meta"] is None, r.json()
            print("   meta=None ok")

        finally:
            asyncio.run(_limpar(usuario_id))

    print("\n" + "━" * 60)
    print("TUDO OK — reserva com objetivo funcionando!")
    print("━" * 60)


def main() -> None:
    smoke_test()


if __name__ == "__main__":
    main()

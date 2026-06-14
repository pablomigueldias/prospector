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


async def _limpar(usuario_id: str) -> None:
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.begin() as conn:
            # parcelas/compras/faturas saem por cascade ao apagar cartão/usuário,
            # mas limpamos explícito o que prende por usuario_id.
            await conn.execute(text(
                "DELETE FROM financas.parcelas WHERE compra_id IN "
                "(SELECT id FROM financas.compras WHERE usuario_id = :u)"
            ), {"u": uuid.UUID(usuario_id)})
            await conn.execute(text(
                "DELETE FROM financas.compras WHERE usuario_id = :u"
            ), {"u": uuid.UUID(usuario_id)})
            await conn.execute(text(
                "DELETE FROM financas.faturas WHERE cartao_id IN "
                "(SELECT id FROM financas.cartoes WHERE usuario_id = :u)"
            ), {"u": uuid.UUID(usuario_id)})
            await conn.execute(text(
                "DELETE FROM financas.transacoes WHERE usuario_id = :u"
            ), {"u": uuid.UUID(usuario_id)})
            await conn.execute(text(
                "DELETE FROM financas.cartoes WHERE usuario_id = :u"
            ), {"u": uuid.UUID(usuario_id)})
            await conn.execute(text(
                "DELETE FROM financas.contas WHERE usuario_id = :u"
            ), {"u": uuid.UUID(usuario_id)})
    finally:
        await eng.dispose()


def _em_aberto(client, cartao_id) -> Decimal:
    r = client.get(f"{CARTOES}/{cartao_id}/faturas")
    assert r.status_code == 200, r.text
    return Decimal(r.json()["total_em_aberto"])


def smoke_test() -> None:
    print("━" * 60)
    print("Smoke test — estornar (excluir) compra de cartão")
    print("━" * 60)

    usuario_id = str(uuid.uuid4())
    with TestClient(app) as client:
        usar_usuario(usuario_id)
        try:
            cartao_id = client.post(CARTOES, json={
                "usuario_id": usuario_id, "nome": "Nubank",
                "dia_fechamento": 1, "dia_vencimento": 10,
            }).json()["id"]

            print("\n→ Test 1: compra 3x de 300 → em aberto 300")
            compra = client.post(COMPRAS, json={
                "usuario_id": usuario_id, "cartao_id": cartao_id,
                "descricao": "Geladeira", "valor_total": 300, "total_parcelas": 3,
                "data_compra": "2026-06-05",
            })
            assert compra.status_code == 201, compra.text
            compra_id = compra.json()["id"]
            assert _em_aberto(client, cartao_id) == Decimal("300")
            n_faturas = len(client.get(f"{CARTOES}/{cartao_id}/faturas").json()["faturas"])
            assert n_faturas == 3, n_faturas
            print(f"   em aberto 300 / {n_faturas} faturas")

            print("\n→ Test 2: + compra à vista 100 → em aberto 400")
            avista = client.post(COMPRAS, json={
                "usuario_id": usuario_id, "cartao_id": cartao_id,
                "descricao": "Tênis", "valor_total": 100, "total_parcelas": 1,
                "data_compra": "2026-06-05",
            }).json()["id"]
            assert _em_aberto(client, cartao_id) == Decimal("400")
            print("   em aberto 400")

            print("\n→ Test 3: estorna a parcelada → em aberto volta a 100")
            r = client.delete(f"{COMPRAS}/{compra_id}")
            assert r.status_code == 204, r.text
            assert _em_aberto(client, cartao_id) == Decimal("100")
            # As 2 faturas que só tinham a parcelada somem; sobra a do à vista.
            faturas = client.get(f"{CARTOES}/{cartao_id}/faturas").json()["faturas"]
            assert len(faturas) == 1, faturas
            print(f"   em aberto 100 / faturas restantes={len(faturas)}")

            print("\n→ Test 4: estornar de novo → 404")
            r = client.delete(f"{COMPRAS}/{compra_id}")
            assert r.status_code == 404, r.status_code
            print("   404 ok")

            print("\n→ Test 5: paga a fatura do à vista e tenta estornar → bloqueia")
            conta_id = client.post(CONTAS, json={
                "usuario_id": usuario_id, "nome": "CC", "tipo": "corrente",
                "saldo_atual": 1000,
            }).json()["id"]
            fatura = client.get(f"{CARTOES}/{cartao_id}/faturas").json()["faturas"][0]
            pg = client.post(
                f"{CARTOES}/{cartao_id}/faturas/{fatura['id']}/pagar",
                json={"conta_id": conta_id},
            )
            assert pg.status_code == 200, pg.text
            r = client.delete(f"{COMPRAS}/{avista}")
            assert r.status_code == 400, r.status_code
            assert "paga" in r.json()["detail"].lower()
            print(f"   bloqueou: {r.json()['detail']}")

        finally:
            asyncio.run(_limpar(usuario_id))

    print("\n" + "━" * 60)
    print("TUDO OK — estorno de compra funcionando!")
    print("━" * 60)


def main() -> None:
    smoke_test()


if __name__ == "__main__":
    main()

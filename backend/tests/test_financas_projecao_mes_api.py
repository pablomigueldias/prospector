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

PROJECAO = "/api/financas/resumo/projecao"
CONTAS = "/api/financas/contas"


async def _inserir(usuario_id, tipo, valor, status, venc) -> None:
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.begin() as conn:
            await conn.execute(text(
                "INSERT INTO financas.transacoes "
                "(id, usuario_id, tipo, descricao, valor_total, data_competencia, "
                " data_vencimento, status, origem) "
                "VALUES (:id,:u,:t,:d,:v,:c,:venc,:s,'manual')"
            ), {"id": uuid.uuid4(), "u": uuid.UUID(usuario_id), "t": tipo,
                "d": f"{tipo} {status}", "v": valor, "c": venc, "venc": venc, "s": status})
    finally:
        await eng.dispose()


async def _limpar(usuario_id):
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.begin() as conn:
            for tab in ("transacoes", "contas"):
                await conn.execute(text(f"DELETE FROM financas.{tab} WHERE usuario_id = :u"),
                                   {"u": uuid.UUID(usuario_id)})
    finally:
        await eng.dispose()


def smoke_test() -> None:
    print("━" * 60)
    print("Smoke test — projeção de fim de mês (sobra estimada)")
    print("━" * 60)

    usuario_id = str(uuid.uuid4())
    hoje = date.today()
    dentro = date(hoje.year, hoje.month, 20)

    with TestClient(app) as client:
        usar_usuario(usuario_id)
        try:
            client.post(CONTAS, json={
                "usuario_id": usuario_id, "nome": "CC", "tipo": "corrente",
                "saldo_atual": 1000,
            })
            # a pagar: 300 prevista + 100 atrasada = 400 ; a receber: 500 prevista
            asyncio.run(_inserir(usuario_id, "despesa", 300, "prevista", dentro))
            asyncio.run(_inserir(usuario_id, "despesa", 100, "atrasada", dentro))
            asyncio.run(_inserir(usuario_id, "receita", 500, "prevista", dentro))
            # uma já paga não entra na projeção
            asyncio.run(_inserir(usuario_id, "despesa", 999, "paga", dentro))

            print("\n→ projeção do mês corrente")
            r = client.get(PROJECAO, params={"usuario_id": usuario_id,
                                             "ano": hoje.year, "mes": hoje.month})
            assert r.status_code == 200, r.text
            b = r.json()
            assert Decimal(b["saldo_atual"]) == Decimal("1000"), b
            assert Decimal(b["a_pagar"]) == Decimal("400"), b
            assert Decimal(b["a_receber"]) == Decimal("500"), b
            # 1000 + 500 - 400 = 1100
            assert Decimal(b["estimativa_sobra"]) == Decimal("1100"), b
            print(f"   saldo={b['saldo_atual']} a_pagar={b['a_pagar']} "
                  f"a_receber={b['a_receber']} → sobra {b['estimativa_sobra']}")

        finally:
            asyncio.run(_limpar(usuario_id))

    print("\n" + "━" * 60)
    print("TUDO OK — projeção de fim de mês!")
    print("━" * 60)


def main() -> None:
    smoke_test()


if __name__ == "__main__":
    main()

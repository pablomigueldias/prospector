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
PROJECAO = "/api/financas/cartoes/projecao"


async def _limpar(usuario_id: str) -> None:
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.begin() as conn:
            await conn.execute(text(
                "DELETE FROM financas.parcelas WHERE compra_id IN "
                "(SELECT id FROM financas.compras WHERE usuario_id = :u)"
            ), {"u": uuid.UUID(usuario_id)})
            for tab in ("compras", "transacoes"):
                await conn.execute(text(
                    f"DELETE FROM financas.{tab} WHERE usuario_id = :u"
                ), {"u": uuid.UUID(usuario_id)})
            await conn.execute(text(
                "DELETE FROM financas.faturas WHERE cartao_id IN "
                "(SELECT id FROM financas.cartoes WHERE usuario_id = :u)"
            ), {"u": uuid.UUID(usuario_id)})
            await conn.execute(text(
                "DELETE FROM financas.cartoes WHERE usuario_id = :u"
            ), {"u": uuid.UUID(usuario_id)})
            await conn.execute(text(
                "DELETE FROM financas.contas WHERE usuario_id = :u"
            ), {"u": uuid.UUID(usuario_id)})
    finally:
        await eng.dispose()


def _proj(client, usuario_id, meses=6):
    r = client.get(PROJECAO, params={"usuario_id": usuario_id, "meses": meses})
    assert r.status_code == 200, r.text
    return r.json()


def smoke_test() -> None:
    print("━" * 60)
    print("Smoke test — projeção consolidada das próximas faturas")
    print("━" * 60)

    from datetime import date
    usuario_id = str(uuid.uuid4())
    with TestClient(app) as client:
        usar_usuario(usuario_id)
        try:
            cartao_id = client.post(CARTOES, json={
                "usuario_id": usuario_id, "nome": "Nubank",
                "dia_fechamento": 28, "dia_vencimento": 5,
            }).json()["id"]

            print("\n→ Test 1: sem compras → projeção vazia")
            b = _proj(client, usuario_id)
            assert b["meses"] == [] and Decimal(b["total"]) == 0, b
            print("   vazio ok")

            print("\n→ Test 2: compra 3x de 300 → 3 meses, total 300")
            client.post(COMPRAS, json={
                "usuario_id": usuario_id, "cartao_id": cartao_id,
                "descricao": "Geladeira", "valor_total": 300, "total_parcelas": 3,
                "data_compra": date.today().isoformat(),
            })
            b = _proj(client, usuario_id)
            assert len(b["meses"]) == 3, b["meses"]
            assert Decimal(b["total"]) == Decimal("300"), b["total"]
            # cada mês ~100 e a soma fecha em 300
            soma = sum(Decimal(m["total"]) for m in b["meses"])
            assert soma == Decimal("300"), soma
            print(f"   {[ (m['mes_referencia'], m['total']) for m in b['meses'] ]}")

            print("\n→ Test 3: paga a 1ª fatura → cai pra 2 meses, total 200")
            conta_id = client.post(CONTAS, json={
                "usuario_id": usuario_id, "nome": "CC", "tipo": "corrente",
                "saldo_atual": 1000,
            }).json()["id"]
            faturas = client.get(f"{CARTOES}/{cartao_id}/faturas").json()["faturas"]
            # mais antiga primeiro (a lista vem desc; pega a de menor mes_ref)
            alvo = sorted(faturas, key=lambda f: f["mes_referencia"])[0]
            pg = client.post(
                f"{CARTOES}/{cartao_id}/faturas/{alvo['id']}/pagar",
                json={"conta_id": conta_id},
            )
            assert pg.status_code == 200, pg.text
            b = _proj(client, usuario_id)
            assert len(b["meses"]) == 2, b["meses"]
            assert Decimal(b["total"]) == Decimal("200"), b["total"]
            print(f"   total agora {b['total']}")

            print("\n→ Test 4: janela curta (1 mês) só pega o mês corrente")
            b = _proj(client, usuario_id, meses=1)
            assert len(b["meses"]) <= 1, b["meses"]
            print(f"   meses={len(b['meses'])}")

        finally:
            asyncio.run(_limpar(usuario_id))

    print("\n" + "━" * 60)
    print("TUDO OK — projeção consolidada funcionando!")
    print("━" * 60)


def main() -> None:
    smoke_test()


if __name__ == "__main__":
    main()

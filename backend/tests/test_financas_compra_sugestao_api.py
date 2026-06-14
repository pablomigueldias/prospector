from __future__ import annotations

import asyncio
import uuid

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.api.main import app
from tests._financas_auth import usar_usuario
from app.config import settings

CARTOES = "/api/financas/cartoes"
COMPRAS = "/api/financas/compras"
CATS = "/api/financas/categorias"
SUG = "/api/financas/compras/sugestao-categoria"


async def _limpar(usuario_id: str) -> None:
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.begin() as conn:
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
                "DELETE FROM financas.cartoes WHERE usuario_id = :u"
            ), {"u": uuid.UUID(usuario_id)})
    finally:
        await eng.dispose()


def _root_id(client, nome):
    for it in client.get(CATS).json()["items"]:
        if it["nome"] == nome:
            return it["id"]
    raise AssertionError(nome)


def smoke_test() -> None:
    print("━" * 60)
    print("Smoke test — auto-categoria por compra (sugestão)")
    print("━" * 60)

    usuario_id = str(uuid.uuid4())
    with TestClient(app) as client:
        usar_usuario(usuario_id)
        try:
            transporte = _root_id(client, "Transporte")
            cartao_id = client.post(CARTOES, json={
                "usuario_id": usuario_id, "nome": "Nubank",
                "dia_fechamento": 28, "dia_vencimento": 5,
            }).json()["id"]

            print("\n→ Test 1: sem histórico → sugestão vazia")
            r = client.get(SUG, params={"usuario_id": usuario_id, "descricao": "Posto Shell"})
            assert r.status_code == 200, r.text
            assert r.json()["categoria_id"] is None, r.json()
            print("   vazio ok")

            print("\n→ Test 2: lança compra 'Posto Shell' c/ Transporte")
            client.post(COMPRAS, json={
                "usuario_id": usuario_id, "cartao_id": cartao_id,
                "descricao": "Posto Shell", "valor_total": 200, "total_parcelas": 1,
                "categoria_id": transporte,
            })

            print("\n→ Test 3: mesma descrição (case-insensitive) → sugere Transporte")
            r = client.get(SUG, params={"usuario_id": usuario_id, "descricao": "  posto shell "})
            assert r.status_code == 200, r.text
            assert r.json()["categoria_id"] == transporte, r.json()
            assert r.json()["categoria_nome"] == "Transporte", r.json()
            print(f"   sugeriu {r.json()['categoria_nome']}")

            print("\n→ Test 4: descrição diferente → vazio")
            r = client.get(SUG, params={"usuario_id": usuario_id, "descricao": "Mercado"})
            assert r.json()["categoria_id"] is None
            print("   vazio ok")

        finally:
            asyncio.run(_limpar(usuario_id))

    print("\n" + "━" * 60)
    print("TUDO OK — auto-categoria por compra funcionando!")
    print("━" * 60)


def main() -> None:
    smoke_test()


if __name__ == "__main__":
    main()

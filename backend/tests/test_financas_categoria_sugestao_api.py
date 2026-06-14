"""Smoke — auto-categoria que aprende (§8): a sugestão de categoria pega a da
última DESPESA do usuário com a mesma descrição.

GET /api/financas/transacoes/sugestao-categoria?descricao=...
"""
from __future__ import annotations

import asyncio
import uuid

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.api.main import app
from app.config import settings
from tests._financas_auth import usar_usuario

CONTAS = "/api/financas/contas"
TX = "/api/financas/transacoes"
CATS = "/api/financas/categorias"
SUG = "/api/financas/transacoes/sugestao-categoria"


async def _limpar(usuario_id: str) -> None:
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.begin() as conn:
            await conn.execute(text(
                "DELETE FROM financas.transacoes WHERE usuario_id = :u"
            ), {"u": uuid.UUID(usuario_id)})
            await conn.execute(text(
                "DELETE FROM financas.contas WHERE usuario_id = :u"
            ), {"u": uuid.UUID(usuario_id)})
    finally:
        await eng.dispose()


def _root_id(client: TestClient, nome: str) -> str:
    for it in client.get(CATS).json()["items"]:
        if it["nome"] == nome:
            return it["id"]
    raise AssertionError(f"categoria raiz {nome!r} não encontrada")


def smoke_test() -> None:
    print("━" * 60)
    print("Smoke test — auto-categoria que aprende (despesa)")
    print("━" * 60)

    usuario_id = str(uuid.uuid4())
    with TestClient(app) as client:
        usar_usuario(usuario_id)
        try:
            alimentacao = _root_id(client, "Alimentação")
            conta_id = client.post(CONTAS, json={
                "usuario_id": usuario_id, "nome": "Nubank",
                "tipo": "corrente", "saldo_atual": 1000,
            }).json()["id"]

            print("\n→ Test 1: sem histórico → sugestão vazia")
            r = client.get(SUG, params={"usuario_id": usuario_id, "descricao": "Mercado Dia"})
            assert r.status_code == 200, r.text
            assert r.json()["categoria_id"] is None, r.json()
            print("   vazio ok")

            print("\n→ Test 2: lança despesa 'Mercado Dia' c/ Alimentação")
            r2 = client.post(f"{TX}/despesa", json={
                "usuario_id": usuario_id, "descricao": "Mercado Dia",
                "valor_total": 80, "conta_id": conta_id, "categoria_id": alimentacao,
            })
            assert r2.status_code == 201, r2.text

            print("\n→ Test 3: mesma descrição (case/spaces) → sugere Alimentação")
            r3 = client.get(SUG, params={"usuario_id": usuario_id, "descricao": "  mercado dia "})
            assert r3.status_code == 200, r3.text
            assert r3.json()["categoria_id"] == alimentacao, r3.json()
            assert r3.json()["categoria_nome"] == "Alimentação", r3.json()
            print(f"   sugeriu {r3.json()['categoria_nome']}")

            print("\n→ Test 4: descrição diferente → vazio")
            r4 = client.get(SUG, params={"usuario_id": usuario_id, "descricao": "Cinema"})
            assert r4.json()["categoria_id"] is None, r4.json()
            print("   vazio ok")

            print("\n→ Test 5: descrição vazia → vazio (sem erro)")
            r5 = client.get(SUG, params={"usuario_id": usuario_id, "descricao": "   "})
            assert r5.status_code == 200 and r5.json()["categoria_id"] is None
            print("   vazio ok")
        finally:
            asyncio.run(_limpar(usuario_id))

    print("\n" + "━" * 60)
    print("TUDO OK — auto-categoria que aprende funcionando!")
    print("━" * 60)


def main() -> None:
    smoke_test()


if __name__ == "__main__":
    main()

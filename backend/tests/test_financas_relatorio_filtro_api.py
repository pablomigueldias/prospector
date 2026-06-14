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

RELATORIO = "/api/financas/resumo/relatorio"
CONTAS = "/api/financas/contas"
CATS = "/api/financas/categorias"
DESPESA = "/api/financas/transacoes/despesa"


async def _limpar(usuario_id: str) -> None:
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.begin() as conn:
            await conn.execute(
                text("DELETE FROM financas.transacoes WHERE usuario_id = :u"),
                {"u": uuid.UUID(usuario_id)},
            )
            await conn.execute(
                text("DELETE FROM financas.contas WHERE usuario_id = :u"),
                {"u": uuid.UUID(usuario_id)},
            )
    finally:
        await eng.dispose()


def _root_id(client: TestClient, nome: str) -> str:
    for it in client.get(CATS).json()["items"]:
        if it["nome"] == nome:
            return it["id"]
    raise AssertionError(f"categoria raiz {nome!r} não encontrada no seed")


def _despesa_total(client, usuario_id, **extra) -> Decimal:
    params = {"usuario_id": usuario_id, "ano": 2026, "mes": 3, "meses": 1, **extra}
    r = client.get(RELATORIO, params=params)
    assert r.status_code == 200, r.text
    return Decimal(r.json()["total_despesas"])


def smoke_test() -> None:
    print("━" * 60)
    print("Smoke test — relatório com recorte por conta/categoria")
    print("━" * 60)

    usuario_id = str(uuid.uuid4())
    with TestClient(app) as client:
        usar_usuario(usuario_id)
        try:
            transporte = _root_id(client, "Transporte")
            alimentacao = _root_id(client, "Alimentação")

            nubank = client.post(CONTAS, json={
                "usuario_id": usuario_id, "nome": "Nubank", "tipo": "corrente",
            }).json()["id"]
            vr = client.post(CONTAS, json={
                "usuario_id": usuario_id, "nome": "VR", "tipo": "vr",
            }).json()["id"]

            def lancar(desc, valor, conta, cat):
                r = client.post(DESPESA, json={
                    "usuario_id": usuario_id, "descricao": desc, "valor_total": valor,
                    "conta_id": conta, "categoria_id": cat,
                    "data_competencia": "2026-03-10", "status": "paga",
                })
                assert r.status_code == 201, r.text

            lancar("Gasolina", 100, nubank, transporte)
            lancar("Uber", 50, nubank, transporte)
            lancar("Mercado", 200, vr, alimentacao)

            print("\n→ Test 1: sem recorte → soma tudo")
            assert _despesa_total(client, usuario_id) == Decimal("350")
            print("   350 ok")

            print("\n→ Test 2: só Nubank → 150")
            assert _despesa_total(client, usuario_id, conta_id=nubank) == Decimal("150")
            print("   150 ok")

            print("\n→ Test 3: só Alimentação → 200")
            assert _despesa_total(client, usuario_id, categoria_id=alimentacao) == Decimal("200")
            print("   200 ok")

            print("\n→ Test 4: Nubank + Transporte → 150 (e top categoria só Transporte)")
            params = {"usuario_id": usuario_id, "ano": 2026, "mes": 3, "meses": 1,
                      "conta_id": nubank, "categoria_id": transporte}
            b = client.get(RELATORIO, params=params).json()
            assert Decimal(b["total_despesas"]) == Decimal("150"), b["total_despesas"]
            nomes = [c["categoria_nome"] for c in b["por_categoria"]]
            assert nomes == ["Transporte"], nomes
            print(f"   150 / categorias={nomes}")

            print("\n→ Test 5: conta inexistente → 0, não erra")
            assert _despesa_total(client, usuario_id, conta_id=str(uuid.uuid4())) == Decimal("0")
            print("   0 ok")

        finally:
            asyncio.run(_limpar(usuario_id))

    print("\n" + "━" * 60)
    print("TUDO OK — recorte do relatório funcionando!")
    print("━" * 60)


def main() -> None:
    smoke_test()


if __name__ == "__main__":
    main()

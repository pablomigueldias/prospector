from __future__ import annotations

import asyncio
import uuid
from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.api.main import app
from app.config import settings

RESUMO = "/api/financas/resumo"
CATS = "/api/financas/categorias"


async def _inserir(usuario_id: str, linhas: list[dict]) -> list[str]:
    """Insere transações direto no banco (controle fino de competência/tipo)."""
    eng = create_async_engine(settings.database_url)
    ids: list[str] = []
    try:
        async with eng.begin() as conn:
            for ln in linhas:
                tid = uuid.uuid4()
                ids.append(str(tid))
                await conn.execute(
                    text(
                        "INSERT INTO financas.transacoes "
                        "(id, usuario_id, tipo, descricao, valor_total, "
                        " data_competencia, status, origem, categoria_id) "
                        "VALUES (:id, :uid, :tipo, :desc, :valor, :comp, "
                        " 'paga', 'manual', :cat)"
                    ),
                    {
                        "id": tid, "uid": uuid.UUID(usuario_id), "tipo": ln["tipo"],
                        "desc": ln["desc"], "valor": ln["valor"], "comp": ln["comp"],
                        "cat": uuid.UUID(ln["cat"]) if ln.get("cat") else None,
                    },
                )
    finally:
        await eng.dispose()
    return ids


async def _limpar(ids: list[str]) -> None:
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.begin() as conn:
            for tid in ids:
                await conn.execute(
                    text("DELETE FROM financas.transacoes WHERE id = :id"), {"id": tid}
                )
    finally:
        await eng.dispose()


def _root_id(client: TestClient, nome: str) -> str:
    for it in client.get(CATS).json()["items"]:
        if it["nome"] == nome:
            return it["id"]
    raise AssertionError(f"categoria raiz {nome!r} não encontrada no seed")


def smoke_test() -> None:
    print("━" * 60)
    print("Smoke test — financas Step 9 (resumo do mês)")
    print("━" * 60)

    usuario_id = str(uuid.uuid4())
    ids: list[str] = []
    with TestClient(app) as client:
        try:
            transporte = _root_id(client, "Transporte")
            alimentacao = _root_id(client, "Alimentação")

            # Mês alvo: 2026-03. Uma despesa em 2026-04 pra testar o filtro.
            ids = asyncio.run(_inserir(usuario_id, [
                {"tipo": "despesa", "desc": "Gasolina", "valor": 100, "comp": date(2026, 3, 5), "cat": transporte},
                {"tipo": "despesa", "desc": "Uber", "valor": 50, "comp": date(2026, 3, 9), "cat": transporte},
                {"tipo": "despesa", "desc": "Mercado", "valor": 200, "comp": date(2026, 3, 12), "cat": alimentacao},
                {"tipo": "despesa", "desc": "Sem cat", "valor": 30, "comp": date(2026, 3, 20), "cat": None},
                {"tipo": "receita", "desc": "Salário", "valor": 1000, "comp": date(2026, 3, 1), "cat": None},
                {"tipo": "despesa", "desc": "OUTRO MÊS", "valor": 999, "comp": date(2026, 4, 1), "cat": transporte},
            ]))

            print("\n→ Test 1: totais do mês 2026-03")
            r = client.get(RESUMO, params={"usuario_id": usuario_id, "ano": 2026, "mes": 3})
            assert r.status_code == 200, r.text
            b = r.json()
            assert Decimal(b["total_despesas"]) == Decimal("380"), b["total_despesas"]
            assert Decimal(b["total_receitas"]) == Decimal("1000"), b["total_receitas"]
            assert Decimal(b["saldo"]) == Decimal("620"), b["saldo"]
            print(f"   despesas={b['total_despesas']} receitas={b['total_receitas']} saldo={b['saldo']}")

            print("\n→ Test 2: quebra por categoria (maior → menor)")
            cats = [(c["categoria_nome"], Decimal(c["total"])) for c in b["por_categoria"]]
            assert cats == [
                ("Alimentação", Decimal("200")),
                ("Transporte", Decimal("150")),
                ("Sem categoria", Decimal("30")),
            ], cats
            print(f"   {cats}")

            print("\n→ Test 3: mês sem dados zera tudo")
            r2 = client.get(RESUMO, params={"usuario_id": usuario_id, "ano": 2026, "mes": 1})
            assert Decimal(r2.json()["total_despesas"]) == 0
            assert r2.json()["por_categoria"] == []
            print("   jan/26 zerado")

            print("\n→ Test 4: mês inválido → 400")
            r3 = client.get(RESUMO, params={"usuario_id": usuario_id, "ano": 2026, "mes": 13})
            assert r3.status_code == 400, r3.status_code
            print(f"   barrou: {r3.json()['detail']}")

        finally:
            asyncio.run(_limpar(ids))

    print("\n" + "━" * 60)
    print("TUDO OK — financas Step 9 funcionando!")
    print("━" * 60)


def main() -> None:
    smoke_test()


if __name__ == "__main__":
    main()

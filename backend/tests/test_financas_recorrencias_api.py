from __future__ import annotations

import asyncio
import uuid

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.api.main import app
from app.config import settings

REC = "/api/financas/recorrencias"
CATS = "/api/financas/categorias"
CONTAS = "/api/financas/contas"


async def _status_por_descricao(usuario_id: str) -> dict[str, str]:
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.connect() as conn:
            rows = await conn.execute(
                text(
                    "SELECT descricao, status FROM financas.transacoes "
                    "WHERE usuario_id = :uid"
                ),
                {"uid": uuid.UUID(usuario_id)},
            )
            return {desc: st for desc, st in rows.all()}
    finally:
        await eng.dispose()


async def _cleanup(usuario_id: str, conta_ids: list[str]) -> None:
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.begin() as conn:
            await conn.execute(
                text("DELETE FROM financas.transacoes WHERE usuario_id = :uid"),
                {"uid": uuid.UUID(usuario_id)},
            )
            await conn.execute(
                text("DELETE FROM financas.recorrencias WHERE usuario_id = :uid"),
                {"uid": uuid.UUID(usuario_id)},
            )
            for cid in conta_ids:
                await conn.execute(
                    text("DELETE FROM financas.contas WHERE id = :id"), {"id": cid}
                )
    finally:
        await eng.dispose()


def _subverba(client: TestClient, pai: str, filho: str) -> str:
    for raiz in client.get(CATS).json()["items"]:
        if raiz["nome"] == pai:
            for f in raiz["filhos"]:
                if f["nome"] == filho:
                    return f["id"]
    raise AssertionError(f"{pai}/{filho} não achado no seed")


def smoke_test() -> None:
    print("━" * 60)
    print("Smoke test — financas Step 12 (recorrências + job)")
    print("━" * 60)

    usuario_id = str(uuid.uuid4())
    conta_ids: list[str] = []

    with TestClient(app) as client:
        try:
            conta_id = client.post(CONTAS, json={
                "usuario_id": usuario_id, "nome": "Nubank",
                "tipo": "corrente", "saldo_atual": 5000,
            }).json()["id"]
            conta_ids.append(conta_id)
            aluguel = _subverba(client, "Moradia", "Aluguel")
            luz = _subverba(client, "Moradia", "Luz (Enel)")

            # ── Cadastra 2 recorrências: vence dia 5 e dia 25 ─────────
            print("\n→ Test 1: cadastra recorrências")
            r1 = client.post(REC, json={
                "usuario_id": usuario_id, "descricao": "Aluguel",
                "valor_estimado": 1500, "dia_vencimento": 5,
                "categoria_id": aluguel, "conta_id": conta_id,
            })
            assert r1.status_code == 201, r1.text
            r2 = client.post(REC, json={
                "usuario_id": usuario_id, "descricao": "Luz",
                "valor_estimado": 200, "dia_vencimento": 25, "categoria_id": luz,
            })
            assert r2.status_code == 201, r2.text
            assert client.get(REC, params={"usuario_id": usuario_id}).json()["total"] == 2
            print("   2 recorrências (dia 5 e dia 25)")

            # ── Processa em 2026-03-20: gera 2 previstas; só a do dia 5 atrasa ─
            print("\n→ Test 2: processa em 2026-03-20")
            rp = client.post(f"{REC}/processar", params={
                "usuario_id": usuario_id, "ref": "2026-03-20",
            })
            assert rp.status_code == 200, rp.text
            assert rp.json() == {"previstas_criadas": 2, "marcadas_atrasadas": 1}, rp.json()
            status = asyncio.run(_status_por_descricao(usuario_id))
            assert status == {"Aluguel": "atrasada", "Luz": "prevista"}, status
            print(f"   {rp.json()} ; status={status}")

            # ── Idempotência: rodar de novo não duplica nem re-marca ──
            print("\n→ Test 3: idempotente")
            rp2 = client.post(f"{REC}/processar", params={
                "usuario_id": usuario_id, "ref": "2026-03-20",
            })
            assert rp2.json() == {"previstas_criadas": 0, "marcadas_atrasadas": 0}, rp2.json()
            print(f"   {rp2.json()}")

            # ── Erros ─────────────────────────────────────────────────
            print("\n→ Test 4: validações")
            rbad = client.post(REC, json={
                "usuario_id": usuario_id, "descricao": "x",
                "valor_estimado": 10, "dia_vencimento": 5, "tipo": "zumbi",
            })
            assert rbad.status_code == 400, rbad.status_code
            print(f"   tipo inválido → 400")

        finally:
            asyncio.run(_cleanup(usuario_id, conta_ids))

    print("\n" + "━" * 60)
    print("TUDO OK — financas Step 12 funcionando!")
    print("━" * 60)


def main() -> None:
    smoke_test()


if __name__ == "__main__":
    main()

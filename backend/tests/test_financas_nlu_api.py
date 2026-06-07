from __future__ import annotations

import asyncio
import json
import uuid

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.analyzers.nlu import extrator
from app.api.main import app
from app.config import settings

CONTAS = "/api/financas/contas"
NLU = "/api/financas/nlu/interpretar"


async def _cleanup(usuario_id: str) -> None:
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.begin() as conn:
            await conn.execute(
                text("DELETE FROM financas.contas WHERE usuario_id = :u"),
                {"u": uuid.UUID(usuario_id)},
            )
    finally:
        await eng.dispose()


def smoke_test() -> None:
    print("━" * 60)
    print("Smoke test — financas Step 17 (NLU texto → rascunho)")
    print("━" * 60)

    usuario_id = str(uuid.uuid4())
    original = extrator.interpretar_llm
    with TestClient(app) as client:
        try:
            client.post(CONTAS, json={
                "usuario_id": usuario_id, "nome": "Carteira", "tipo": "dinheiro",
            })

            # ── 1. "gastei 50 no mercado hoje" → resolve conta+categoria ─
            print("\n→ Test 1: frase resolve conta e categoria")
            extrator.interpretar_llm = lambda p: json.dumps({
                "tipo": "despesa", "valor": 50, "descricao": "mercado",
                "categoria": "Mercado", "conta": "Carteira", "data": "2026-06-07",
            })
            r = client.post(NLU, json={
                "usuario_id": usuario_id, "texto": "gastei 50 no mercado hoje",
            })
            assert r.status_code == 200, r.text
            b = r.json()
            assert b["tipo"] == "despesa" and float(b["valor"]) == 50.0
            assert b["conta_nome"] == "Carteira" and b["conta_id"]
            assert b["categoria_nome"] == "Mercado" and b["categoria_id"]
            assert b["data"] == "2026-06-07"
            print(f"   {b['descricao']} → conta={b['conta_nome']} categoria={b['categoria_nome']}")

            # ── 2. Nome fora das listas → id None (não inventa) ───────
            print("\n→ Test 2: conta inexistente → conta_id None")
            extrator.interpretar_llm = lambda p: json.dumps({
                "tipo": "receita", "valor": 3200, "descricao": "salário",
                "categoria": "Inexistente", "conta": "Banco XPTO", "data": None,
            })
            r2 = client.post(NLU, json={
                "usuario_id": usuario_id, "texto": "salário caiu 3200",
            })
            assert r2.status_code == 200, r2.text
            b2 = r2.json()
            assert b2["tipo"] == "receita"
            assert b2["conta_id"] is None and b2["categoria_id"] is None
            assert b2["data"]  # default hoje
            print(f"   sem match: conta_id={b2['conta_id']} categoria_id={b2['categoria_id']}")

            # ── 3. LLM devolve lixo → 400 ─────────────────────────────
            print("\n→ Test 3: resposta ininteligível → 400")
            extrator.interpretar_llm = lambda p: "desculpa, não sei"
            r3 = client.post(NLU, json={"usuario_id": usuario_id, "texto": "???"})
            assert r3.status_code == 400, r3.status_code

            # ── 4. Texto vazio → 400 ──────────────────────────────────
            r4 = client.post(NLU, json={"usuario_id": usuario_id, "texto": "  "})
            assert r4.status_code == 400, r4.status_code
            print("   lixo → 400 ; vazio → 400")

        finally:
            extrator.interpretar_llm = original
            asyncio.run(_cleanup(usuario_id))

    print("\n" + "━" * 60)
    print("TUDO OK — financas Step 17 funcionando!")
    print("━" * 60)


def main() -> None:
    smoke_test()


if __name__ == "__main__":
    main()

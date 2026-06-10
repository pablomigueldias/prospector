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

LEITURAS = "/api/financas/leituras"


async def _cleanup(usuario_id: str) -> None:
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.begin() as conn:
            await conn.execute(
                text("DELETE FROM financas.leituras_consumo WHERE usuario_id = :uid"),
                {"uid": uuid.UUID(usuario_id)},
            )
    finally:
        await eng.dispose()


def smoke_test() -> None:
    print("━" * 60)
    print("Smoke test — financas Step 13 (leituras de consumo)")
    print("━" * 60)

    usuario_id = str(uuid.uuid4())
    with TestClient(app) as client:
        usar_usuario(usuario_id)  # dono = sessão (override de auth)
        try:
            # ── 1. Consumo calculado (atual − anterior) ───────────────
            print("\n→ Test 1: consumo calculado")
            r = client.post(LEITURAS, json={
                "usuario_id": usuario_id, "tipo": "gas",
                "mes_referencia": "2026-05-01",
                "leitura_atual": 120.5, "leitura_anterior": 97.3, "valor": 88.40,
            })
            assert r.status_code == 201, r.text
            assert Decimal(r.json()["consumo"]) == Decimal("23.200"), r.json()["consumo"]
            print(f"   consumo gás mai/26 = {r.json()['consumo']}")

            # ── 2. Outro mês de gás + uma de água ─────────────────────
            client.post(LEITURAS, json={
                "usuario_id": usuario_id, "tipo": "gas",
                "mes_referencia": "2026-06-01",
                "leitura_atual": 145.0, "leitura_anterior": 120.5,
            })
            client.post(LEITURAS, json={
                "usuario_id": usuario_id, "tipo": "agua",
                "mes_referencia": "2026-06-01", "leitura_atual": 1000, "consumo": 8,
            })

            # ── 3. Lista por tipo, ordenada por mês (tendência) ───────
            print("\n→ Test 2: tendência de gás (2 meses, em ordem)")
            rg = client.get(LEITURAS, params={"usuario_id": usuario_id, "tipo": "gas"})
            meses = [x["mes_referencia"] for x in rg.json()["items"]]
            assert rg.json()["total"] == 2
            assert meses == ["2026-05-01", "2026-06-01"], meses
            print(f"   gás: {meses}")

            # ── 4. Lista geral = 3 leituras ───────────────────────────
            rall = client.get(LEITURAS, params={"usuario_id": usuario_id})
            assert rall.json()["total"] == 3
            print(f"   total de leituras = {rall.json()['total']}")

            # ── 5. Tipo inválido → 400 ────────────────────────────────
            print("\n→ Test 3: tipo inválido → 400")
            rbad = client.post(LEITURAS, json={
                "usuario_id": usuario_id, "tipo": "vento",
                "mes_referencia": "2026-06-01", "leitura_atual": 1,
            })
            assert rbad.status_code == 400, rbad.status_code
            print(f"   barrou: {rbad.json()['detail']}")

        finally:
            asyncio.run(_cleanup(usuario_id))

    print("\n" + "━" * 60)
    print("TUDO OK — financas Step 13 funcionando!")
    print("━" * 60)


def main() -> None:
    smoke_test()


if __name__ == "__main__":
    main()

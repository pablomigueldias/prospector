from __future__ import annotations

import asyncio
import uuid

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.api.main import app
from tests._financas_auth import usar_usuario
from app.config import settings
from app.utils.s3_storage import get_storage

COMP = "/api/financas/comprovantes"


async def _cleanup(usuario_id: str) -> None:
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.connect() as conn:
            objs = (await conn.execute(
                text("SELECT bucket, arquivo_path FROM financas.comprovantes WHERE usuario_id = :u"),
                {"u": uuid.UUID(usuario_id)},
            )).all()
        for bucket, key in objs:
            try:
                get_storage().client.delete_object(Bucket=bucket, Key=key)
            except Exception:
                pass
        async with eng.begin() as conn:
            await conn.execute(
                text("DELETE FROM financas.comprovantes WHERE usuario_id = :u"),
                {"u": uuid.UUID(usuario_id)},
            )
    finally:
        await eng.dispose()


def smoke_test() -> None:
    print("━" * 60)
    print("Smoke test — financas Step 26 (galeria de comprovantes)")
    print("━" * 60)

    usuario_id = str(uuid.uuid4())
    with TestClient(app) as client:
        usar_usuario(usuario_id)  # dono = sessão (override de auth)
        try:
            client.post(COMP, data={"usuario_id": usuario_id, "tipo": "boleto"},
                        files={"file": ("b.pdf", b"%PDF boleto", "application/pdf")})
            client.post(COMP, data={"usuario_id": usuario_id, "tipo": "nota_fiscal"},
                        files={"file": ("n.xml", b"<nota/>", "application/xml")})

            # ── 1. Galeria do usuário = 2, com URL ────────────────────
            print("\n→ Test 1: galeria por usuário")
            r = client.get(COMP, params={"usuario_id": usuario_id})
            assert r.status_code == 200, r.text
            assert r.json()["total"] == 2
            assert all(it["url"] and it["url"].startswith("http") for it in r.json()["items"])
            print(f"   {r.json()['total']} comprovantes com URL")

            # ── 2. Filtro por tipo ────────────────────────────────────
            print("\n→ Test 2: filtro tipo=boleto")
            rb = client.get(COMP, params={"usuario_id": usuario_id, "tipo": "boleto"})
            assert rb.json()["total"] == 1
            assert rb.json()["items"][0]["tipo"] == "boleto"
            print("   1 boleto")

            # ── 3. Sem transacao_id → galeria do usuário logado (sessão)
            print("\n→ Test 3: sem transacao_id → galeria do logado")
            rg = client.get(COMP)
            assert rg.status_code == 200, rg.text
            assert rg.json()["total"] == 2, rg.json()["total"]
            print("   lista a galeria do usuário da sessão ok")

        finally:
            asyncio.run(_cleanup(usuario_id))

    print("\n" + "━" * 60)
    print("TUDO OK — financas Step 26 (backend) funcionando!")
    print("━" * 60)


def main() -> None:
    smoke_test()


if __name__ == "__main__":
    main()

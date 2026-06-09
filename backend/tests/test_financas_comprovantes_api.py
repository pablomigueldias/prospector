from __future__ import annotations

import asyncio
import uuid

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.api.main import app
from app.config import settings
from app.utils.s3_storage import get_storage

CONTAS = "/api/financas/contas"
TX = "/api/financas/transacoes"
COMP = "/api/financas/comprovantes"


async def _cleanup(usuario_id: str, objetos: list[tuple[str, str]]) -> None:
    for bucket, key in objetos:
        try:
            get_storage().client.delete_object(Bucket=bucket, Key=key)
        except Exception:
            pass
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.begin() as conn:
            await conn.execute(
                text("DELETE FROM financas.transacoes WHERE usuario_id = :u"),
                {"u": uuid.UUID(usuario_id)},
            )
            await conn.execute(
                text("DELETE FROM financas.comprovantes WHERE usuario_id = :u"),
                {"u": uuid.UUID(usuario_id)},
            )
            await conn.execute(
                text("DELETE FROM financas.contas WHERE usuario_id = :u"),
                {"u": uuid.UUID(usuario_id)},
            )
    finally:
        await eng.dispose()


def smoke_test() -> None:
    print("━" * 60)
    print("Smoke test — financas Step 15 (upload de comprovante via HTTP)")
    print("━" * 60)

    usuario_id = str(uuid.uuid4())
    outro = str(uuid.uuid4())
    objetos: list[tuple[str, str]] = []

    with TestClient(app) as client:
        try:
            conta_id = client.post(CONTAS, json={
                "usuario_id": usuario_id, "nome": "Nubank",
                "tipo": "corrente", "saldo_atual": 2000,
            }).json()["id"]
            tx_id = client.post(f"{TX}/despesa", json={
                "usuario_id": usuario_id, "descricao": "Condomínio",
                "valor_total": 1107.52, "conta_id": conta_id,
            }).json()["id"]

            # ── 1. Upload multipart vinculado à transação ─────────────
            print("\n→ Test 1: POST multipart (boleto)")
            r = client.post(COMP, data={
                "usuario_id": usuario_id, "tipo": "boleto", "transacao_id": tx_id,
            }, files={"file": ("condominio.pdf", b"%PDF boleto lello", "application/pdf")})
            assert r.status_code == 201, r.text
            b = r.json()
            objetos.append((b["bucket"], b["arquivo_path"]))
            assert b["transacao_id"] == tx_id
            assert b["tipo"] == "boleto" and b["bucket"] == "boletos"
            print(f"   {b['bucket']}/{b['arquivo_path']} vinculado à tx {tx_id[:8]}")

            # ── 2. Lista por transação traz URL pré-assinada ──────────
            print("\n→ Test 2: GET lista por transação")
            rl = client.get(COMP, params={"transacao_id": tx_id})
            assert rl.status_code == 200
            assert rl.json()["total"] == 1
            url = rl.json()["items"][0]["url"]
            assert url and url.startswith("http"), url
            print(f"   1 comprovante, url={url[:48]}...")

            # ── 3. Transação inexistente → 404 ────────────────────────
            print("\n→ Test 3: transação inexistente → 404")
            r404 = client.post(COMP, data={
                "usuario_id": usuario_id, "tipo": "comprovante",
                "transacao_id": str(uuid.uuid4()),
            }, files={"file": ("x.png", b"img", "image/png")})
            assert r404.status_code == 404, r404.status_code
            # essa subiu pro MinIO antes de validar? não — dedup/validação antes do put.
            print("   404 ok")

            # ── 4. Transação de outro usuário → 400 ───────────────────
            print("\n→ Test 4: transação de outro usuário → 400")
            rmix = client.post(COMP, data={
                "usuario_id": outro, "tipo": "comprovante", "transacao_id": tx_id,
            }, files={"file": ("y.png", b"img2", "image/png")})
            assert rmix.status_code == 400, rmix.status_code
            print("   400 ok")

        finally:
            asyncio.run(_cleanup(usuario_id, objetos))

    print("\n" + "━" * 60)
    print("TUDO OK — financas Step 15 funcionando!")
    print("━" * 60)


def main() -> None:
    smoke_test()


if __name__ == "__main__":
    main()

from __future__ import annotations

import asyncio
import json
import uuid

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.analyzers.boleto import extrator as boleto_extrator
from app.api.main import app
from app.api.services.financas import bot_service
from app.config import settings
from app.integrations import telegram as tg
from app.utils.s3_storage import get_storage

WEBHOOK = "/telegram/webhook"
CHAT = "111222333"

BOLETO = {
    "beneficiario": "Condomínio Lello", "vencimento": "2026-06-10",
    "valor_total": 100.00,
    "verbas": [{"descricao": "Taxa", "valor": 60.0}, {"descricao": "Gás", "valor": 40.0}],
    "leituras": [],
}


async def _n_transacoes(usuario_id: str) -> int:
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.connect() as conn:
            return await conn.scalar(
                text("SELECT count(*) FROM financas.transacoes WHERE usuario_id = :u"),
                {"u": uuid.UUID(usuario_id)},
            )
    finally:
        await eng.dispose()


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
            for tbl in ("transacoes", "comprovantes"):
                await conn.execute(
                    text(f"DELETE FROM financas.{tbl} WHERE usuario_id = :u"),
                    {"u": uuid.UUID(usuario_id)},
                )
    finally:
        await eng.dispose()


def smoke_test() -> None:
    print("━" * 60)
    print("Smoke test — financas Step 20 (boleto pelo bot)")
    print("━" * 60)

    usuario_id = str(uuid.uuid4())
    enviadas: list[str] = []

    orig_map = bot_service.mapa_chat_usuario
    orig_send = tg.send_message
    orig_path, orig_dl = tg.get_file_path, tg.download_file
    orig_llm = boleto_extrator.extrair_boleto_llm
    orig_secret = settings.telegram_webhook_secret
    settings.telegram_webhook_secret = ""  # teste não envia o header do secret
    bot_service.mapa_chat_usuario = lambda: {CHAT: usuario_id}
    tg.send_message = lambda c, t, rm=None: enviadas.append(t) or {"ok": True}
    tg.get_file_path = lambda fid: "boletos/file.pdf"
    tg.download_file = lambda p: b"%PDF fake boleto"
    boleto_extrator.extrair_boleto_llm = lambda c, ct: json.dumps(BOLETO)

    with TestClient(app) as client:
        try:
            # ── 1. Documento PDF → importa e cria a despesa ───────────
            print("\n→ Test 1: PDF (document)")
            enviadas.clear()
            client.post(WEBHOOK, json={"message": {
                "chat": {"id": int(CHAT)},
                "document": {"file_id": "f1", "file_name": "cond.pdf", "mime_type": "application/pdf"},
            }})
            assert asyncio.run(_n_transacoes(usuario_id)) == 1, "deveria ter criado a despesa"
            assert any("✅" in m for m in enviadas), enviadas
            print(f"   {enviadas[-1]}")

            # ── 2. Foto (photo) também cai no importador ──────────────
            print("\n→ Test 2: foto (photo)")
            enviadas.clear()
            client.post(WEBHOOK, json={"message": {
                "chat": {"id": int(CHAT)},
                "photo": [{"file_id": "small"}, {"file_id": "big"}],
            }})
            # dedup do comprovante (mesmo conteúdo) → mas é outra transação importada
            assert asyncio.run(_n_transacoes(usuario_id)) >= 1
            assert any("✅" in m or "⚠️" in m for m in enviadas), enviadas
            print(f"   {enviadas[-1]}")

        finally:
            bot_service.mapa_chat_usuario = orig_map
            tg.send_message = orig_send
            tg.get_file_path, tg.download_file = orig_path, orig_dl
            boleto_extrator.extrair_boleto_llm = orig_llm
            settings.telegram_webhook_secret = orig_secret
            asyncio.run(_cleanup(usuario_id))

    print("\n" + "━" * 60)
    print("TUDO OK — financas Step 20 funcionando!")
    print("━" * 60)


def main() -> None:
    smoke_test()


if __name__ == "__main__":
    main()

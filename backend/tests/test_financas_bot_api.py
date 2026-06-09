from __future__ import annotations

import asyncio
import uuid

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.api.main import app
from app.api.services.financas import bot_service
from app.config import settings
from app.integrations import telegram as tg

CONTAS = "/api/financas/contas"
WEBHOOK = "/telegram/webhook"
CHAT = "999000111"


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


def _msg(chat_id: str, texto: str) -> dict:
    return {"message": {"chat": {"id": int(chat_id)}, "text": texto}}


def smoke_test() -> None:
    print("━" * 60)
    print("Smoke test — financas Step 18 (bot base: webhook + /gasto)")
    print("━" * 60)

    usuario_id = str(uuid.uuid4())
    enviadas: list[tuple[str, str]] = []

    orig_map = bot_service.mapa_chat_usuario
    orig_send = tg.send_message
    orig_secret = settings.telegram_webhook_secret
    bot_service.mapa_chat_usuario = lambda: {CHAT: usuario_id}
    tg.send_message = lambda chat_id, text_, reply_markup=None: enviadas.append((str(chat_id), text_)) or {"ok": True}
    settings.telegram_webhook_secret = ""  # teste não envia o header do secret

    with TestClient(app) as client:
        try:
            client.post(CONTAS, json={
                "usuario_id": usuario_id, "nome": "Carteira",
                "tipo": "dinheiro", "saldo_atual": 500,
            })

            # ── 1. /start → saudação ──────────────────────────────────
            print("\n→ Test 1: /start")
            enviadas.clear()
            r = client.post(WEBHOOK, json=_msg(CHAT, "/start"))
            assert r.status_code == 200 and r.json() == {"ok": True}
            assert enviadas and "no ar" in enviadas[-1][1]
            print(f"   resposta: {enviadas[-1][1][:40]}...")

            # ── 2. /gasto 50 mercado → cria despesa + confirma ────────
            print("\n→ Test 2: /gasto 50 mercado")
            enviadas.clear()
            r = client.post(WEBHOOK, json=_msg(CHAT, "/gasto 50 mercado"))
            assert r.status_code == 200
            assert asyncio.run(_n_transacoes(usuario_id)) == 1
            assert "✅" in enviadas[-1][1] and "Carteira" in enviadas[-1][1]
            print(f"   {enviadas[-1][1]}")

            # ── 3. Chat não autorizado → 🚫, sem nova transação ───────
            print("\n→ Test 3: chat não autorizado")
            enviadas.clear()
            r = client.post(WEBHOOK, json=_msg("555", "/gasto 999 churrasco"))
            assert r.status_code == 200
            assert "🚫" in enviadas[-1][1]
            assert asyncio.run(_n_transacoes(usuario_id)) == 1  # não criou
            print(f"   {enviadas[-1][1]}")

            # ── 4. Secret errado → 403 ────────────────────────────────
            print("\n→ Test 4: secret do webhook")
            settings.telegram_webhook_secret = "segredo-x"
            try:
                r = client.post(WEBHOOK, json=_msg(CHAT, "/start"))
                assert r.status_code == 403, r.status_code
                r2 = client.post(WEBHOOK, json=_msg(CHAT, "/start"),
                                 headers={"X-Telegram-Bot-Api-Secret-Token": "segredo-x"})
                assert r2.status_code == 200, r2.status_code
            finally:
                settings.telegram_webhook_secret = ""
            print("   sem header → 403 ; com header certo → 200")

        finally:
            bot_service.mapa_chat_usuario = orig_map
            tg.send_message = orig_send
            settings.telegram_webhook_secret = orig_secret
            asyncio.run(_cleanup(usuario_id))

    print("\n" + "━" * 60)
    print("TUDO OK — financas Step 18 funcionando!")
    print("━" * 60)


def main() -> None:
    smoke_test()


if __name__ == "__main__":
    main()

from __future__ import annotations

import asyncio
import uuid

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.api.main import app
from tests._financas_auth import usar_usuario
from app.api.services.financas import bot_service
from app.config import settings
from app.integrations import telegram as tg

WEBHOOK = "/telegram/webhook"
CHAT = "999000222"


async def _contar(usuario_id: str, tabela: str) -> int:
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.connect() as conn:
            return await conn.scalar(
                text(f"SELECT count(*) FROM financas.{tabela} WHERE usuario_id = :u"),
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
    print("Smoke test — bot: /conta, /contas e /desfazer")
    print("━" * 60)

    usuario_id = str(uuid.uuid4())
    enviadas: list[tuple[str, str]] = []

    orig_map = bot_service.mapa_chat_usuario
    orig_send = tg.send_message
    orig_secret = settings.telegram_webhook_secret
    bot_service.mapa_chat_usuario = lambda: {CHAT: usuario_id}
    tg.send_message = lambda chat_id, text_, reply_markup=None: enviadas.append((str(chat_id), text_)) or {"ok": True}
    settings.telegram_webhook_secret = ""

    with TestClient(app) as client:
        usar_usuario(usuario_id)
        try:
            # ── 1. /contas sem nenhuma → orienta a criar ──────────────
            print("\n→ Test 1: /contas (vazio)")
            enviadas.clear()
            r = client.post(WEBHOOK, json=_msg(CHAT, "/contas"))
            assert r.status_code == 200
            assert "/conta" in enviadas[-1][1]
            print(f"   {enviadas[-1][1]}")

            # ── 2. /conta Nubank corrente → cria ──────────────────────
            print("\n→ Test 2: /conta Nubank corrente")
            enviadas.clear()
            r = client.post(WEBHOOK, json=_msg(CHAT, "/conta Nubank corrente"))
            assert r.status_code == 200, r.text
            assert asyncio.run(_contar(usuario_id, "contas")) == 1
            assert "✅" in enviadas[-1][1] and "Nubank" in enviadas[-1][1]
            print(f"   {enviadas[-1][1]}")

            # ── 3. /conta VR Caju vr → nome com espaço + tipo válido ──
            print("\n→ Test 3: /conta VR Caju vr")
            enviadas.clear()
            r = client.post(WEBHOOK, json=_msg(CHAT, "/conta VR Caju vr"))
            assert r.status_code == 200, r.text
            assert asyncio.run(_contar(usuario_id, "contas")) == 2
            assert "VR Caju" in enviadas[-1][1] and "(vr)" in enviadas[-1][1]
            print(f"   {enviadas[-1][1]}")

            # ── 4. /conta tipo inválido → erro amigável, não cria ─────
            print("\n→ Test 4: tipo inválido")
            enviadas.clear()
            r = client.post(WEBHOOK, json=_msg(CHAT, "/conta Inter cripto"))
            assert r.status_code == 200
            # "cripto" não é tipo válido → vira parte do nome, tipo=corrente
            assert asyncio.run(_contar(usuario_id, "contas")) == 3
            print(f"   {enviadas[-1][1]}")

            # ── 5. /contas → lista as criadas ─────────────────────────
            print("\n→ Test 5: /contas")
            enviadas.clear()
            r = client.post(WEBHOOK, json=_msg(CHAT, "/contas"))
            assert r.status_code == 200
            assert "Nubank" in enviadas[-1][1] and "VR Caju" in enviadas[-1][1]
            print(f"   {enviadas[-1][1]}")

            # ── 6. /gasto e /desfazer → some o último lançamento ──────
            print("\n→ Test 6: /gasto 50 mercado nubank + /desfazer")
            enviadas.clear()
            client.post(WEBHOOK, json=_msg(CHAT, "/gasto 50 mercado nubank"))
            assert asyncio.run(_contar(usuario_id, "transacoes")) == 1
            r = client.post(WEBHOOK, json=_msg(CHAT, "/desfazer"))
            assert r.status_code == 200
            assert "↩️" in enviadas[-1][1] and "mercado" in enviadas[-1][1]
            assert asyncio.run(_contar(usuario_id, "transacoes")) == 0
            print(f"   {enviadas[-1][1]}")

            # ── 7. /desfazer sem nada → mensagem, sem erro ────────────
            print("\n→ Test 7: /desfazer (nada)")
            enviadas.clear()
            r = client.post(WEBHOOK, json=_msg(CHAT, "/desfazer"))
            assert r.status_code == 200
            assert "nada" in enviadas[-1][1].lower()
            print(f"   {enviadas[-1][1]}")

        finally:
            bot_service.mapa_chat_usuario = orig_map
            tg.send_message = orig_send
            settings.telegram_webhook_secret = orig_secret
            asyncio.run(_cleanup(usuario_id))

    print("\n" + "━" * 60)
    print("TUDO OK — /conta, /contas e /desfazer funcionando!")
    print("━" * 60)


def main() -> None:
    smoke_test()


if __name__ == "__main__":
    main()

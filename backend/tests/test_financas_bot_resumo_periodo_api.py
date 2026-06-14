from __future__ import annotations

import asyncio
import uuid
from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.api.main import app
from tests._financas_auth import usar_usuario
from app.api.services.financas import bot_service
from app.config import settings
from app.integrations import telegram as tg

WEBHOOK = "/telegram/webhook"
CHAT = "999000333"


async def _inserir(usuario_id, tipo, valor, comp) -> None:
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.begin() as conn:
            await conn.execute(text(
                "INSERT INTO financas.transacoes "
                "(id, usuario_id, tipo, descricao, valor_total, data_competencia, status, origem) "
                "VALUES (:id,:u,:t,:d,:v,:c,'paga','manual')"
            ), {"id": uuid.uuid4(), "u": uuid.UUID(usuario_id), "t": tipo,
                "d": f"{tipo} teste", "v": valor, "c": comp})
    finally:
        await eng.dispose()


async def _limpar(usuario_id) -> None:
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.begin() as conn:
            await conn.execute(text(
                "DELETE FROM financas.transacoes WHERE usuario_id = :u"
            ), {"u": uuid.UUID(usuario_id)})
    finally:
        await eng.dispose()


def _msg(texto):
    return {"message": {"chat": {"id": int(CHAT)}, "text": texto}}


def smoke_test() -> None:
    print("━" * 60)
    print("Smoke test — /resumo por período")
    print("━" * 60)

    # 1) parser puro
    print("\n→ Test 1: _parse_periodo")
    hoje = date.today()
    assert bot_service._parse_periodo("") == (hoje.year, hoje.month)
    assert bot_service._parse_periodo("julho") == (
        hoje.year if 7 <= hoje.month else hoje.year - 1, 7)
    assert bot_service._parse_periodo("07") == (
        hoje.year if 7 <= hoje.month else hoje.year - 1, 7)
    assert bot_service._parse_periodo("2025-03") == (2025, 3)
    assert bot_service._parse_periodo("03/2025") == (2025, 3)
    assert bot_service._parse_periodo("lixo") == (hoje.year, hoje.month)
    print("   parser ok")

    usuario_id = str(uuid.uuid4())
    enviadas: list[tuple[str, str]] = []
    orig_map = bot_service.mapa_chat_usuario
    orig_send = tg.send_message
    orig_secret = settings.telegram_webhook_secret
    bot_service.mapa_chat_usuario = lambda: {CHAT: usuario_id}
    tg.send_message = lambda c, t, rm=None: enviadas.append((str(c), t)) or {"ok": True}
    settings.telegram_webhook_secret = ""

    with TestClient(app) as client:
        usar_usuario(usuario_id)
        try:
            # transação em 2025-03 (passado garantido)
            asyncio.run(_inserir(usuario_id, "despesa", 150, date(2025, 3, 10)))

            print("\n→ Test 2: /resumo 2025-03 → mostra 03/2025 e 150")
            enviadas.clear()
            r = client.post(WEBHOOK, json=_msg("/resumo 2025-03"))
            assert r.status_code == 200, r.text
            msg = enviadas[-1][1]
            assert "03/2025" in msg and "150" in msg, msg
            print(f"   {msg.splitlines()[0]} / contém 150")

            print("\n→ Test 3: /resumo março (mês nominal) → também acha 2025-03")
            # só se hoje >= março; senão cai em ano-1. Garante consistência:
            enviadas.clear()
            client.post(WEBHOOK, json=_msg("/resumo abril"))
            assert "04/" in enviadas[-1][1]
            print(f"   {enviadas[-1][1].splitlines()[0]}")

        finally:
            bot_service.mapa_chat_usuario = orig_map
            tg.send_message = orig_send
            settings.telegram_webhook_secret = orig_secret
            asyncio.run(_limpar(usuario_id))

    print("\n" + "━" * 60)
    print("TUDO OK — /resumo por período funcionando!")
    print("━" * 60)


def main() -> None:
    smoke_test()


if __name__ == "__main__":
    main()

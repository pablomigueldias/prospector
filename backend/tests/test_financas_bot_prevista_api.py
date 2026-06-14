from __future__ import annotations

import asyncio
import json
import uuid
from datetime import date, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.api.main import app
from tests._financas_auth import usar_usuario
from app.api.services.financas import bot_service
from app.config import settings
from app.integrations import telegram as tg

CONTAS = "/api/financas/contas"
WEBHOOK = "/telegram/webhook"
CHAT = "999000444"


async def _criar_rascunho(usuario_id, payload) -> str:
    rid = uuid.uuid4()
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.begin() as conn:
            await conn.execute(text(
                "INSERT INTO financas.bot_rascunhos (id, usuario_id, chat_id, payload) "
                "VALUES (:id, :u, :c, CAST(:p AS jsonb))"
            ), {"id": rid, "u": uuid.UUID(usuario_id), "c": CHAT, "p": json.dumps(payload)})
    finally:
        await eng.dispose()
    return str(rid)


async def _saldo_e_ultima(usuario_id):
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.connect() as conn:
            saldo = await conn.scalar(text(
                "SELECT saldo_atual FROM financas.contas WHERE usuario_id = :u LIMIT 1"
            ), {"u": uuid.UUID(usuario_id)})
            row = (await conn.execute(text(
                "SELECT status, data_vencimento FROM financas.transacoes "
                "WHERE usuario_id = :u ORDER BY created_at DESC LIMIT 1"
            ), {"u": uuid.UUID(usuario_id)})).first()
        return saldo, row
    finally:
        await eng.dispose()


async def _limpar(usuario_id):
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.begin() as conn:
            for tab in ("bot_rascunhos", "transacoes", "contas"):
                await conn.execute(
                    text(f"DELETE FROM financas.{tab} WHERE usuario_id = :u"),
                    {"u": uuid.UUID(usuario_id)},
                )
    finally:
        await eng.dispose()


def _callback(rid):
    return {"callback_query": {
        "id": "cb1", "data": f"confirmar:{rid}",
        "message": {"chat": {"id": int(CHAT)}},
    }}


def smoke_test() -> None:
    print("━" * 60)
    print("Smoke test — bot: lançar despesa prevista (agendada)")
    print("━" * 60)

    hoje = date.today()
    futuro = hoje + timedelta(days=5)

    print("\n→ Test 1: _eh_prevista (heurística)")
    assert bot_service._eh_prevista("vou pagar 200 de luz", hoje) is True
    assert bot_service._eh_prevista("gastei 50 no mercado", hoje) is False
    assert bot_service._eh_prevista("paguei a conta", futuro) is True  # data futura
    print("   heurística ok")

    usuario_id = str(uuid.uuid4())
    enviadas: list = []
    orig_map = bot_service.mapa_chat_usuario
    orig_send = tg.send_message
    orig_ans = tg.answer_callback_query
    orig_secret = settings.telegram_webhook_secret
    bot_service.mapa_chat_usuario = lambda: {CHAT: usuario_id}
    tg.send_message = lambda c, t, rm=None: enviadas.append((str(c), t)) or {"ok": True}
    tg.answer_callback_query = lambda *a, **k: {"ok": True}
    settings.telegram_webhook_secret = ""

    with TestClient(app) as client:
        usar_usuario(usuario_id)
        try:
            conta_id = client.post(CONTAS, json={
                "usuario_id": usuario_id, "nome": "CC", "tipo": "corrente",
                "saldo_atual": 1000,
            }).json()["id"]

            print("\n→ Test 2: confirmar prevista → status prevista, saldo intacto")
            rid = asyncio.run(_criar_rascunho(usuario_id, {
                "tipo": "despesa", "valor": "200", "descricao": "Luz",
                "data": futuro.isoformat(), "conta_id": conta_id,
                "categoria_id": None, "prevista": True,
            }))
            enviadas.clear()
            r = client.post(WEBHOOK, json=_callback(rid))
            assert r.status_code == 200, r.text
            saldo, row = asyncio.run(_saldo_e_ultima(usuario_id))
            assert row[0] == "prevista", row
            assert str(row[1]) == futuro.isoformat(), row
            assert Decimal(saldo) == Decimal("1000"), saldo
            assert "🗓️" in enviadas[-1][1], enviadas[-1][1]
            print(f"   status={row[0]} vence={row[1]} saldo={saldo}")

            print("\n→ Test 3: confirmar paga → saldo desce")
            rid2 = asyncio.run(_criar_rascunho(usuario_id, {
                "tipo": "despesa", "valor": "50", "descricao": "Mercado",
                "data": hoje.isoformat(), "conta_id": conta_id,
                "categoria_id": None, "prevista": False,
            }))
            enviadas.clear()
            client.post(WEBHOOK, json=_callback(rid2))
            saldo, row = asyncio.run(_saldo_e_ultima(usuario_id))
            assert row[0] == "paga", row
            assert Decimal(saldo) == Decimal("950"), saldo
            print(f"   status={row[0]} saldo={saldo}")

        finally:
            bot_service.mapa_chat_usuario = orig_map
            tg.send_message = orig_send
            tg.answer_callback_query = orig_ans
            settings.telegram_webhook_secret = orig_secret
            asyncio.run(_limpar(usuario_id))

    print("\n" + "━" * 60)
    print("TUDO OK — prevista pelo bot funcionando!")
    print("━" * 60)


def main() -> None:
    smoke_test()


if __name__ == "__main__":
    main()

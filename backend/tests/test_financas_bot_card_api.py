from __future__ import annotations

import asyncio
import json
import uuid

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.analyzers.nlu import extrator
from app.api.main import app
from app.api.services.financas import bot_service
from app.config import settings
from app.integrations import telegram as tg

CONTAS = "/api/financas/contas"
WEBHOOK = "/telegram/webhook"
CHAT = "888777666"


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
            for tbl in ("transacoes", "bot_rascunhos", "contas"):
                await conn.execute(
                    text(f"DELETE FROM financas.{tbl} WHERE usuario_id = :u"),
                    {"u": uuid.UUID(usuario_id)},
                )
    finally:
        await eng.dispose()


def _msg(texto: str) -> dict:
    return {"message": {"chat": {"id": int(CHAT)}, "text": texto}}


def _cb(data: str) -> dict:
    return {"callback_query": {"id": "cb1", "data": data, "message": {"chat": {"id": int(CHAT)}}}}


def _rid_do_card(enviadas: list) -> str:
    _, _, markup = enviadas[-1]
    cb = markup["inline_keyboard"][0][0]["callback_data"]   # "confirmar:rid"
    return cb.split(":", 1)[1]


def smoke_test() -> None:
    print("━" * 60)
    print("Smoke test — financas Step 19 (card de confirmação)")
    print("━" * 60)

    usuario_id = str(uuid.uuid4())
    enviadas: list[tuple] = []

    orig_map = bot_service.mapa_chat_usuario
    orig_send, orig_ans = tg.send_message, tg.answer_callback_query
    orig_llm = extrator.interpretar_llm
    bot_service.mapa_chat_usuario = lambda: {CHAT: usuario_id}
    tg.send_message = lambda c, t, rm=None: enviadas.append((str(c), t, rm)) or {"ok": True}
    tg.answer_callback_query = lambda cid, text_=None: {"ok": True}

    with TestClient(app) as client:
        try:
            client.post(CONTAS, json={
                "usuario_id": usuario_id, "nome": "Carteira",
                "tipo": "dinheiro", "saldo_atual": 500,
            })

            # NLU mockado: "gastei 50 no mercado" → despesa na Carteira
            extrator.interpretar_llm = lambda p: json.dumps({
                "tipo": "despesa", "valor": 50, "descricao": "mercado",
                "categoria": None, "conta": "Carteira", "data": "2026-06-07",
            })

            # ── 1. Texto livre → card com botões ──────────────────────
            print("\n→ Test 1: texto livre → card")
            enviadas.clear()
            client.post(WEBHOOK, json=_msg("gastei 50 no mercado hoje"))
            assert enviadas, "nada enviado"
            chat, txt, markup = enviadas[-1]
            assert markup and "inline_keyboard" in markup
            assert "Confirma?" in txt and "Carteira" in txt
            rid = _rid_do_card(enviadas)
            assert asyncio.run(_n_transacoes(usuario_id)) == 0  # ainda não gravou
            print(f"   card enviado (rascunho {rid[:8]}), nada gravado ainda")

            # ── 2. Confirmar → cria a transação ───────────────────────
            print("\n→ Test 2: clica Confirmar")
            enviadas.clear()
            client.post(WEBHOOK, json=_cb(f"confirmar:{rid}"))
            assert asyncio.run(_n_transacoes(usuario_id)) == 1
            assert "✅" in enviadas[-1][1]
            print(f"   {enviadas[-1][1]}")

            # confirmar de novo (rascunho já consumido) → expirou
            enviadas.clear()
            client.post(WEBHOOK, json=_cb(f"confirmar:{rid}"))
            assert "expirou" in enviadas[-1][1]
            assert asyncio.run(_n_transacoes(usuario_id)) == 1  # não duplicou
            print("   reconfirmar não duplica (rascunho consumido)")

            # ── 3. Cancelar não grava ─────────────────────────────────
            print("\n→ Test 3: outro texto → Cancelar")
            enviadas.clear()
            client.post(WEBHOOK, json=_msg("gastei 30 na padaria"))
            rid2 = _rid_do_card(enviadas)
            enviadas.clear()
            client.post(WEBHOOK, json=_cb(f"cancelar:{rid2}"))
            assert "❌" in enviadas[-1][1]
            assert asyncio.run(_n_transacoes(usuario_id)) == 1  # segue 1
            print(f"   {enviadas[-1][1]} (nada gravado)")

        finally:
            bot_service.mapa_chat_usuario = orig_map
            tg.send_message, tg.answer_callback_query = orig_send, orig_ans
            extrator.interpretar_llm = orig_llm
            asyncio.run(_cleanup(usuario_id))

    print("\n" + "━" * 60)
    print("TUDO OK — financas Step 19 funcionando!")
    print("━" * 60)


def main() -> None:
    smoke_test()


if __name__ == "__main__":
    main()

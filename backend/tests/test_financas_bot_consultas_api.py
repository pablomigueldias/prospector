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
TX = "/api/financas/transacoes"
WEBHOOK = "/telegram/webhook"
CHAT = "777666555"


async def _cleanup(usuario_id: str) -> None:
    eng = create_async_engine(settings.database_url)
    try:
        async with eng.begin() as conn:
            for tbl in ("transacoes", "contas"):
                await conn.execute(
                    text(f"DELETE FROM financas.{tbl} WHERE usuario_id = :u"),
                    {"u": uuid.UUID(usuario_id)},
                )
    finally:
        await eng.dispose()


def _msg(texto: str) -> dict:
    return {"message": {"chat": {"id": int(CHAT)}, "text": texto}}


def smoke_test() -> None:
    print("━" * 60)
    print("Smoke test — financas Step 21 (consultas no bot)")
    print("━" * 60)

    # roteamento de intenção (não precisa de I/O)
    assert bot_service._consulta_intent("gastei 50 no mercado") is None
    assert bot_service._consulta_intent("quanto gastei esse mês?") == "resumo"
    assert bot_service._consulta_intent("qual meu saldo?") == "saldo"
    print("\n→ Test 0: intent — lançamento≠consulta, 'quanto'→resumo, 'saldo'→saldo ✓")

    usuario_id = str(uuid.uuid4())
    enviadas: list[str] = []
    orig_map, orig_send = bot_service.mapa_chat_usuario, tg.send_message
    bot_service.mapa_chat_usuario = lambda: {CHAT: usuario_id}
    tg.send_message = lambda c, t, rm=None: enviadas.append(t) or {"ok": True}

    with TestClient(app) as client:
        try:
            conta_id = client.post(CONTAS, json={
                "usuario_id": usuario_id, "nome": "Carteira",
                "tipo": "dinheiro", "saldo_atual": 500,
            }).json()["id"]
            client.post(f"{TX}/despesa", json={
                "usuario_id": usuario_id, "descricao": "Mercado",
                "valor_total": 50, "conta_id": conta_id,
            })

            # ── 1. "qual meu saldo" → mostra saldo da conta ───────────
            print("\n→ Test 1: consulta de saldo")
            enviadas.clear()
            client.post(WEBHOOK, json=_msg("qual meu saldo?"))
            assert "Carteira" in enviadas[-1] and "450" in enviadas[-1], enviadas[-1]
            print(f"   {enviadas[-1].splitlines()[0]} ... (saldo 450)")

            # ── 2. "quanto gastei esse mês" → resumo ──────────────────
            print("\n→ Test 2: resumo do mês")
            enviadas.clear()
            client.post(WEBHOOK, json=_msg("quanto gastei esse mês?"))
            assert "Despesas: R$ 50" in enviadas[-1], enviadas[-1]
            print(f"   {[l for l in enviadas[-1].splitlines() if 'Despesas' in l]}")

        finally:
            bot_service.mapa_chat_usuario, tg.send_message = orig_map, orig_send
            asyncio.run(_cleanup(usuario_id))

    print("\n" + "━" * 60)
    print("TUDO OK — financas Step 21 funcionando!")
    print("━" * 60)


def main() -> None:
    smoke_test()


if __name__ == "__main__":
    main()

"""Dispatch do bot do Telegram (Organizador Financeiro).

Handler manual: o webhook entrega o Update (dict), aqui a gente decide o que
fazer e responde via app.integrations.telegram. Auth por chat_id.

Era um arquivo-deus de ~547 linhas; foi quebrado por responsabilidade (ver
docs/ORGANIZACAO_REFATORACAO.md): `_base` (config/envio/helpers), `comandos`
(/gasto, /saldo, …), `nlu` (texto livre → card → confirmar) e `arquivo`
(boleto por foto/PDF). O **roteamento** (`processar_update`/`_callback`) mora
aqui no `__init__` de propósito: os testes fazem monkeypatch de
`bot_service.mapa_chat_usuario`, então o roteador precisa lê-lo deste namespace.
"""
from __future__ import annotations

import asyncio
import uuid

from app.db.models.financas.bot_rascunho import BotRascunho
from app.db.session import get_session
from app.integrations import telegram as tg

from ._base import (
    AJUDA,
    BOAS_VINDAS,
    _consulta_intent,
    _eh_prevista,
    _parse_periodo,
    _responder,
    mapa_chat_usuario,
)
from .arquivo import _arquivo
from .comandos import (
    _cmd_conta,
    _cmd_desfazer,
    _cmd_lancar,
    _listar_contas,
    _resumo_mes,
    _saldos,
)
from .nlu import _confirmar, _texto_livre

__all__ = [
    "processar_update",
    "mapa_chat_usuario",
    "_consulta_intent",
    "_eh_prevista",
    "_parse_periodo",
]


async def processar_update(update: dict) -> dict:
    # Clique num botão do card de confirmação.
    if "callback_query" in update:
        return await _callback(update["callback_query"])

    msg = update.get("message") or update.get("edited_message")
    if not msg:
        return {"ok": True, "ignorado": True}

    chat_id = str(msg.get("chat", {}).get("id", ""))
    usuario_id = mapa_chat_usuario().get(chat_id)
    if usuario_id is None:
        await _responder(
            chat_id,
            "🚫 Este bot é privado.\n\n"
            "Se você deve ter acesso, passe este código pro dono te liberar:\n"
            f"<code>{chat_id}</code>",
        )
        return {"ok": True, "autorizado": False, "chat_id": chat_id}

    # Foto ou PDF → importador de boleto.
    if msg.get("photo") or msg.get("document"):
        return await _arquivo(chat_id, usuario_id, msg)

    texto = (msg.get("text") or "").strip()

    if texto.startswith("/start"):
        await _responder(chat_id, BOAS_VINDAS + AJUDA)
        return {"ok": True, "comando": "start"}

    if texto.startswith(("/help", "/ajuda")):
        await _responder(chat_id, AJUDA)
        return {"ok": True, "comando": "help"}

    if texto.startswith("/gasto"):
        return await _cmd_lancar(chat_id, usuario_id, texto, tipo="despesa")

    if texto.startswith(("/ganho", "/receita")):
        return await _cmd_lancar(chat_id, usuario_id, texto, tipo="receita")

    if texto.startswith("/saldo"):
        return await _saldos(chat_id, usuario_id)

    if texto.startswith("/resumo"):
        return await _resumo_mes(chat_id, usuario_id, texto)

    if texto.startswith("/contas"):
        return await _listar_contas(chat_id, usuario_id)

    if texto.startswith("/conta"):
        return await _cmd_conta(chat_id, usuario_id, texto)

    if texto.startswith(("/desfazer", "/undo")):
        return await _cmd_desfazer(chat_id, usuario_id)

    if texto and not texto.startswith("/"):
        intent = _consulta_intent(texto)
        if intent == "saldo":
            return await _saldos(chat_id, usuario_id)
        if intent == "resumo":
            return await _resumo_mes(chat_id, usuario_id)
        return await _texto_livre(chat_id, usuario_id, texto)

    await _responder(chat_id, "Não entendi esse comando 🤔\n\n" + AJUDA)
    return {"ok": True, "comando": None}


async def _callback(cq: dict) -> dict:
    cq_id = cq.get("id")
    chat_id = str(cq.get("message", {}).get("chat", {}).get("id", ""))
    if cq_id:
        await asyncio.to_thread(tg.answer_callback_query, cq_id)

    usuario_id = mapa_chat_usuario().get(chat_id)
    if usuario_id is None:
        return {"ok": True, "autorizado": False}

    acao, _, rid = (cq.get("data") or "").partition(":")
    try:
        rid_uuid = uuid.UUID(rid)
    except ValueError:
        await _responder(chat_id, "Botão inválido 🤷")
        return {"ok": True, "erro": "callback"}

    async with get_session() as session:
        rascunho = await session.get(BotRascunho, rid_uuid)
        if rascunho is None or str(rascunho.usuario_id) != usuario_id:
            await _responder(chat_id, "Esse rascunho expirou 🤷")
            return {"ok": True, "rascunho": "expirado"}
        payload = dict(rascunho.payload)
        await session.delete(rascunho)   # consumido (confirmar/cancelar/editar)
        await session.commit()

    if acao == "cancelar":
        await _responder(chat_id, "❌ Cancelado.")
        return {"ok": True, "acao": "cancelar"}
    if acao == "editar":
        await _responder(chat_id, "✏️ Manda a frase corrigida que eu refaço.")
        return {"ok": True, "acao": "editar"}
    if acao == "confirmar":
        return await _confirmar(chat_id, usuario_id, payload)

    await _responder(chat_id, "Ação desconhecida 🤷")
    return {"ok": True, "acao": acao}

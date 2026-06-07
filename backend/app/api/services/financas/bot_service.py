"""Dispatch do bot do Telegram (Organizador Financeiro).

Handler manual: o webhook entrega o Update (dict), aqui a gente decide o que
fazer e responde via app.integrations.telegram. Auth por chat_id (só você e a
Sandra). As chamadas de saída ao Telegram (tg.*) são síncronas → asyncio.to_thread.
"""
from __future__ import annotations

import asyncio
from decimal import Decimal, InvalidOperation
from typing import Optional

from app.api.schemas.financas import DespesaCreate
from app.api.services.financas import conta_service, transacao_service
from app.config import settings
from app.integrations import telegram as tg
from app.utils.logger import get_logger

logger = get_logger()

AJUDA = (
    "Manda assim:\n"
    "• <code>/gasto 50 mercado</code> (lança rápido)\n"
    "• <code>/gasto 50 mercado vr</code> (escolhe a conta)\n"
    "• ou um boleto (PDF/foto) que eu importo."
)


def mapa_chat_usuario() -> dict[str, str]:
    """chat_id (str) → usuario_id (UUID str). Lido das settings."""
    mapa: dict[str, str] = {}
    if settings.telegram_chat_id and settings.telegram_usuario_id:
        mapa[str(settings.telegram_chat_id)] = settings.telegram_usuario_id
    if settings.telegram_chat_id_sandra and settings.telegram_usuario_id_sandra:
        mapa[str(settings.telegram_chat_id_sandra)] = settings.telegram_usuario_id_sandra
    return mapa


async def _responder(chat_id: str, texto: str, reply_markup: Optional[dict] = None) -> None:
    await asyncio.to_thread(tg.send_message, chat_id, texto, reply_markup)


async def processar_update(update: dict) -> dict:
    msg = update.get("message") or update.get("edited_message")
    if not msg:
        return {"ok": True, "ignorado": True}  # callback_query etc. (Fase 5+)

    chat_id = str(msg.get("chat", {}).get("id", ""))
    usuario_id = mapa_chat_usuario().get(chat_id)
    if usuario_id is None:
        await _responder(chat_id, "🚫 Bot privado. Você não está autorizado.")
        return {"ok": True, "autorizado": False}

    texto = (msg.get("text") or "").strip()

    if texto.startswith("/start"):
        await _responder(chat_id, "💰 Organizador financeiro no ar.\n\n" + AJUDA)
        return {"ok": True, "comando": "start"}

    if texto.startswith("/gasto"):
        return await _cmd_gasto(chat_id, usuario_id, texto)

    await _responder(chat_id, "Não entendi 🤔\n\n" + AJUDA)
    return {"ok": True, "comando": None}


async def _cmd_gasto(chat_id: str, usuario_id: str, texto: str) -> dict:
    partes = texto.split()
    if len(partes) < 3:
        await _responder(chat_id, "Uso: <code>/gasto &lt;valor&gt; &lt;descrição&gt; [conta]</code>")
        return {"ok": True, "comando": "gasto", "erro": "uso"}

    try:
        valor = Decimal(partes[1].replace(",", "."))
    except InvalidOperation:
        await _responder(chat_id, f"Valor inválido: {partes[1]!r}")
        return {"ok": True, "comando": "gasto", "erro": "valor"}
    if valor <= 0:
        await _responder(chat_id, "O valor precisa ser maior que zero.")
        return {"ok": True, "comando": "gasto", "erro": "valor"}

    resto = partes[2:]
    contas = (await conta_service.listar_contas(usuario_id, apenas_ativas=True)).items
    if not contas:
        await _responder(chat_id, "Você ainda não tem contas. Cadastre uma primeiro.")
        return {"ok": True, "comando": "gasto", "erro": "sem_conta"}

    # Último token pode ser o nome/tipo de uma conta.
    conta = None
    if len(resto) > 1:
        cand = resto[-1].lower()
        for c in contas:
            if cand == c.nome.lower() or cand == c.tipo.lower():
                conta = c
                resto = resto[:-1]
                break
    if conta is None:
        conta = contas[0]  # default: primeira conta ativa

    descricao = " ".join(resto) or "gasto"
    resp = await transacao_service.lancar_despesa(DespesaCreate(
        usuario_id=usuario_id, descricao=descricao,
        valor_total=valor, conta_id=conta.id,
    ))
    await _responder(
        chat_id,
        f"✅ R$ {valor} em <b>{descricao}</b> na conta <b>{conta.nome}</b>.",
    )
    return {"ok": True, "comando": "gasto", "transacao_id": resp.id, "conta": conta.nome}

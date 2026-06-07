"""Dispatch do bot do Telegram (Organizador Financeiro).

Handler manual: o webhook entrega o Update (dict), aqui a gente decide o que
fazer e responde via app.integrations.telegram. Auth por chat_id (só você e a
Sandra). As chamadas de saída ao Telegram (tg.*) são síncronas → asyncio.to_thread.
"""
from __future__ import annotations

import asyncio
import uuid
from decimal import Decimal, InvalidOperation
from datetime import date
from typing import Optional

from app.api.schemas.financas import DespesaCreate, ReceitaCreate
from app.api.services.financas import (
    conta_service,
    importador_service,
    nlu_service,
    transacao_service,
)
from app.api.services.financas.nlu_service import NLUError
from app.config import settings
from app.db.models.financas.bot_rascunho import BotRascunho
from app.db.session import get_session
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
    # Clique num botão do card de confirmação.
    if "callback_query" in update:
        return await _callback(update["callback_query"])

    msg = update.get("message") or update.get("edited_message")
    if not msg:
        return {"ok": True, "ignorado": True}

    chat_id = str(msg.get("chat", {}).get("id", ""))
    usuario_id = mapa_chat_usuario().get(chat_id)
    if usuario_id is None:
        await _responder(chat_id, "🚫 Bot privado. Você não está autorizado.")
        return {"ok": True, "autorizado": False}

    # Foto ou PDF → importador de boleto.
    if msg.get("photo") or msg.get("document"):
        return await _arquivo(chat_id, usuario_id, msg)

    texto = (msg.get("text") or "").strip()

    if texto.startswith("/start"):
        await _responder(chat_id, "💰 Organizador financeiro no ar.\n\n" + AJUDA)
        return {"ok": True, "comando": "start"}

    if texto.startswith("/gasto"):
        return await _cmd_gasto(chat_id, usuario_id, texto)

    if texto and not texto.startswith("/"):
        return await _texto_livre(chat_id, usuario_id, texto)

    await _responder(chat_id, "Não entendi 🤔\n\n" + AJUDA)
    return {"ok": True, "comando": None}


async def _arquivo(chat_id: str, usuario_id: str, msg: dict) -> dict:
    """Baixa o arquivo do Telegram e manda pro importador de boleto."""
    if msg.get("document"):
        doc = msg["document"]
        file_id = doc["file_id"]
        nome = doc.get("file_name") or "documento"
        mime = doc.get("mime_type") or "application/pdf"
    else:  # photo: lista de tamanhos, pega o maior
        foto = msg["photo"][-1]
        file_id = foto["file_id"]
        nome, mime = "foto.jpg", "image/jpeg"

    await _responder(chat_id, "📎 Recebi, lendo o boleto...")
    caminho = await asyncio.to_thread(tg.get_file_path, file_id)
    conteudo = await asyncio.to_thread(tg.download_file, caminho)

    resp = await importador_service.importar_boleto(
        usuario_id=usuario_id, conteudo=conteudo,
        nome_original=nome, content_type=mime,
    )
    prefixo = "✅" if resp.conferido else ("⚠️" if resp.success else "❌")
    await _responder(chat_id, f"{prefixo} {resp.mensagem}")
    return {"ok": True, "tipo": "arquivo", "conferido": resp.conferido,
            "transacao_id": resp.transacao_id}


def _card_keyboard(rid: str) -> dict:
    return {"inline_keyboard": [
        [{"text": "✅ Confirmar", "callback_data": f"confirmar:{rid}"},
         {"text": "❌ Cancelar", "callback_data": f"cancelar:{rid}"}],
        [{"text": "✏️ Editar", "callback_data": f"editar:{rid}"}],
    ]}


async def _texto_livre(chat_id: str, usuario_id: str, texto: str) -> dict:
    """Interpreta a frase (NLU) e manda um card de confirmação."""
    try:
        interp = await nlu_service.interpretar_texto(usuario_id, texto)
    except NLUError as e:
        await _responder(chat_id, f"🤔 {e}")
        return {"ok": True, "nlu": False}

    payload = {
        "tipo": interp.tipo,
        "valor": str(interp.valor),
        "descricao": interp.descricao,
        "data": interp.data.isoformat(),
        "conta_id": interp.conta_id,
        "conta_nome": interp.conta_nome,
        "categoria_id": interp.categoria_id,
        "categoria_nome": interp.categoria_nome,
    }
    async with get_session() as session:
        rascunho = BotRascunho(
            usuario_id=uuid.UUID(usuario_id), chat_id=chat_id, payload=payload
        )
        session.add(rascunho)
        await session.commit()
        await session.refresh(rascunho)
        rid = str(rascunho.id)

    emoji = "💸" if interp.tipo == "despesa" else "💰"
    linhas = [
        f"{emoji} <b>{interp.tipo}</b>: R$ {interp.valor}",
        f"📝 {interp.descricao}",
        f"📅 {interp.data.isoformat()}",
    ]
    if interp.conta_nome:
        linhas.append(f"🏦 {interp.conta_nome}")
    if interp.categoria_nome:
        linhas.append(f"🏷️ {interp.categoria_nome}")
    linhas.append("\nConfirma?")
    await _responder(chat_id, "\n".join(linhas), _card_keyboard(rid))
    return {"ok": True, "rascunho_id": rid}


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


async def _confirmar(chat_id: str, usuario_id: str, payload: dict) -> dict:
    valor = Decimal(payload["valor"])
    tipo = payload["tipo"]
    descricao = payload["descricao"]
    competencia = date.fromisoformat(payload["data"])
    conta_id = payload.get("conta_id")
    categoria_id = payload.get("categoria_id")

    if not conta_id:
        contas = (await conta_service.listar_contas(usuario_id, apenas_ativas=True)).items
        if not contas:
            await _responder(chat_id, "Você não tem contas. Cadastre uma primeiro.")
            return {"ok": True, "acao": "confirmar", "erro": "sem_conta"}
        conta_id = contas[0].id

    if tipo == "receita":
        resp = await transacao_service.lancar_receita(ReceitaCreate(
            usuario_id=usuario_id, descricao=descricao, valor_total=valor,
            conta_id=conta_id, categoria_id=categoria_id, data_competencia=competencia,
        ))
    else:
        resp = await transacao_service.lancar_despesa(DespesaCreate(
            usuario_id=usuario_id, descricao=descricao, valor_total=valor,
            conta_id=conta_id, categoria_id=categoria_id, data_competencia=competencia,
        ))
    await _responder(chat_id, f"✅ Lançado: <b>{descricao}</b> R$ {valor}.")
    return {"ok": True, "acao": "confirmar", "transacao_id": resp.id}


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

"""NLU do bot: interpreta texto livre, monta o card de confirmação e, no
callback, efetiva o lançamento (_confirmar)."""
from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from app.api.schemas.financas import DespesaCreate, ReceitaCreate
from app.api.services.financas import conta_service, nlu_service, transacao_service
from app.api.services.financas.nlu_service import NLUError
from app.db.models.financas.bot_rascunho import BotRascunho
from app.db.session import get_session

from ._base import _card_keyboard, _eh_prevista, _responder


async def _texto_livre(chat_id: str, usuario_id: str, texto: str) -> dict:
    """Interpreta a frase (NLU) e manda um card de confirmação."""
    try:
        interp = await nlu_service.interpretar_texto(usuario_id, texto)
    except NLUError as e:
        await _responder(chat_id, f"🤔 {e}")
        return {"ok": True, "nlu": False}

    prevista = interp.tipo == "despesa" and _eh_prevista(texto, interp.data)
    payload = {
        "tipo": interp.tipo,
        "valor": str(interp.valor),
        "descricao": interp.descricao,
        "data": interp.data.isoformat(),
        "conta_id": interp.conta_id,
        "conta_nome": interp.conta_nome,
        "categoria_id": interp.categoria_id,
        "categoria_nome": interp.categoria_nome,
        "prevista": prevista,
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
    if prevista:
        linhas.append("🗓️ <b>prevista</b> (agendada — não mexe no saldo ainda)")
    if interp.conta_nome:
        linhas.append(f"🏦 {interp.conta_nome}")
    if interp.categoria_nome:
        linhas.append(f"🏷️ {interp.categoria_nome}")
    linhas.append("\nConfirma?")
    await _responder(chat_id, "\n".join(linhas), _card_keyboard(rid))
    return {"ok": True, "rascunho_id": rid}


async def _confirmar(chat_id: str, usuario_id: str, payload: dict) -> dict:
    valor = Decimal(payload["valor"])
    tipo = payload["tipo"]
    descricao = payload["descricao"]
    competencia = date.fromisoformat(payload["data"])
    conta_id = payload.get("conta_id")
    categoria_id = payload.get("categoria_id")
    prevista = bool(payload.get("prevista"))

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
        await _responder(chat_id, f"✅ Lançado: <b>{descricao}</b> R$ {valor}.")
    else:
        resp = await transacao_service.lancar_despesa(DespesaCreate(
            usuario_id=usuario_id, descricao=descricao, valor_total=valor,
            conta_id=conta_id, categoria_id=categoria_id, data_competencia=competencia,
            data_vencimento=competencia if prevista else None,
            status="prevista" if prevista else "paga",
        ))
        if prevista:
            await _responder(
                chat_id,
                f"🗓️ Agendado: <b>{descricao}</b> R$ {valor} "
                f"(vence {competencia.isoformat()}). Aparece em 'A pagar'.",
            )
        else:
            await _responder(chat_id, f"✅ Lançado: <b>{descricao}</b> R$ {valor}.")
    return {"ok": True, "acao": "confirmar", "transacao_id": resp.id, "prevista": prevista}

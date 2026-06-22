"""Follow-up de propostas do agente Freela.

Roda 1x/dia (dentro da ``rotina_diaria``). Encontra propostas que foram
ENVIADAS há ≥ N dias e ainda não tiveram resposta, e manda um lembrete no
Telegram pra você dar um follow-up — SEMPRE dentro da plataforma (a Workana
penaliza contato fora). A ferramenta não envia nada pro cliente; só te cutuca.
"""
from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from sqlalchemy import select

from app.config import settings
from app.db.models.pessoal.freela.cliente import Cliente
from app.db.models.pessoal.freela.projeto import Projeto
from app.db.models.pessoal.freela.proposta import Proposta
from app.db.session import get_session
from app.integrations import telegram as tg
from app.utils.logger import get_logger

logger = get_logger()


async def lembrete_followup(ref: datetime | None = None) -> dict:
    if not settings.freela_followup_enabled:
        return {"enviados": 0, "motivo": "desligado"}
    chat_id = settings.telegram_chat_id
    if not chat_id or not settings.telegram_bot_token:
        return {"enviados": 0, "motivo": "sem telegram configurado"}

    agora = ref or datetime.now(UTC)
    dias = max(1, settings.freela_followup_dias)

    async with get_session() as session:
        stmt = (
            select(Proposta, Projeto.titulo, Cliente.nome)
            .join(Projeto, Projeto.id == Proposta.projeto_id)
            .outerjoin(Cliente, Cliente.id == Projeto.cliente_id)
            .where(
                Proposta.status == "enviada",
                Proposta.data_resposta.is_(None),
                Proposta.enviada_em.is_not(None),
            )
            .order_by(Proposta.enviada_em.asc())
        )
        linhas = (await session.execute(stmt)).all()

    pendentes = []
    for proposta, titulo, cliente_nome in linhas:
        enviada = proposta.enviada_em
        if enviada.tzinfo is None:
            enviada = enviada.replace(tzinfo=UTC)
        d = (agora - enviada).days
        if d >= dias:
            quem = f" — {cliente_nome}" if cliente_nome else ""
            pendentes.append(f"• {titulo}{quem} (enviada há {d}d)")

    if not pendentes:
        return {"enviados": 0, "pendentes": 0}

    texto = (
        f"📨 <b>Follow-up Freela</b> — {len(pendentes)} proposta(s) sem resposta "
        f"há {dias}+ dias.\nDê um toque <b>dentro da Workana</b> (não force "
        f"contato fora):\n\n" + "\n".join(pendentes)
    )
    try:
        await asyncio.to_thread(tg.send_message, chat_id, texto)
        return {"enviados": 1, "pendentes": len(pendentes)}
    except Exception as e:  # nunca derruba a rotina por causa de envio
        logger.warning("Falha ao enviar follow-up do freela: {}", e)
        return {"enviados": 0, "pendentes": len(pendentes), "erro": str(e)}

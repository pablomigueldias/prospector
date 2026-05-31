from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import select

from app.db.sync_bridge import bridge_session
from app.db.models.email_outreach import EmailOutreach
from app.mailer.client import (
    ler_enviados, ler_inbox, _extrair_emails, _normalizar_assunto,
)
from app.utils.logger import get_logger

logger = get_logger()


async def _reconciliar_enviados(session, dias: int) -> int:
    
    enviados = ler_enviados(dias=dias)
    if not enviados:
        logger.info("Nenhum e-mail na pasta Enviados (ou nada enviado ainda).")
        return 0

    # Pega registros que ainda não foram confirmados como enviados
    stmt = select(EmailOutreach).where(
        EmailOutreach.status.in_(["rascunho", "enviado"])
    )
    registros = (await session.execute(stmt)).scalars().all()

    atualizados = 0
    for reg in registros:
        if reg.sent_message_id:
            continue  # já reconciliado
        alvo_dest = (reg.destinatario or "").lower()
        alvo_assunto = _normalizar_assunto(reg.assunto or "")

        for env in enviados:
            destinos = _extrair_emails(env["to"])
            if alvo_dest in destinos and env["subject_norm"] == alvo_assunto:
                reg.status = "enviado"
                reg.sent_message_id = env["message_id"]
                reg.enviado_em = env["date"] or datetime.now()
                atualizados += 1
                logger.info(f"   ✉️  Enviado confirmado: {alvo_dest}")
                break

    if atualizados:
        await session.commit()
    return atualizados


async def _detectar_respostas(session, dias: int) -> int:
    inbox = ler_inbox(dias=dias)
    if not inbox:
        return 0

    stmt = select(EmailOutreach).where(
        EmailOutreach.status == "enviado",
        EmailOutreach.sent_message_id.is_not(None),
    )
    enviados = (await session.execute(stmt)).scalars().all()

    detectadas = 0
    for reg in enviados:
        sent_id = reg.sent_message_id
        remetente_alvo = (reg.destinatario or "").lower()

        for msg in inbox:
            # Plano A: threading por In-Reply-To / References
            casou_thread = (
                sent_id and (
                    sent_id in msg["in_reply_to"]
                    or sent_id in msg["references"]
                )
            )
            # Plano B: veio de quem contatamos, depois do envio
            de = _extrair_emails(msg["from"])
            casou_remetente = (
                remetente_alvo in de
                and msg["date"]
                and reg.enviado_em
                and msg["date"] >= reg.enviado_em
            )

            if casou_thread or casou_remetente:
                reg.status = "respondido"
                reg.primeira_resposta_em = msg["date"] or datetime.now()
                reg.resposta_trecho = (msg["subject"] or "")[:500]
                reg.resposta_corpo = msg.get("corpo") or None
                detectadas += 1
                via = "thread" if casou_thread else "remetente"
                logger.success(f"   💬 RESPOSTA de {remetente_alvo} (via {via})")
                break

    if detectadas:
        await session.commit()
    return detectadas


async def _sincronizar_async(dias: int = 30) -> dict:
    async with bridge_session() as session:
        enviados = await _reconciliar_enviados(session, dias)
        respostas = await _detectar_respostas(session, dias)
    return {"enviados_confirmados": enviados, "respostas_detectadas": respostas}


def sincronizar(dias: int = 30) -> dict:
    """Ponto de entrada síncrono (pro CLI/router)."""
    import asyncio
    return asyncio.run(_sincronizar_async(dias=dias))
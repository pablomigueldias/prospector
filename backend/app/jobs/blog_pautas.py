"""Cron do agente Blog (P5 §6.B4): mantém o backlog de pautas cheio.

Roda 1x/semana. Se o backlog de pautas "ideia" estiver abaixo do mínimo, pede
pro motor gerar mais e (se houver Telegram) avisa o Pablo pra revisar. NÃO
publica nada — só alimenta o backlog; escrever/publicar segue com checkpoint
humano.
"""
from __future__ import annotations

import asyncio

from app.api.schemas.blog import BlogPautaGerarRequest
from app.api.services import blog_service
from app.config import settings
from app.db.session import get_session
from app.integrations import telegram as tg
from app.repositories.blog_repository import BlogRepository
from app.utils.logger import get_logger

logger = get_logger()


async def rotina_pautas() -> dict:
    if not settings.blog_pautas_cron_enabled:
        return {"geradas": 0, "motivo": "desligado"}

    async with get_session() as session:
        backlog = await BlogRepository(session).listar_pautas(status="ideia")
    if len(backlog) >= settings.blog_pautas_min_backlog:
        return {"geradas": 0, "motivo": "backlog cheio", "atual": len(backlog)}

    try:
        novas = await blog_service.pauta.gerar(
            BlogPautaGerarRequest(quantidade=settings.blog_pautas_gerar)
        )
    except Exception as e:  # noqa: BLE001 — cron nunca derruba o processo
        logger.warning("blog_pautas: falha ao gerar (%s)", e)
        return {"geradas": 0, "motivo": f"erro: {e}"}

    logger.info("blog_pautas: %d pautas novas no backlog", len(novas))

    if settings.telegram_chat_id and settings.telegram_bot_token and novas:
        linhas = "\n".join(f"• {p.titulo}" for p in novas[:5])
        try:
            await asyncio.to_thread(
                tg.send_message,
                settings.telegram_chat_id,
                f"📝 Blog: gerei {len(novas)} pautas novas pra revisar:\n{linhas}",
            )
        except Exception as e:  # noqa: BLE001
            logger.warning("blog_pautas: falha no aviso Telegram (%s)", e)

    return {"geradas": len(novas)}

"""Cron do agente LinkedIn (P5 §6.C — L4): mantém a FILA de rascunhos cheia.

Roda 1x/semana. Se a fila de rascunhos da conta-alvo estiver abaixo do mínimo,
o coordenador gera mais (tendências/projetos) e os AGENDA no calendário editorial
(slots espaçados). NÃO publica nada no LinkedIn — só prepara rascunhos pro Pablo
revisar e postar. Espelha `blog_pautas.py`.
"""
from __future__ import annotations

import asyncio
from datetime import UTC, datetime, time, timedelta

from app.api.schemas.linkedin import LinkedinGerarRequest, LinkedinPostUpdate
from app.api.services import linkedin_service
from app.config import settings
from app.db.session import get_session
from app.integrations import telegram as tg
from app.repositories.linkedin_repository import LinkedinRepository
from app.utils.logger import get_logger

logger = get_logger()


async def _agendar(conta: str, posts: list) -> None:
    """Distribui os novos rascunhos no calendário: a partir do último slot já
    agendado (ou de amanhã), um a cada `linkedin_intervalo_dias`, na hora do cron."""
    async with get_session() as session:
        ultimo = await LinkedinRepository(session).ultimo_agendado(conta=conta)

    agora = datetime.now(UTC)
    base = ultimo if (ultimo and ultimo > agora) else agora
    intervalo = max(1, settings.linkedin_intervalo_dias)
    hora = time(hour=settings.linkedin_hora, tzinfo=UTC)

    for i, p in enumerate(posts, start=1):
        dia = (base + timedelta(days=intervalo * i)).date()
        quando = datetime.combine(dia, hora)
        await linkedin_service.admin.atualizar(
            p.id, LinkedinPostUpdate(scheduled_for=quando)
        )


async def rotina_fila() -> dict:
    if not settings.linkedin_cron_enabled:
        return {"gerados": 0, "motivo": "desligado"}

    conta = settings.linkedin_conta
    async with get_session() as session:
        na_fila = await LinkedinRepository(session).contar(
            status="rascunho", conta=conta
        )
    if na_fila >= settings.linkedin_min_fila:
        return {"gerados": 0, "motivo": "fila cheia", "atual": na_fila}

    try:
        novos = await linkedin_service.coordenador.gerar(
            LinkedinGerarRequest(
                fonte=settings.linkedin_fonte,
                quantidade=settings.linkedin_gerar,
                conta=conta,
            )
        )
    except Exception as e:  # noqa: BLE001 — cron nunca derruba o processo
        logger.warning("linkedin_posts: falha ao gerar ({})", e)
        return {"gerados": 0, "motivo": f"erro: {e}"}

    if novos:
        try:
            await _agendar(conta, novos)
        except Exception as e:  # noqa: BLE001
            logger.warning("linkedin_posts: falha ao agendar ({})", e)

    logger.info("linkedin_posts: {} rascunho(s) novo(s) na fila ({})", len(novos), conta)

    if settings.telegram_chat_id and settings.telegram_bot_token and novos:
        linhas = "\n".join(f"• {p.titulo or p.hook}" for p in novos[:5])
        try:
            await asyncio.to_thread(
                tg.send_message,
                settings.telegram_chat_id,
                f"💼 LinkedIn ({conta}): gerei {len(novos)} rascunho(s) pra revisar:\n{linhas}",
            )
        except Exception as e:  # noqa: BLE001
            logger.warning("linkedin_posts: falha no aviso Telegram ({})", e)

    return {"gerados": len(novos), "conta": conta}

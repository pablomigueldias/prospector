"""Job do briefing noturno (MAS-4).

Roda 1x/dia pelo agendador: monta o 'Resumo da Noite' (orchestrator.briefing) e
te manda no Telegram + registra na memória compartilhada (alvo `briefing`). Nada
sai pra fora além do aviso pra você — é preparo, não ação.
"""
from __future__ import annotations

from datetime import date

from app.api.services import memoria_service
from app.config import settings
from app.integrations import telegram as tg
from app.orchestrator import briefing as briefing_chain
from app.utils.logger import get_logger

logger = get_logger()


async def rotina_briefing() -> dict:
    if not settings.briefing_enabled:
        return {"enviado": False, "motivo": "desligado"}
    b = await briefing_chain.gerar()

    # Memória: guarda o briefing do dia (alvo = briefing/<data>).
    await memoria_service.registrar(
        agente="coordenador", alvo_tipo="briefing", alvo_id=b.data,
        tipo="briefing",
        resumo=(
            f"{b.vagas_triar.total} vaga(s) a triar · "
            f"{b.freela_followups.total} follow-up(s) · "
            f"{b.atividades_atrasadas} atrasada(s)"
        ),
        payload=b.model_dump(), origem="cron",
    )

    chat_id = settings.telegram_chat_id
    if chat_id and settings.telegram_bot_token:
        try:
            tg.send_message(chat_id, b.texto)
            return {"enviado": True, "data": b.data}
        except Exception as e:  # noqa: BLE001
            logger.warning("briefing: falha ao enviar Telegram: {}", e)
    return {"enviado": False, "data": b.data, "motivo": "sem telegram"}


if __name__ == "__main__":
    import asyncio
    print(asyncio.run(rotina_briefing()))
    print("briefing rodado em", date.today().isoformat())

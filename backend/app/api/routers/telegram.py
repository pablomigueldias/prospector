from fastapi import APIRouter, HTTPException, Request

from app.api.services.financas import bot_service
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger()

# Sem /api: o Caddy roteia /telegram/* direto pra API (caminho preservado).
router = APIRouter(prefix="/telegram", tags=["telegram"])


@router.post("/webhook", summary="Webhook do bot do Telegram")
async def webhook(request: Request) -> dict:
    # Telegram manda o secret no header; valida se configurado.
    if settings.telegram_webhook_secret:
        recebido = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
        if recebido != settings.telegram_webhook_secret:
            raise HTTPException(status_code=403, detail="secret inválido")

    update = await request.json()
    try:
        await bot_service.processar_update(update)
    except Exception as e:
        # Nunca devolve erro pro Telegram (senão ele reenvia em loop); loga.
        logger.exception("Erro processando update do Telegram: %s", e)
    return {"ok": True}

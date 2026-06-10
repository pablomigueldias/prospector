from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.dependencies.financas import financas_usuario_id
from app.api.services.financas import eventos

router = APIRouter(prefix="/api/financas/eventos", tags=["financas:eventos"])


@router.get("", summary="Stream SSE de eventos do financas (tempo real)")
async def stream(
    usuario_id: str = Depends(financas_usuario_id),
) -> StreamingResponse:
    return StreamingResponse(
        eventos.stream_eventos(usuario_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # desliga buffering em proxies
        },
    )

from fastapi import APIRouter, HTTPException

from app.api.schemas.outreach import (
    EmailHistoryResponse,
    GerarRascunhosRequest,
    GerarRascunhosResponse,
    GerarFollowupsRequest,
    GerarFollowupsResponse,
    SyncResponse,
)
from app.api.services import outreach_service

router = APIRouter(prefix="/api/agents/outreach", tags=["outreach"])


@router.post("/gerar", response_model=GerarRascunhosResponse,
             summary="Gera rascunhos pros contatos pendentes")
async def gerar(body: GerarRascunhosRequest) -> GerarRascunhosResponse:
    try:
        r = await outreach_service.gerar(limit=body.limit, pausa=body.pausa)
        return GerarRascunhosResponse(**r)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")

@router.post("/followups", response_model=GerarFollowupsResponse,
             summary="Gera rascunhos de follow-up pros e-mails sem resposta")
async def followups(body: GerarFollowupsRequest) -> GerarFollowupsResponse:
    try:
        r = await outreach_service.gerar_followups(
            dias=body.dias,
            max_followups=body.max_followups,
            limit=body.limit,
            pausa=body.pausa,
        )
        return GerarFollowupsResponse(**r)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")


@router.post("/sync", response_model=SyncResponse,
             summary="Confirma enviados e detecta respostas")
async def sync() -> SyncResponse:
    try:
        r = await outreach_service.sincronizar_async()
        return SyncResponse(**r)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")


@router.get("/emails", response_model=EmailHistoryResponse,
            summary="Histórico de e-mails")
async def emails(limit: int = 50) -> EmailHistoryResponse:
    try:
        items = await outreach_service.historico(limit=limit)
        return EmailHistoryResponse(items=items, total=len(items)) #type: ignore
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")

from fastapi import APIRouter, HTTPException

from app.api.schemas.observability import ObsResumo

router = APIRouter(prefix="/api/observability", tags=["observability"])


@router.get("/stats", summary="Resumo de uso de IA e eventos do pipeline")
def observability_stats() -> dict:
    from app.db.observability import stats_sync
    try:
        return {"success": True, **stats_sync()}
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Postgres indisponível: {type(e).__name__}: {e}",
        )


@router.get("/resumo", response_model=ObsResumo,
            summary="Custos/tokens de IA por agente e por dia (S2)")
async def observability_resumo(dias: int = 30) -> ObsResumo:
    from app.api.services import observability_service
    try:
        return await observability_service.resumo(dias)
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Postgres indisponível: {type(e).__name__}: {e}",
        ) from e

from fastapi import APIRouter, HTTPException

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
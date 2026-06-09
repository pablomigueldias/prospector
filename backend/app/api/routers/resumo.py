from fastapi import APIRouter, HTTPException

from app.api.schemas.financas import ResumoMesResponse
from app.api.services.financas import resumo_service
from app.api.services.financas.resumo_service import ResumoError

router = APIRouter(prefix="/api/financas/resumo", tags=["financas:resumo"])


def _handle(e: Exception) -> HTTPException:
    if isinstance(e, ResumoError):
        return HTTPException(status_code=400, detail=str(e))
    return HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")


@router.get("", response_model=ResumoMesResponse,
            summary="Resumo do mês: receita x despesa e quebra por categoria")
async def resumo(usuario_id: str, ano: int, mes: int) -> ResumoMesResponse:
    try:
        return await resumo_service.resumo_mes(usuario_id, ano, mes)
    except Exception as e:
        raise _handle(e)

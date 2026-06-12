from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies.financas import financas_usuario_id
from app.api.schemas.financas import RelatorioResponse, ResumoMesResponse
from app.api.services.financas import resumo_service
from app.api.services.financas.resumo_service import ResumoError

router = APIRouter(prefix="/api/financas/resumo", tags=["financas:resumo"])


def _handle(e: Exception) -> HTTPException:
    if isinstance(e, ResumoError):
        return HTTPException(status_code=400, detail=str(e))
    return HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")


@router.get("", response_model=ResumoMesResponse,
            summary="Resumo do mês: receita x despesa e quebra por categoria")
async def resumo(
    ano: int, mes: int, usuario_id: str = Depends(financas_usuario_id),
) -> ResumoMesResponse:
    try:
        return await resumo_service.resumo_mes(usuario_id, ano, mes)
    except Exception as e:
        raise _handle(e)


@router.get("/relatorio", response_model=RelatorioResponse,
            summary="Relatório do período: série mês a mês + top categorias")
async def relatorio(
    ano: int,
    mes: int,
    meses: int = Query(6, ge=1, le=24, description="Quantos meses até o âncora"),
    usuario_id: str = Depends(financas_usuario_id),
) -> RelatorioResponse:
    try:
        return await resumo_service.relatorio(usuario_id, ano, mes, meses)
    except Exception as e:
        raise _handle(e)

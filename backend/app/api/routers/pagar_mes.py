
from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies.financas import exige_editar, financas_usuario_id
from app.api.schemas.financas import (
    PagamentoMesPreview,
    PagamentoMesRequest,
    PagamentoMesResultado,
)
from app.api.services.financas import pagamento_mes_service
from app.api.services.financas.pagamento_mes_service import PagamentoMesError

router = APIRouter(prefix="/api/financas/pagar-mes", tags=["financas:pagar-mes"])


def _handle(e: Exception) -> HTTPException:
    if isinstance(e, PagamentoMesError):
        return HTTPException(status_code=400, detail=str(e))
    return HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")


@router.get("/preview", response_model=PagamentoMesPreview,
            summary="Pendências do mês: boletos a pagar + faturas em aberto")
async def preview(
    competencia: str | None = None,
    usuario_id: str = Depends(financas_usuario_id),
) -> PagamentoMesPreview:
    try:
        return await pagamento_mes_service.preview_mes(usuario_id, competencia)
    except Exception as e:
        raise _handle(e)


@router.post("", response_model=PagamentoMesResultado,
             summary="Paga os itens selecionados do mês (boletos + faturas)",
             dependencies=[Depends(exige_editar)])
async def pagar(
    body: PagamentoMesRequest,
    usuario_id: str = Depends(financas_usuario_id),
) -> PagamentoMesResultado:
    try:
        return await pagamento_mes_service.pagar_mes(usuario_id, body)
    except Exception as e:
        raise _handle(e)

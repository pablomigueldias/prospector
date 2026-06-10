from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies.financas import exige_editar, financas_usuario_id
from app.api.schemas.financas import InterpretacaoResponse, InterpretarTextoRequest
from app.api.services.financas import nlu_service
from app.api.services.financas.nlu_service import NLUError

router = APIRouter(prefix="/api/financas/nlu", tags=["financas:nlu"])


@router.post("/interpretar", response_model=InterpretacaoResponse,
             summary="Interpreta texto livre → rascunho de transação (não grava)",
             dependencies=[Depends(exige_editar)])
async def interpretar(
    body: InterpretarTextoRequest,
    usuario_id: str = Depends(financas_usuario_id),
) -> InterpretacaoResponse:
    try:
        return await nlu_service.interpretar_texto(usuario_id, body.texto)
    except NLUError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")

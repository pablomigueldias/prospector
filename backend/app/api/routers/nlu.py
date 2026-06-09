from fastapi import APIRouter, HTTPException

from app.api.schemas.financas import InterpretacaoResponse, InterpretarTextoRequest
from app.api.services.financas import nlu_service
from app.api.services.financas.nlu_service import NLUError

router = APIRouter(prefix="/api/financas/nlu", tags=["financas:nlu"])


@router.post("/interpretar", response_model=InterpretacaoResponse,
             summary="Interpreta texto livre → rascunho de transação (não grava)")
async def interpretar(body: InterpretarTextoRequest) -> InterpretacaoResponse:
    try:
        return await nlu_service.interpretar_texto(body.usuario_id, body.texto)
    except NLUError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")

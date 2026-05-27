from fastapi import APIRouter, HTTPException
from app.api.schemas.copywriter import CopywriterRequest, CopywriterResponse
from app.api.services.copywriter_service import gerar_email, CopywriterError

router = APIRouter(prefix="/api/agents/copywriter", tags=["copywriter"])


@router.post("/gerar", response_model=CopywriterResponse,
             summary="Gera e-mail de prospecção personalizado")
def copywriter_gerar(body: CopywriterRequest) -> CopywriterResponse:
    try:
        return gerar_email(body)
    except CopywriterError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro inesperado: {type(e).__name__}: {e}",
        )
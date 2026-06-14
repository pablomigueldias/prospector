from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies.financas import usuario_financas
from app.api.schemas.financas import PixParseRequest, PixParseResponse
from app.api.services.financas import pix_service
from app.api.services.financas.pix_service import PixError

router = APIRouter(prefix="/api/financas/pix", tags=["financas:pix"])


@router.post("/parse", response_model=PixParseResponse,
             summary="Lê um PIX copia-e-cola e extrai valor/beneficiário",
             dependencies=[Depends(usuario_financas)])
async def parse(body: PixParseRequest) -> PixParseResponse:
    try:
        return pix_service.parse_copia_cola(body.codigo)
    except PixError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")

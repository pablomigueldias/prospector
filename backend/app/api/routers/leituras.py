from typing import Optional

from fastapi import APIRouter, HTTPException

from app.api.schemas.financas import (
    LeituraConsumoCreate,
    LeituraConsumoListResponse,
    LeituraConsumoResponse,
)
from app.api.services.financas import leitura_service
from app.api.services.financas.leitura_service import LeituraError

router = APIRouter(prefix="/api/financas/leituras", tags=["financas:leituras"])


def _handle(e: Exception) -> HTTPException:
    if isinstance(e, LeituraError):
        return HTTPException(status_code=400, detail=str(e))
    return HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")


@router.get("", response_model=LeituraConsumoListResponse,
            summary="Lista leituras de consumo (tendência), opcional por tipo")
async def listar(usuario_id: str, tipo: Optional[str] = None) -> LeituraConsumoListResponse:
    try:
        return await leitura_service.listar_leituras(usuario_id, tipo=tipo)
    except Exception as e:
        raise _handle(e)


@router.post("", response_model=LeituraConsumoResponse, status_code=201,
             summary="Registra uma leitura de consumo")
async def criar(body: LeituraConsumoCreate) -> LeituraConsumoResponse:
    try:
        return await leitura_service.criar_leitura(body)
    except Exception as e:
        raise _handle(e)

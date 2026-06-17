
from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies.financas import exige_editar, financas_usuario_id
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
async def listar(
    tipo: str | None = None,
    usuario_id: str = Depends(financas_usuario_id),
) -> LeituraConsumoListResponse:
    try:
        return await leitura_service.listar_leituras(usuario_id, tipo=tipo)
    except Exception as e:
        raise _handle(e)


@router.post("", response_model=LeituraConsumoResponse, status_code=201,
             summary="Registra uma leitura de consumo",
             dependencies=[Depends(exige_editar)])
async def criar(
    body: LeituraConsumoCreate,
    usuario_id: str = Depends(financas_usuario_id),
) -> LeituraConsumoResponse:
    body.usuario_id = usuario_id  # dono = sessão
    try:
        return await leitura_service.criar_leitura(body)
    except Exception as e:
        raise _handle(e)

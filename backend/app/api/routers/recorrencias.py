from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException

from app.api.schemas.financas import (
    ProcessarRecorrenciasResponse,
    RecorrenciaCreate,
    RecorrenciaListResponse,
    RecorrenciaResponse,
)
from app.api.services.financas import recorrencia_service
from app.api.services.financas.recorrencia_service import RecorrenciaError
from app.jobs.recorrencias import processar_recorrencias

router = APIRouter(prefix="/api/financas/recorrencias", tags=["financas:recorrencias"])


def _handle(e: Exception) -> HTTPException:
    if isinstance(e, RecorrenciaError):
        msg = str(e)
        status = 404 if "não encontrad" in msg.lower() else 400
        return HTTPException(status_code=status, detail=msg)
    return HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")


@router.get("", response_model=RecorrenciaListResponse,
            summary="Lista as recorrências de um usuário")
async def listar(usuario_id: str) -> RecorrenciaListResponse:
    try:
        return await recorrencia_service.listar_recorrencias(usuario_id)
    except Exception as e:
        raise _handle(e)


@router.post("", response_model=RecorrenciaResponse, status_code=201,
             summary="Cadastra uma despesa/receita fixa")
async def criar(body: RecorrenciaCreate) -> RecorrenciaResponse:
    try:
        return await recorrencia_service.criar_recorrencia(body)
    except Exception as e:
        raise _handle(e)


@router.post("/processar", response_model=ProcessarRecorrenciasResponse,
             summary="Gera as previstas do mês e marca atrasadas (job diário)")
async def processar(
    usuario_id: Optional[str] = None, ref: Optional[date] = None
) -> ProcessarRecorrenciasResponse:
    import uuid

    uid = None
    if usuario_id:
        try:
            uid = uuid.UUID(usuario_id)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"usuario_id inválido: {usuario_id!r}")
    try:
        resultado = await processar_recorrencias(usuario_id=uid, ref=ref)
        return ProcessarRecorrenciasResponse(**resultado)
    except Exception as e:
        raise _handle(e)

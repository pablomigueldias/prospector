from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies.financas import exige_editar, financas_usuario_id
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
            summary="Lista as recorrências do usuário logado")
async def listar(
    usuario_id: str = Depends(financas_usuario_id),
) -> RecorrenciaListResponse:
    try:
        return await recorrencia_service.listar_recorrencias(usuario_id)
    except Exception as e:
        raise _handle(e)


@router.post("", response_model=RecorrenciaResponse, status_code=201,
             summary="Cadastra uma despesa/receita fixa",
             dependencies=[Depends(exige_editar)])
async def criar(
    body: RecorrenciaCreate,
    usuario_id: str = Depends(financas_usuario_id),
) -> RecorrenciaResponse:
    body.usuario_id = usuario_id  # dono = sessão
    try:
        return await recorrencia_service.criar_recorrencia(body)
    except Exception as e:
        raise _handle(e)


# NB: endpoint de JOB (cron/manutenção), não de usuário: com usuario_id=None
# processa TODOS os perfis. Por isso NÃO deriva da sessão (senão o cron diário
# não conseguiria varrer todo mundo). Tratar o endurecimento dele à parte.
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

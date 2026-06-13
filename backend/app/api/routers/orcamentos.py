from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies.financas import exige_editar, financas_usuario_id
from app.api.schemas.financas import (
    OrcamentoCreate,
    OrcamentoListResponse,
    OrcamentoResponse,
    OrcamentoStatusResponse,
    OrcamentoUpdate,
)
from app.api.services.financas import orcamento_service
from app.api.services.financas.orcamento_service import OrcamentoError

router = APIRouter(prefix="/api/financas/orcamentos", tags=["financas:orcamentos"])


def _handle(e: Exception) -> HTTPException:
    if isinstance(e, OrcamentoError):
        msg = str(e)
        status = 404 if "não encontrad" in msg.lower() else 400
        return HTTPException(status_code=status, detail=msg)
    return HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")


@router.get("", response_model=OrcamentoListResponse,
            summary="Lista os orçamentos do usuário logado")
async def listar(
    usuario_id: str = Depends(financas_usuario_id),
) -> OrcamentoListResponse:
    try:
        return await orcamento_service.listar_orcamentos(usuario_id)
    except Exception as e:
        raise _handle(e)


@router.get("/status", response_model=OrcamentoStatusResponse,
            summary="Consumido × orçado por categoria no mês")
async def status(
    competencia: Optional[str] = None,
    usuario_id: str = Depends(financas_usuario_id),
) -> OrcamentoStatusResponse:
    try:
        return await orcamento_service.status_do_mes(usuario_id, competencia)
    except Exception as e:
        raise _handle(e)


@router.post("", response_model=OrcamentoResponse, status_code=201,
             summary="Define um teto mensal pra uma categoria",
             dependencies=[Depends(exige_editar)])
async def criar(
    body: OrcamentoCreate,
    usuario_id: str = Depends(financas_usuario_id),
) -> OrcamentoResponse:
    body.usuario_id = usuario_id  # dono = sessão
    try:
        return await orcamento_service.criar_orcamento(body)
    except Exception as e:
        raise _handle(e)


@router.patch("/{orcamento_id}", response_model=OrcamentoResponse,
              summary="Edita o teto / ativa-desativa",
              dependencies=[Depends(exige_editar)])
async def atualizar(orcamento_id: str, body: OrcamentoUpdate) -> OrcamentoResponse:
    try:
        return await orcamento_service.atualizar_orcamento(orcamento_id, body)
    except Exception as e:
        raise _handle(e)


@router.delete("/{orcamento_id}", status_code=204,
               summary="Remove o orçamento",
               dependencies=[Depends(exige_editar)])
async def remover(orcamento_id: str) -> None:
    try:
        await orcamento_service.excluir_orcamento(orcamento_id)
    except Exception as e:
        raise _handle(e)

from fastapi import APIRouter, HTTPException

from app.api.schemas.financas import (
    ContaCreate,
    ContaListResponse,
    ContaResponse,
    ContaUpdate,
)
from app.api.services.financas import conta_service
from app.api.services.financas.conta_service import ContaError

router = APIRouter(prefix="/api/financas/contas", tags=["financas:contas"])


def _handle(e: Exception) -> HTTPException:
    if isinstance(e, ContaError):
        msg = str(e)
        status = 404 if "não encontrada" in msg.lower() else 400
        return HTTPException(status_code=status, detail=msg)
    return HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")


@router.get("", response_model=ContaListResponse,
            summary="Lista as contas de um usuário")
async def listar(usuario_id: str, apenas_ativas: bool = False) -> ContaListResponse:
    try:
        return await conta_service.listar_contas(
            usuario_id, apenas_ativas=apenas_ativas
        )
    except Exception as e:
        raise _handle(e)


@router.post("", response_model=ContaResponse, status_code=201,
             summary="Cria uma conta")
async def criar(body: ContaCreate) -> ContaResponse:
    try:
        return await conta_service.criar_conta(body)
    except Exception as e:
        raise _handle(e)


@router.get("/{conta_id}", response_model=ContaResponse, summary="Detalhe da conta")
async def detalhe(conta_id: str) -> ContaResponse:
    try:
        return await conta_service.get_conta(conta_id)
    except Exception as e:
        raise _handle(e)


@router.patch("/{conta_id}", response_model=ContaResponse,
              summary="Atualiza nome/tipo/ativa da conta")
async def atualizar(conta_id: str, body: ContaUpdate) -> ContaResponse:
    try:
        return await conta_service.atualizar_conta(conta_id, body)
    except Exception as e:
        raise _handle(e)


@router.delete("/{conta_id}", status_code=204, summary="Remove a conta")
async def remover(conta_id: str) -> None:
    try:
        await conta_service.deletar_conta(conta_id)
    except Exception as e:
        raise _handle(e)

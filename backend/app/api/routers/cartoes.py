from fastapi import APIRouter, HTTPException

from app.api.schemas.financas import (
    CartaoCreate,
    CartaoListResponse,
    CartaoResponse,
    FaturasCartaoResponse,
)
from app.api.services.financas import cartao_service
from app.api.services.financas.cartao_service import CartaoError

router = APIRouter(prefix="/api/financas/cartoes", tags=["financas:cartoes"])


def _handle(e: Exception) -> HTTPException:
    if isinstance(e, CartaoError):
        msg = str(e)
        status = 404 if "não encontrado" in msg.lower() else 400
        return HTTPException(status_code=status, detail=msg)
    return HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")


@router.get("", response_model=CartaoListResponse,
            summary="Lista os cartões de um usuário")
async def listar(usuario_id: str) -> CartaoListResponse:
    try:
        return await cartao_service.listar_cartoes(usuario_id)
    except Exception as e:
        raise _handle(e)


@router.post("", response_model=CartaoResponse, status_code=201,
             summary="Cadastra um cartão de crédito")
async def criar(body: CartaoCreate) -> CartaoResponse:
    try:
        return await cartao_service.criar_cartao(body)
    except Exception as e:
        raise _handle(e)


@router.get("/{cartao_id}/faturas", response_model=FaturasCartaoResponse,
            summary="Faturas do cartão + total em aberto e total de juros")
async def faturas(cartao_id: str) -> FaturasCartaoResponse:
    try:
        return await cartao_service.faturas_do_cartao(cartao_id)
    except Exception as e:
        raise _handle(e)


@router.get("/{cartao_id}", response_model=CartaoResponse, summary="Detalhe do cartão")
async def detalhe(cartao_id: str) -> CartaoResponse:
    try:
        return await cartao_service.get_cartao(cartao_id)
    except Exception as e:
        raise _handle(e)

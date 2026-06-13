from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies.financas import (
    exige_editar,
    financas_usuario_id,
    usuario_financas,
)
from app.api.schemas.financas import (
    CartaoCreate,
    CartaoListResponse,
    CartaoResponse,
    CartaoUpdate,
    FaturaExtratoResponse,
    FaturasCartaoResponse,
)
from app.api.services.financas import cartao_service
from app.api.services.financas.cartao_service import CartaoError

router = APIRouter(prefix="/api/financas/cartoes", tags=["financas:cartoes"])


def _handle(e: Exception) -> HTTPException:
    if isinstance(e, CartaoError):
        msg = str(e)
        status = 404 if "não encontrad" in msg.lower() else 400
        return HTTPException(status_code=status, detail=msg)
    return HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")


@router.get("", response_model=CartaoListResponse,
            summary="Lista os cartões do usuário logado")
async def listar(
    usuario_id: str = Depends(financas_usuario_id),
) -> CartaoListResponse:
    try:
        return await cartao_service.listar_cartoes(usuario_id)
    except Exception as e:
        raise _handle(e)


@router.post("", response_model=CartaoResponse, status_code=201,
             summary="Cadastra um cartão de crédito",
             dependencies=[Depends(exige_editar)])
async def criar(
    body: CartaoCreate,
    usuario_id: str = Depends(financas_usuario_id),
) -> CartaoResponse:
    body.usuario_id = usuario_id  # dono = sessão
    try:
        return await cartao_service.criar_cartao(body)
    except Exception as e:
        raise _handle(e)


@router.get("/{cartao_id}/faturas", response_model=FaturasCartaoResponse,
            summary="Faturas do cartão + total em aberto e total de juros",
            dependencies=[Depends(usuario_financas)])
async def faturas(cartao_id: str) -> FaturasCartaoResponse:
    try:
        return await cartao_service.faturas_do_cartao(cartao_id)
    except Exception as e:
        raise _handle(e)


@router.get("/{cartao_id}/faturas/{fatura_id}", response_model=FaturaExtratoResponse,
            summary="Extrato da fatura: parcelas/compras que a compõem",
            dependencies=[Depends(usuario_financas)])
async def extrato_fatura(cartao_id: str, fatura_id: str) -> FaturaExtratoResponse:
    try:
        return await cartao_service.extrato_fatura(fatura_id)
    except Exception as e:
        raise _handle(e)


@router.get("/{cartao_id}", response_model=CartaoResponse, summary="Detalhe do cartão",
            dependencies=[Depends(usuario_financas)])
async def detalhe(cartao_id: str) -> CartaoResponse:
    try:
        return await cartao_service.get_cartao(cartao_id)
    except Exception as e:
        raise _handle(e)


@router.patch("/{cartao_id}", response_model=CartaoResponse,
              summary="Edita o cartão (nome, bandeira, dias, limite, ativo)",
              dependencies=[Depends(exige_editar)])
async def atualizar(cartao_id: str, body: CartaoUpdate) -> CartaoResponse:
    try:
        return await cartao_service.atualizar_cartao(cartao_id, body)
    except Exception as e:
        raise _handle(e)


@router.delete("/{cartao_id}", status_code=204,
               summary="Remove o cartão (faturas vão junto; compras ficam sem vínculo)",
               dependencies=[Depends(exige_editar)])
async def remover(cartao_id: str) -> None:
    try:
        await cartao_service.excluir_cartao(cartao_id)
    except Exception as e:
        raise _handle(e)

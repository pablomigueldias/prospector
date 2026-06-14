from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies.financas import (
    exige_editar,
    financas_usuario_id,
    usuario_financas,
)
from app.api.schemas.financas import (
    BoletoParceladoCreate,
    CompraCategoriaSugestao,
    CompraParceladaCreate,
    CompraResponse,
)
from app.api.services.financas import compra_service
from app.api.services.financas.compra_service import CompraError

router = APIRouter(prefix="/api/financas/compras", tags=["financas:compras"])


def _handle(e: Exception) -> HTTPException:
    if isinstance(e, CompraError):
        msg = str(e)
        status = 404 if "não encontrad" in msg.lower() else 400
        return HTTPException(status_code=status, detail=msg)
    return HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")


@router.post("", response_model=CompraResponse, status_code=201,
             summary="Compra no cartão parcelada → gera N parcelas em faturas",
             dependencies=[Depends(exige_editar)])
async def criar_parcelada(
    body: CompraParceladaCreate,
    usuario_id: str = Depends(financas_usuario_id),
) -> CompraResponse:
    body.usuario_id = usuario_id  # dono = sessão
    try:
        return await compra_service.criar_compra_parcelada(body)
    except Exception as e:
        raise _handle(e)


@router.post("/boleto", response_model=CompraResponse, status_code=201,
             summary="Boleto parcelado (sem cartão) → gera N parcelas mensais",
             dependencies=[Depends(exige_editar)])
async def criar_boleto_parcelado(
    body: BoletoParceladoCreate,
    usuario_id: str = Depends(financas_usuario_id),
) -> CompraResponse:
    body.usuario_id = usuario_id  # dono = sessão
    try:
        return await compra_service.criar_compra_boleto_parcelada(body)
    except Exception as e:
        raise _handle(e)


@router.get("/sugestao-categoria", response_model=CompraCategoriaSugestao,
            summary="Categoria da última compra com a mesma descrição",
            dependencies=[Depends(usuario_financas)])
async def sugestao_categoria(
    descricao: str = Query(..., description="Descrição da compra digitada"),
    usuario_id: str = Depends(financas_usuario_id),
) -> CompraCategoriaSugestao:
    try:
        return await compra_service.sugerir_categoria(usuario_id, descricao)
    except Exception as e:
        raise _handle(e)


@router.get("/{compra_id}", response_model=CompraResponse,
            summary="Detalhe da compra (com as parcelas)",
            dependencies=[Depends(usuario_financas)])
async def detalhe(compra_id: str) -> CompraResponse:
    try:
        return await compra_service.get_compra(compra_id)
    except Exception as e:
        raise _handle(e)


@router.delete("/{compra_id}", status_code=204,
               summary="Estorna a compra: remove as parcelas e abate das faturas",
               dependencies=[Depends(exige_editar)])
async def excluir(
    compra_id: str,
    usuario_id: str = Depends(financas_usuario_id),
) -> None:
    try:
        await compra_service.excluir_compra(compra_id, usuario_id=usuario_id)
    except Exception as e:
        raise _handle(e)

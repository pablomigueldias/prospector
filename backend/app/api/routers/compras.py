from fastapi import APIRouter, HTTPException

from app.api.schemas.financas import (
    BoletoParceladoCreate,
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
             summary="Compra no cartão parcelada → gera N parcelas em faturas")
async def criar_parcelada(body: CompraParceladaCreate) -> CompraResponse:
    try:
        return await compra_service.criar_compra_parcelada(body)
    except Exception as e:
        raise _handle(e)


@router.post("/boleto", response_model=CompraResponse, status_code=201,
             summary="Boleto parcelado (sem cartão) → gera N parcelas mensais")
async def criar_boleto_parcelado(body: BoletoParceladoCreate) -> CompraResponse:
    try:
        return await compra_service.criar_compra_boleto_parcelada(body)
    except Exception as e:
        raise _handle(e)


@router.get("/{compra_id}", response_model=CompraResponse,
            summary="Detalhe da compra (com as parcelas)")
async def detalhe(compra_id: str) -> CompraResponse:
    try:
        return await compra_service.get_compra(compra_id)
    except Exception as e:
        raise _handle(e)

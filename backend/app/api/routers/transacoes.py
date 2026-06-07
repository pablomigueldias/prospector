from fastapi import APIRouter, HTTPException

from app.api.schemas.financas import DespesaCreate, TransacaoResponse
from app.api.services.financas import transacao_service
from app.api.services.financas.transacao_service import TransacaoError

router = APIRouter(prefix="/api/financas/transacoes", tags=["financas:transacoes"])


def _handle(e: Exception) -> HTTPException:
    if isinstance(e, TransacaoError):
        msg = str(e)
        status = 404 if "não encontrad" in msg.lower() else 400
        return HTTPException(status_code=status, detail=msg)
    return HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")


@router.post("/despesa", response_model=TransacaoResponse, status_code=201,
             summary="Lança uma despesa simples (uma conta)")
async def lancar_despesa(body: DespesaCreate) -> TransacaoResponse:
    try:
        return await transacao_service.lancar_despesa(body)
    except Exception as e:
        raise _handle(e)


@router.get("/{transacao_id}", response_model=TransacaoResponse,
            summary="Detalhe da transação (com itens e pagamentos)")
async def detalhe(transacao_id: str) -> TransacaoResponse:
    try:
        return await transacao_service.get_transacao(transacao_id)
    except Exception as e:
        raise _handle(e)

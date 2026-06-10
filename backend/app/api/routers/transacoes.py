from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies.financas import (
    exige_editar,
    financas_usuario_id,
    usuario_financas,
)
from app.api.schemas.financas import (
    DespesaAutoSplitCreate,
    DespesaCreate,
    DespesaDivididaCreate,
    ReceitaCreate,
    TransacaoListResponse,
    TransacaoResponse,
)
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
             summary="Lança uma despesa simples (uma conta)",
             dependencies=[Depends(exige_editar)])
async def lancar_despesa(
    body: DespesaCreate,
    usuario_id: str = Depends(financas_usuario_id),
) -> TransacaoResponse:
    body.usuario_id = usuario_id  # dono = sessão
    try:
        return await transacao_service.lancar_despesa(body)
    except Exception as e:
        raise _handle(e)


@router.post("/receita", response_model=TransacaoResponse, status_code=201,
             summary="Lança uma receita simples (uma conta)",
             dependencies=[Depends(exige_editar)])
async def lancar_receita(
    body: ReceitaCreate,
    usuario_id: str = Depends(financas_usuario_id),
) -> TransacaoResponse:
    body.usuario_id = usuario_id  # dono = sessão
    try:
        return await transacao_service.lancar_receita(body)
    except Exception as e:
        raise _handle(e)


@router.post("/despesa/dividida", response_model=TransacaoResponse, status_code=201,
             summary="Lança despesa paga por N contas (split explícito)",
             dependencies=[Depends(exige_editar)])
async def lancar_despesa_dividida(
    body: DespesaDivididaCreate,
    usuario_id: str = Depends(financas_usuario_id),
) -> TransacaoResponse:
    body.usuario_id = usuario_id  # dono = sessão
    try:
        return await transacao_service.lancar_despesa_dividida(body)
    except Exception as e:
        raise _handle(e)


@router.post("/despesa/auto-split", response_model=TransacaoResponse, status_code=201,
             summary="Esgota o VR/VA e joga o resto no dinheiro",
             dependencies=[Depends(exige_editar)])
async def lancar_despesa_auto_split(
    body: DespesaAutoSplitCreate,
    usuario_id: str = Depends(financas_usuario_id),
) -> TransacaoResponse:
    body.usuario_id = usuario_id  # dono = sessão
    try:
        return await transacao_service.lancar_despesa_auto_split(body)
    except Exception as e:
        raise _handle(e)


@router.get("", response_model=TransacaoListResponse,
            summary="Lista filtrável das transações do usuário logado")
async def listar(
    ano: Optional[int] = Query(None, description="Filtra pelo mês de competência (com mes)"),
    mes: Optional[int] = Query(None, ge=1, le=12),
    conta_id: Optional[str] = Query(None, description="Só transações que tocam essa conta"),
    categoria_id: Optional[str] = None,
    tipo: Optional[str] = Query(None, description="despesa | receita"),
    busca: Optional[str] = Query(None, description="Texto na descrição"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    usuario_id: str = Depends(financas_usuario_id),
) -> TransacaoListResponse:
    try:
        return await transacao_service.listar_transacoes(
            usuario_id,
            ano=ano,
            mes=mes,
            conta_id=conta_id,
            categoria_id=categoria_id,
            tipo=tipo,
            busca=busca,
            limit=limit,
            offset=offset,
        )
    except Exception as e:
        raise _handle(e)


@router.get("/{transacao_id}", response_model=TransacaoResponse,
            summary="Detalhe da transação (com itens e pagamentos)",
            dependencies=[Depends(usuario_financas)])
async def detalhe(transacao_id: str) -> TransacaoResponse:
    try:
        return await transacao_service.get_transacao(transacao_id)
    except Exception as e:
        raise _handle(e)


@router.delete("/{transacao_id}", status_code=204,
               summary="Exclui a transação e reverte o saldo (se paga)",
               dependencies=[Depends(exige_editar)])
async def excluir(transacao_id: str) -> None:
    try:
        await transacao_service.excluir_transacao(transacao_id)
    except Exception as e:
        raise _handle(e)

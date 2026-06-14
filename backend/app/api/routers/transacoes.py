from typing import List, Optional

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
    PagarTransacaoRequest,
    PrevistaUpdate,
    ReceitaCreate,
    RecorrenciaResponse,
    SugestaoContaResponse,
    TransacaoListResponse,
    TransacaoResponse,
    TransacaoUpdate,
    TransferenciaCreate,
    TransferenciaResponse,
)
from app.api.services.financas import recorrencia_service, transacao_service
from app.api.services.financas.recorrencia_service import RecorrenciaError
from app.api.services.financas.transacao_service import TransacaoError

router = APIRouter(prefix="/api/financas/transacoes", tags=["financas:transacoes"])


def _handle(e: Exception) -> HTTPException:
    if isinstance(e, (TransacaoError, RecorrenciaError)):
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


@router.post("/transferencia", response_model=TransferenciaResponse, status_code=201,
             summary="Transfere entre contas (ex.: guardar na reserva)",
             dependencies=[Depends(exige_editar)])
async def transferir(
    body: TransferenciaCreate,
    usuario_id: str = Depends(financas_usuario_id),
) -> TransferenciaResponse:
    body.usuario_id = usuario_id  # dono = sessão
    try:
        return await transacao_service.transferir(body)
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
    status: Optional[List[str]] = Query(None, description="prevista/paga/atrasada (repetível)"),
    busca: Optional[str] = Query(None, description="Texto na descrição"),
    por_vencimento: bool = Query(False, description="Ordena por vencimento (vencidas primeiro)"),
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
            status=status,
            busca=busca,
            por_vencimento=por_vencimento,
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


@router.patch("/{transacao_id}", response_model=TransacaoResponse,
              summary="Edita uma transação simples (uma conta) e reajusta o saldo",
              dependencies=[Depends(exige_editar)])
async def editar(
    transacao_id: str,
    body: TransacaoUpdate,
    usuario_id: str = Depends(financas_usuario_id),
) -> TransacaoResponse:
    try:
        return await transacao_service.editar_transacao(transacao_id, body, usuario_id)
    except Exception as e:
        raise _handle(e)


@router.get("/{transacao_id}/sugestao-conta", response_model=SugestaoContaResponse,
            summary="Conta sugerida pra pagar (última usada com o mesmo beneficiário)",
            dependencies=[Depends(usuario_financas)])
async def sugestao_conta(
    transacao_id: str,
    usuario_id: str = Depends(financas_usuario_id),
) -> SugestaoContaResponse:
    try:
        return SugestaoContaResponse(
            **await transacao_service.sugestao_conta_pagamento(transacao_id, usuario_id)
        )
    except Exception as e:
        raise _handle(e)


@router.post("/{transacao_id}/tornar-recorrente", response_model=RecorrenciaResponse,
             status_code=201,
             summary="Cria uma conta fixa (recorrência) a partir do boleto",
             dependencies=[Depends(exige_editar)])
async def tornar_recorrente(
    transacao_id: str,
    dia_vencimento: Optional[int] = None,
    usuario_id: str = Depends(financas_usuario_id),
) -> RecorrenciaResponse:
    try:
        return await recorrencia_service.tornar_recorrente(
            transacao_id, usuario_id, dia_vencimento
        )
    except Exception as e:
        raise _handle(e)


@router.patch("/{transacao_id}/conta-a-pagar", response_model=TransacaoResponse,
              summary="Edita uma conta a pagar (prevista) — detalha verbas, valor, etc.",
              dependencies=[Depends(exige_editar)])
async def editar_prevista(
    transacao_id: str,
    body: PrevistaUpdate,
    usuario_id: str = Depends(financas_usuario_id),
) -> TransacaoResponse:
    try:
        return await transacao_service.editar_prevista(transacao_id, body, usuario_id)
    except Exception as e:
        raise _handle(e)


@router.post("/{transacao_id}/pagar", response_model=TransacaoResponse,
             summary="Marca a transação como paga (move o saldo)",
             dependencies=[Depends(exige_editar)])
async def pagar(
    transacao_id: str,
    body: PagarTransacaoRequest,
    usuario_id: str = Depends(financas_usuario_id),
) -> TransacaoResponse:
    try:
        return await transacao_service.pagar_transacao(
            transacao_id,
            conta_id=body.conta_id,
            data_pagamento=body.data_pagamento,
            multa_percentual=body.multa_percentual,
            juros_mensal_percentual=body.juros_mensal_percentual,
            valor_pago=body.valor_pago,
            usuario_id_sessao=usuario_id,
        )
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

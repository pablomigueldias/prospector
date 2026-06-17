"""Base do service de Transações: imports compartilhados, TransacaoError e
helpers privados usados pelos submódulos (lancar/transferir/consultas/editar/
pagar/excluir)."""
from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.financas import (
    TransacaoItemResponse,
    TransacaoPagamentoResponse,
    TransacaoResponse,
)
from app.api.services.financas import eventos, saldo_service
from app.db.models.financas.categoria import Categoria
from app.db.models.financas.conta import Conta
from app.db.models.financas.transacao import STATUS_TRANSACAO, Transacao
from app.db.models.financas.transacao_pagamento import TransacaoPagamento
from app.repositories.financas.transacao_repository import TransacaoRepository


class TransacaoError(Exception):
    """Erro de negócio de Transações — vira HTTP 400/404 no router."""


from app.api.services.financas._common import iso as _iso


def _uuid(valor: str, *, campo: str = "id") -> uuid.UUID:
    try:
        return uuid.UUID(str(valor))
    except (ValueError, AttributeError):
        raise TransacaoError(f"{campo} inválido: {valor!r}")


def _to_response(t: Transacao) -> TransacaoResponse:
    return TransacaoResponse(
        id=str(t.id),
        usuario_id=str(t.usuario_id),
        tipo=t.tipo,
        descricao=t.descricao,
        valor_total=t.valor_total,
        data_competencia=t.data_competencia,
        data_pagamento=t.data_pagamento,
        data_vencimento=t.data_vencimento,
        multa_percentual=t.multa_percentual,
        juros_mensal_percentual=t.juros_mensal_percentual,
        encargos_pagos=t.encargos_pagos,
        linha_digitavel=t.linha_digitavel,
        desconto_valor=t.desconto_valor,
        desconto_ate=t.desconto_ate,
        status=t.status,
        origem=t.origem,
        categoria_id=str(t.categoria_id) if t.categoria_id else None,
        recorrencia_id=str(t.recorrencia_id) if t.recorrencia_id else None,
        notas=t.notas,
        itens=[
            TransacaoItemResponse(
                id=str(i.id),
                categoria_id=str(i.categoria_id) if i.categoria_id else None,
                descricao=i.descricao,
                valor=i.valor,
            )
            for i in t.itens
        ],
        pagamentos=[
            TransacaoPagamentoResponse(
                id=str(p.id), conta_id=str(p.conta_id), valor=p.valor
            )
            for p in t.pagamentos
        ],
        created_at=_iso(t.created_at),
        updated_at=_iso(t.updated_at),
    )


async def _buscar_conta(
    session: AsyncSession, conta_id: uuid.UUID, usuario_id: uuid.UUID
) -> Conta:
    conta = await session.get(Conta, conta_id)
    if conta is None:
        raise TransacaoError("Conta não encontrada.")
    if conta.usuario_id != usuario_id:
        raise TransacaoError("A conta não pertence a esse usuário.")
    return conta


async def _validar_categoria(
    session: AsyncSession, categoria_id: Optional[uuid.UUID]
) -> None:
    if categoria_id is not None:
        if await session.get(Categoria, categoria_id) is None:
            raise TransacaoError("Categoria não encontrada.")


async def _finalizar_transacao(
    session: AsyncSession,
    *,
    tipo: str,
    usuario_id: uuid.UUID,
    descricao: str,
    valor_total: Decimal,
    categoria_id: Optional[uuid.UUID],
    competencia: date,
    pagamento_em: Optional[date],
    status: str,
    notas: Optional[str],
    pagamentos: List[Tuple[Conta, Decimal]],
    vencimento: Optional[date] = None,
) -> TransacaoResponse:
    """Núcleo: cria a transação (despesa/receita) com N pagamentos e ajusta o
    saldo de cada conta (só quando paga). Assume contas/categoria já validadas."""
    transacao = Transacao(
        usuario_id=usuario_id,
        tipo=tipo,
        descricao=descricao,
        valor_total=valor_total,
        data_competencia=competencia,
        data_pagamento=pagamento_em,
        data_vencimento=vencimento,
        status=status,
        origem="manual",
        categoria_id=categoria_id,
        notas=notas,
        pagamentos=[
            TransacaoPagamento(conta_id=conta.id, valor=valor)
            for conta, valor in pagamentos
        ],
    )
    repo = TransacaoRepository(session)
    repo.add(transacao)

    if status == "paga":
        for conta, valor in pagamentos:
            saldo_service.aplicar_movimento(conta, tipo, valor)

    # Avisa o dashboard em tempo real (entregue no commit).
    await eventos.notificar(session, usuario_id, "transacao_criada")
    await session.commit()
    return _to_response(await repo.get(transacao.id))


def _checar_status(status: str) -> None:
    if status not in STATUS_TRANSACAO:
        raise TransacaoError(
            f"Status inválido: {status!r}. "
            f"Use um de: {', '.join(STATUS_TRANSACAO)}."
        )



def _intervalo_mes(ano: Optional[int], mes: Optional[int]) -> Tuple[
    Optional[date], Optional[date]
]:
    """(inicio, proximo_mes) para filtrar por competência; (None, None) se
    ano/mes não vierem juntos."""
    if not ano or not mes:
        return None, None
    if mes < 1 or mes > 12:
        raise TransacaoError(f"Mês inválido: {mes}.")
    inicio = date(ano, mes, 1)
    proximo = date(ano + 1, 1, 1) if mes == 12 else date(ano, mes + 1, 1)
    return inicio, proximo

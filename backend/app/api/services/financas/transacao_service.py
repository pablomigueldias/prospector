"""Service de Transações — lançamento de despesa e cálculo de saldo.

Step 7: despesa simples (uma conta, uma categoria). Split de pagamento e
resumo do mês vêm nos próximos steps.
"""
from __future__ import annotations

import uuid
from datetime import date
from typing import Optional

from app.api.schemas.financas import (
    DespesaCreate,
    TransacaoItemResponse,
    TransacaoPagamentoResponse,
    TransacaoResponse,
)
from app.api.services.financas import saldo_service
from app.db.models.financas.categoria import Categoria
from app.db.models.financas.conta import Conta
from app.db.models.financas.transacao import STATUS_TRANSACAO, Transacao
from app.db.models.financas.transacao_pagamento import TransacaoPagamento
from app.db.session import get_session
from app.repositories.financas.transacao_repository import TransacaoRepository


class TransacaoError(Exception):
    """Erro de negócio de Transações — vira HTTP 400/404 no router."""


def _iso(dt) -> Optional[str]:
    return dt.isoformat(timespec="seconds") if dt else None


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
        status=t.status,
        origem=t.origem,
        categoria_id=str(t.categoria_id) if t.categoria_id else None,
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


async def lancar_despesa(payload: DespesaCreate) -> TransacaoResponse:
    if not payload.descricao.strip():
        raise TransacaoError("A despesa precisa de uma descrição.")
    if payload.status not in STATUS_TRANSACAO:
        raise TransacaoError(
            f"Status inválido: {payload.status!r}. "
            f"Use um de: {', '.join(STATUS_TRANSACAO)}."
        )

    usuario_id = _uuid(payload.usuario_id, campo="usuario_id")
    conta_id = _uuid(payload.conta_id, campo="conta_id")
    categoria_id = (
        _uuid(payload.categoria_id, campo="categoria_id")
        if payload.categoria_id else None
    )

    competencia = payload.data_competencia or date.today()
    paga = payload.status == "paga"
    pagamento_em = payload.data_pagamento or (date.today() if paga else None)

    async with get_session() as session:
        # Conta precisa existir e ser do mesmo usuário.
        conta = await session.get(Conta, conta_id)
        if conta is None:
            raise TransacaoError("Conta não encontrada.")
        if conta.usuario_id != usuario_id:
            raise TransacaoError("A conta não pertence a esse usuário.")

        if categoria_id is not None:
            if await session.get(Categoria, categoria_id) is None:
                raise TransacaoError("Categoria não encontrada.")

        transacao = Transacao(
            usuario_id=usuario_id,
            tipo="despesa",
            descricao=payload.descricao.strip(),
            valor_total=payload.valor_total,
            data_competencia=competencia,
            data_pagamento=pagamento_em,
            status=payload.status,
            origem="manual",
            categoria_id=categoria_id,
            notas=payload.notas,
            pagamentos=[
                TransacaoPagamento(conta_id=conta_id, valor=payload.valor_total),
            ],
        )
        repo = TransacaoRepository(session)
        repo.add(transacao)

        # Só mexe no saldo quando a despesa já foi paga.
        if paga:
            saldo_service.aplicar_movimento(conta, "despesa", payload.valor_total)

        await session.commit()

        transacao_completa = await repo.get(transacao.id)
        return _to_response(transacao_completa)


async def get_transacao(transacao_id: str) -> TransacaoResponse:
    async with get_session() as session:
        transacao = await TransacaoRepository(session).get(_uuid(transacao_id))
        if transacao is None:
            raise TransacaoError("Transação não encontrada.")
        return _to_response(transacao)

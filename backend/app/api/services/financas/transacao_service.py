"""Service de Transações — lançamento de despesa e cálculo de saldo.

Step 7: despesa simples (uma conta, uma categoria). Split de pagamento e
resumo do mês vêm nos próximos steps.
"""
from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.financas import (
    DespesaAutoSplitCreate,
    DespesaCreate,
    DespesaDivididaCreate,
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


async def _finalizar_despesa(
    session: AsyncSession,
    *,
    usuario_id: uuid.UUID,
    descricao: str,
    valor_total: Decimal,
    categoria_id: Optional[uuid.UUID],
    competencia: date,
    pagamento_em: Optional[date],
    status: str,
    notas: Optional[str],
    pagamentos: List[Tuple[Conta, Decimal]],
) -> TransacaoResponse:
    """Núcleo: cria a despesa com N pagamentos e ajusta o saldo de cada conta
    (só quando paga). Assume contas/categoria já validadas."""
    transacao = Transacao(
        usuario_id=usuario_id,
        tipo="despesa",
        descricao=descricao,
        valor_total=valor_total,
        data_competencia=competencia,
        data_pagamento=pagamento_em,
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
            saldo_service.aplicar_movimento(conta, "despesa", valor)

    await session.commit()
    return _to_response(await repo.get(transacao.id))


def _checar_status(status: str) -> None:
    if status not in STATUS_TRANSACAO:
        raise TransacaoError(
            f"Status inválido: {status!r}. "
            f"Use um de: {', '.join(STATUS_TRANSACAO)}."
        )


async def lancar_despesa(payload: DespesaCreate) -> TransacaoResponse:
    if not payload.descricao.strip():
        raise TransacaoError("A despesa precisa de uma descrição.")
    _checar_status(payload.status)

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
        conta = await _buscar_conta(session, conta_id, usuario_id)
        await _validar_categoria(session, categoria_id)
        return await _finalizar_despesa(
            session,
            usuario_id=usuario_id,
            descricao=payload.descricao.strip(),
            valor_total=payload.valor_total,
            categoria_id=categoria_id,
            competencia=competencia,
            pagamento_em=pagamento_em,
            status=payload.status,
            notas=payload.notas,
            pagamentos=[(conta, payload.valor_total)],
        )


async def lancar_despesa_dividida(
    payload: DespesaDivididaCreate,
) -> TransacaoResponse:
    if not payload.descricao.strip():
        raise TransacaoError("A despesa precisa de uma descrição.")
    _checar_status(payload.status)

    soma = sum((p.valor for p in payload.pagamentos), Decimal("0"))
    if soma != payload.valor_total:
        raise TransacaoError(
            f"A soma dos pagamentos (R${soma}) não bate com o total "
            f"(R${payload.valor_total})."
        )

    usuario_id = _uuid(payload.usuario_id, campo="usuario_id")
    categoria_id = (
        _uuid(payload.categoria_id, campo="categoria_id")
        if payload.categoria_id else None
    )
    competencia = payload.data_competencia or date.today()
    paga = payload.status == "paga"
    pagamento_em = payload.data_pagamento or (date.today() if paga else None)

    async with get_session() as session:
        await _validar_categoria(session, categoria_id)
        pagamentos: List[Tuple[Conta, Decimal]] = []
        for p in payload.pagamentos:
            conta = await _buscar_conta(
                session, _uuid(p.conta_id, campo="conta_id"), usuario_id
            )
            pagamentos.append((conta, p.valor))

        return await _finalizar_despesa(
            session,
            usuario_id=usuario_id,
            descricao=payload.descricao.strip(),
            valor_total=payload.valor_total,
            categoria_id=categoria_id,
            competencia=competencia,
            pagamento_em=pagamento_em,
            status=payload.status,
            notas=payload.notas,
            pagamentos=pagamentos,
        )


async def lancar_despesa_auto_split(
    payload: DespesaAutoSplitCreate,
) -> TransacaoResponse:
    """Esgota o VR/VA e joga o resto no dinheiro. Sempre paga (move o saldo)."""
    if not payload.descricao.strip():
        raise TransacaoError("A despesa precisa de uma descrição.")

    usuario_id = _uuid(payload.usuario_id, campo="usuario_id")
    vr_id = _uuid(payload.conta_vr_id, campo="conta_vr_id")
    fallback_id = _uuid(payload.conta_fallback_id, campo="conta_fallback_id")
    categoria_id = (
        _uuid(payload.categoria_id, campo="categoria_id")
        if payload.categoria_id else None
    )
    if vr_id == fallback_id:
        raise TransacaoError("As contas de VR e fallback precisam ser diferentes.")

    competencia = payload.data_competencia or date.today()
    total = payload.valor_total

    async with get_session() as session:
        vr = await _buscar_conta(session, vr_id, usuario_id)
        fallback = await _buscar_conta(session, fallback_id, usuario_id)
        await _validar_categoria(session, categoria_id)

        # Quanto o VR cobre (nunca negativo), o resto vai pro fallback.
        vr_disponivel = max(Decimal("0"), Decimal(vr.saldo_atual))
        parte_vr = min(total, vr_disponivel)
        parte_fallback = total - parte_vr

        pagamentos: List[Tuple[Conta, Decimal]] = []
        if parte_vr > 0:
            pagamentos.append((vr, parte_vr))
        if parte_fallback > 0:
            pagamentos.append((fallback, parte_fallback))

        return await _finalizar_despesa(
            session,
            usuario_id=usuario_id,
            descricao=payload.descricao.strip(),
            valor_total=total,
            categoria_id=categoria_id,
            competencia=competencia,
            pagamento_em=date.today(),
            status="paga",
            notas=payload.notas,
            pagamentos=pagamentos,
        )


async def get_transacao(transacao_id: str) -> TransacaoResponse:
    async with get_session() as session:
        transacao = await TransacaoRepository(session).get(_uuid(transacao_id))
        if transacao is None:
            raise TransacaoError("Transação não encontrada.")
        return _to_response(transacao)

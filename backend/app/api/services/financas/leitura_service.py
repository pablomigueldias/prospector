"""Service de Leituras de Consumo (água/gás/luz)."""
from __future__ import annotations

import uuid

from sqlalchemy import select

from app.api.schemas.financas import (
    LeituraConsumoCreate,
    LeituraConsumoListResponse,
    LeituraConsumoResponse,
)
from app.db.models.financas.leitura_consumo import TIPOS_CONSUMO, LeituraConsumo
from app.db.session import get_session


class LeituraError(Exception):
    """Erro de negócio de Leituras — vira HTTP 400 no router."""


from app.api.services.financas._common import iso as _iso


def _uuid(valor: str, *, campo: str = "id") -> uuid.UUID:
    try:
        return uuid.UUID(str(valor))
    except (ValueError, AttributeError):
        raise LeituraError(f"{campo} inválido: {valor!r}")


def _to_response(le: LeituraConsumo) -> LeituraConsumoResponse:
    return LeituraConsumoResponse(
        id=str(le.id),
        usuario_id=str(le.usuario_id),
        tipo=le.tipo,
        mes_referencia=le.mes_referencia,
        leitura_atual=le.leitura_atual,
        leitura_anterior=le.leitura_anterior,
        consumo=le.consumo,
        valor=le.valor,
        transacao_id=str(le.transacao_id) if le.transacao_id else None,
        created_at=_iso(le.created_at),
        updated_at=_iso(le.updated_at),
    )


async def criar_leitura(payload: LeituraConsumoCreate) -> LeituraConsumoResponse:
    if payload.tipo not in TIPOS_CONSUMO:
        raise LeituraError(
            f"Tipo inválido: {payload.tipo!r}. Use um de: {', '.join(TIPOS_CONSUMO)}."
        )

    # Calcula o consumo se não veio explícito e há leitura anterior.
    consumo = payload.consumo
    if consumo is None and payload.leitura_anterior is not None:
        consumo = payload.leitura_atual - payload.leitura_anterior

    async with get_session() as session:
        leitura = LeituraConsumo(
            usuario_id=_uuid(payload.usuario_id, campo="usuario_id"),
            tipo=payload.tipo,
            mes_referencia=payload.mes_referencia,
            leitura_atual=payload.leitura_atual,
            leitura_anterior=payload.leitura_anterior,
            consumo=consumo,
            valor=payload.valor,
            transacao_id=(
                _uuid(payload.transacao_id, campo="transacao_id")
                if payload.transacao_id else None
            ),
        )
        session.add(leitura)
        await session.commit()
        await session.refresh(leitura)
        return _to_response(leitura)


async def listar_leituras(
    usuario_id: str, *, tipo: str | None = None
) -> LeituraConsumoListResponse:
    uid = _uuid(usuario_id, campo="usuario_id")
    if tipo is not None and tipo not in TIPOS_CONSUMO:
        raise LeituraError(f"Tipo inválido: {tipo!r}.")

    async with get_session() as session:
        stmt = (
            select(LeituraConsumo)
            .where(LeituraConsumo.usuario_id == uid)
            .order_by(LeituraConsumo.mes_referencia)
        )
        if tipo is not None:
            stmt = stmt.where(LeituraConsumo.tipo == tipo)
        leituras = (await session.execute(stmt)).scalars().all()
        items = [_to_response(le) for le in leituras]
    return LeituraConsumoListResponse(items=items, total=len(items))

"""Service de Recorrências — cadastro e leitura das despesas/receitas fixas."""
from __future__ import annotations

import uuid
from typing import List, Optional

from sqlalchemy import select

from app.api.schemas.financas import (
    RecorrenciaCreate,
    RecorrenciaListResponse,
    RecorrenciaResponse,
)
from app.db.models.financas.categoria import Categoria
from app.db.models.financas.conta import Conta
from app.db.models.financas.recorrencia import Recorrencia
from app.db.session import get_session

TIPOS_RECORRENCIA = ("despesa", "receita")


class RecorrenciaError(Exception):
    """Erro de negócio de Recorrências — vira HTTP 400/404 no router."""


def _iso(dt) -> Optional[str]:
    return dt.isoformat(timespec="seconds") if dt else None


def _uuid(valor: str, *, campo: str = "id") -> uuid.UUID:
    try:
        return uuid.UUID(str(valor))
    except (ValueError, AttributeError):
        raise RecorrenciaError(f"{campo} inválido: {valor!r}")


def _to_response(r: Recorrencia) -> RecorrenciaResponse:
    return RecorrenciaResponse(
        id=str(r.id),
        usuario_id=str(r.usuario_id),
        descricao=r.descricao,
        tipo=r.tipo,
        valor_estimado=r.valor_estimado,
        dia_vencimento=r.dia_vencimento,
        frequencia=r.frequencia,
        categoria_id=str(r.categoria_id) if r.categoria_id else None,
        conta_id=str(r.conta_id) if r.conta_id else None,
        ativa=r.ativa,
        created_at=_iso(r.created_at),
        updated_at=_iso(r.updated_at),
    )


async def criar_recorrencia(payload: RecorrenciaCreate) -> RecorrenciaResponse:
    if not payload.descricao.strip():
        raise RecorrenciaError("A recorrência precisa de uma descrição.")
    if payload.tipo not in TIPOS_RECORRENCIA:
        raise RecorrenciaError(
            f"Tipo inválido: {payload.tipo!r}. Use 'despesa' ou 'receita'."
        )

    usuario_id = _uuid(payload.usuario_id, campo="usuario_id")
    categoria_id = (
        _uuid(payload.categoria_id, campo="categoria_id")
        if payload.categoria_id else None
    )
    conta_id = _uuid(payload.conta_id, campo="conta_id") if payload.conta_id else None

    async with get_session() as session:
        if categoria_id and await session.get(Categoria, categoria_id) is None:
            raise RecorrenciaError("Categoria não encontrada.")
        if conta_id is not None:
            conta = await session.get(Conta, conta_id)
            if conta is None:
                raise RecorrenciaError("Conta não encontrada.")
            if conta.usuario_id != usuario_id:
                raise RecorrenciaError("A conta não pertence a esse usuário.")

        rec = Recorrencia(
            usuario_id=usuario_id,
            descricao=payload.descricao.strip(),
            tipo=payload.tipo,
            valor_estimado=payload.valor_estimado,
            dia_vencimento=payload.dia_vencimento,
            frequencia=payload.frequencia,
            categoria_id=categoria_id,
            conta_id=conta_id,
        )
        session.add(rec)
        await session.commit()
        await session.refresh(rec)
        return _to_response(rec)


async def listar_recorrencias(usuario_id: str) -> RecorrenciaListResponse:
    uid = _uuid(usuario_id, campo="usuario_id")
    async with get_session() as session:
        stmt = (
            select(Recorrencia)
            .where(Recorrencia.usuario_id == uid)
            .order_by(Recorrencia.dia_vencimento)
        )
        recs = (await session.execute(stmt)).scalars().all()
        items = [_to_response(r) for r in recs]
    return RecorrenciaListResponse(items=items, total=len(items))

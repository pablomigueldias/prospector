"""Service de Cartões — cadastro e leitura."""
from __future__ import annotations

import uuid
from typing import Optional

from app.api.schemas.financas import CartaoCreate, CartaoResponse
from app.db.models.financas.cartao import Cartao
from app.db.session import get_session


class CartaoError(Exception):
    """Erro de negócio de Cartões — vira HTTP 400/404 no router."""


def _iso(dt) -> Optional[str]:
    return dt.isoformat(timespec="seconds") if dt else None


def _uuid(valor: str, *, campo: str = "id") -> uuid.UUID:
    try:
        return uuid.UUID(str(valor))
    except (ValueError, AttributeError):
        raise CartaoError(f"{campo} inválido: {valor!r}")


def _to_response(c: Cartao) -> CartaoResponse:
    return CartaoResponse(
        id=str(c.id),
        usuario_id=str(c.usuario_id),
        nome=c.nome,
        bandeira=c.bandeira,
        dia_fechamento=c.dia_fechamento,
        dia_vencimento=c.dia_vencimento,
        limite=c.limite,
        ativo=c.ativo,
        created_at=_iso(c.created_at),
        updated_at=_iso(c.updated_at),
    )


async def criar_cartao(payload: CartaoCreate) -> CartaoResponse:
    if not payload.nome.strip():
        raise CartaoError("O cartão precisa de um nome.")
    async with get_session() as session:
        cartao = Cartao(
            usuario_id=_uuid(payload.usuario_id, campo="usuario_id"),
            nome=payload.nome.strip(),
            bandeira=payload.bandeira,
            dia_fechamento=payload.dia_fechamento,
            dia_vencimento=payload.dia_vencimento,
            limite=payload.limite,
        )
        session.add(cartao)
        await session.commit()
        await session.refresh(cartao)
        return _to_response(cartao)


async def get_cartao(cartao_id: str) -> CartaoResponse:
    async with get_session() as session:
        cartao = await session.get(Cartao, _uuid(cartao_id))
        if cartao is None:
            raise CartaoError("Cartão não encontrado.")
        return _to_response(cartao)

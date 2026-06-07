from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import Boolean, Index, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import expression

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Cartao(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Cartão de crédito. dia_fechamento/dia_vencimento definem em qual fatura
    cada compra cai e quando vence."""

    __tablename__ = "cartoes"

    usuario_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False
    )
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    bandeira: Mapped[Optional[str]] = mapped_column(String(50))
    dia_fechamento: Mapped[int] = mapped_column(Integer, nullable=False)
    dia_vencimento: Mapped[int] = mapped_column(Integer, nullable=False)
    limite: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    ativo: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=expression.true()
    )

    __table_args__ = (
        Index("ix_fin_cartoes_usuario_id", "usuario_id"),
        {"schema": "financas"},
    )

    def __repr__(self) -> str:
        return f"<Cartao id={self.id} nome={self.nome!r}>"

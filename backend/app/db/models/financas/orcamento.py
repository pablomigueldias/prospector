from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, Index, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import expression

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Orcamento(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Teto mensal de despesa por categoria (ex.: R$800 em Mercado). O consumido
    do mês é calculado das transações (não é guardado). Um por (usuário,
    categoria)."""

    __tablename__ = "orcamentos"

    usuario_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False
    )
    categoria_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("financas.categorias.id", ondelete="CASCADE"),
        nullable=False,
    )
    valor_mensal: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    ativo: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=expression.true()
    )

    __table_args__ = (
        UniqueConstraint(
            "usuario_id", "categoria_id", name="uq_fin_orcamentos_usuario_categoria"
        ),
        Index("ix_fin_orcamentos_usuario_id", "usuario_id"),
        {"schema": "financas"},
    )

    def __repr__(self) -> str:
        return f"<Orcamento cat={self.categoria_id} R${self.valor_mensal}/mês>"

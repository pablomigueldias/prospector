from __future__ import annotations

import uuid
from typing import List, Optional

from sqlalchemy import Boolean, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import expression

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Categoria(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Categoria hierárquica de gastos/receitas.

    O auto-relacionamento (``categoria_pai_id``) é o que resolve o boleto do
    condomínio: uma categoria-pai ("Condomínio") com várias subverbas
    ("Consumo de gás", "Fundo de reserva"...). Categorias são compartilhadas
    (não têm usuario_id) — o seed inicial monta a árvore base.
    """

    __tablename__ = "categorias"

    nome: Mapped[str] = mapped_column(String(200), nullable=False)

    categoria_pai_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("financas.categorias.id", ondelete="CASCADE"),
        nullable=True,
    )

    ativa: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=expression.true()
    )

    # ── Auto-relacionamento (pai ↔ filhos) ───────────────────────────
    pai: Mapped[Optional["Categoria"]] = relationship(
        "Categoria",
        remote_side="Categoria.id",
        back_populates="filhos",
    )
    filhos: Mapped[List["Categoria"]] = relationship(
        "Categoria",
        back_populates="pai",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_fin_categorias_pai_id", "categoria_pai_id"),
        {"schema": "financas"},
    )

    def __repr__(self) -> str:
        return f"<Categoria id={self.id} nome={self.nome!r} pai={self.categoria_pai_id}>"

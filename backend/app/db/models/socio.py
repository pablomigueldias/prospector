from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


if TYPE_CHECKING:
    from app.db.models.empresa import Empresa


class Socio(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "socios"

    empresa_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("empresas.id", ondelete="CASCADE"),
        nullable=False,
    )

    nome: Mapped[str] = mapped_column(String(300), nullable=False)
    qualificacao: Mapped[Optional[str]] = mapped_column(String(200))

    # ── Relacionamento reverso ───────────────────────────────────
    empresa: Mapped["Empresa"] = relationship(back_populates="socios")

    __table_args__ = (
        Index("ix_socios_empresa_id", "empresa_id"),
    )

    def __repr__(self) -> str:
        return f"<Socio id={self.id} nome={self.nome!r}>"
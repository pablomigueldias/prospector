from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


if TYPE_CHECKING:
    from app.db.models.empresa import Empresa


class Contato(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "contatos"

    # ── FK pra empresa ───────────────────────────────────────────
    empresa_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("empresas.id", ondelete="CASCADE"),
        nullable=False,
    )

    # ── Identidade ───────────────────────────────────────────────
    nome: Mapped[str] = mapped_column(String(300), nullable=False)
    cargo: Mapped[Optional[str]] = mapped_column(String(200))
    decisor: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true", nullable=False
    )

    # ── Canais de contato ────────────────────────────────────────
    email: Mapped[Optional[str]] = mapped_column(String(300))
    telefone: Mapped[Optional[str]] = mapped_column(String(50))
    whatsapp: Mapped[Optional[str]] = mapped_column(String(50))
    linkedin: Mapped[Optional[str]] = mapped_column(String(500))

    # ── Metadata de origem ───────────────────────────────────────
    origem_contato: Mapped[str] = mapped_column(
        String(50), default="Network", server_default="Network"
    )

    # ── Sync com Notion ──────────────────────────────────────────
    notion_page_id: Mapped[Optional[str]] = mapped_column(String(50))
    notion_synced_at: Mapped[Optional[datetime]] = mapped_column()

    # ── Relacionamento ───────────────────────────────────────────
    empresa: Mapped["Empresa"] = relationship(back_populates="contatos")

    __table_args__ = (
        Index("ix_contatos_empresa_id", "empresa_id"),
        # Buscar contato por email é caso comum (dedup, etc)
        Index("ix_contatos_email", "email"),
        # Filtrar só decisores também é comum
        Index("ix_contatos_decisor", "decisor"),
    )

    def __repr__(self) -> str:
        return f"<Contato id={self.id} nome={self.nome!r}>"

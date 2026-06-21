from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Atividade(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Atividade/follow-up (espelha a base 'Atividades' do Notion)."""

    __tablename__ = "atividades"

    titulo: Mapped[str] = mapped_column(String(500), nullable=False)
    tipo: Mapped[str | None] = mapped_column(String(60))      # ✉️ E-mail, ☎️ Ligação…
    status: Mapped[str | None] = mapped_column(String(60))    # 🟡 Agendada…
    data: Mapped[datetime | None] = mapped_column(DateTime(timezone=False))
    resumo: Mapped[str | None] = mapped_column(Text)
    proximos_passos: Mapped[str | None] = mapped_column(Text)

    negocio_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("negocios.id", ondelete="SET NULL")
    )
    contato_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("contatos.id", ondelete="SET NULL")
    )

    negocio = relationship("Negocio", lazy="selectin")
    contato = relationship("Contato", lazy="selectin")

    notion_page_id: Mapped[str | None] = mapped_column(String(50))
    notion_synced_at: Mapped[datetime | None] = mapped_column()

    __table_args__ = (
        Index("ix_atividades_data", "data"),
        Index("ix_atividades_status", "status"),
        Index("ix_atividades_negocio_id", "negocio_id"),
        Index("ix_atividades_notion_page_id", "notion_page_id"),
    )

    def __repr__(self) -> str:
        return f"<Atividade {self.titulo!r} status={self.status}>"

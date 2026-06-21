from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class EmailOutreach(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "email_outreach"

    empresa_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("empresas.id", ondelete="SET NULL"),
        nullable=True,
    )
    contato_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("contatos.id", ondelete="SET NULL"),
        nullable=True,
    )

    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("email_outreach.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ── Conteúdo do e-mail gerado
    destinatario: Mapped[str] = mapped_column(String(300), nullable=False)
    assunto: Mapped[str] = mapped_column(String(500), nullable=False)
    corpo: Mapped[str] = mapped_column(Text, nullable=False)
    tom: Mapped[str | None] = mapped_column(String(100))
    canal: Mapped[str] = mapped_column(
        String(20), default="email", server_default="email", nullable=False
    )
    follow_up_num: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )

    # ciclo de vida
    status: Mapped[str] = mapped_column(
        String(30), default="rascunho", server_default="rascunho", nullable=False
    )
    message_id: Mapped[str | None] = mapped_column(String(500))
    sent_message_id: Mapped[str | None] = mapped_column(String(500))

    draft_criado_em: Mapped[datetime | None] = mapped_column()
    enviado_em: Mapped[datetime | None] = mapped_column()
    primeira_resposta_em: Mapped[datetime | None] = mapped_column()
    resposta_trecho: Mapped[str | None] = mapped_column(Text)
    resposta_corpo: Mapped[str | None] = mapped_column(Text)

    # Dados pra treino futuro da IA
    contexto: Mapped[dict | None] = mapped_column(JSONB)
    resultado: Mapped[dict | None] = mapped_column(JSONB)

    __table_args__ = (
        Index("ix_email_outreach_contato_id", "contato_id"),
        Index("ix_email_outreach_empresa_id", "empresa_id"),
        Index("ix_email_outreach_status", "status"),
        Index("ix_email_outreach_message_id", "message_id"),
        Index("ix_email_outreach_destinatario", "destinatario"),
    )

    def __repr__(self) -> str:
        return (
            f"<EmailOutreach id={self.id} para={self.destinatario!r} "
            f"status={self.status}>"
        )

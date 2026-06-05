from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


if TYPE_CHECKING:
    from app.db.models.pessoal.vaga import Vaga


class CandidaturaEmail(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Rascunho de candidatura — espelha o EmailOutreach do Prospector.

    PRINCÍPIO INEGOCIÁVEL: a ferramenta gera o rascunho e PARA. Quem
    revisa e envia é você. Por isso o status nasce 'rascunho' e nada aqui
    dispara e-mail.
    """

    __tablename__ = "pessoal_candidatura_emails"

    vaga_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("pessoal_vagas.id", ondelete="CASCADE"),
        nullable=False,
    )

    # email | carta
    tipo: Mapped[str] = mapped_column(
        String(20), default="email", server_default="email", nullable=False
    )

    destinatario: Mapped[Optional[str]] = mapped_column(String(300))
    assunto: Mapped[Optional[str]] = mapped_column(String(500))
    corpo: Mapped[str] = mapped_column(Text, nullable=False)
    tom: Mapped[Optional[str]] = mapped_column(String(100))

    # ciclo de vida — nasce rascunho; envio é manual, fora da ferramenta
    status: Mapped[str] = mapped_column(
        String(30), default="rascunho", server_default="rascunho", nullable=False
    )
    enviado_em: Mapped[Optional[datetime]] = mapped_column()

    # variantes A/B e contexto usado na geração (pra revisar/treinar)
    variantes: Mapped[Optional[list]] = mapped_column(JSONB)
    contexto: Mapped[Optional[dict]] = mapped_column(JSONB)

    vaga: Mapped["Vaga"] = relationship(back_populates="emails")

    __table_args__ = (
        Index("ix_pessoal_cand_emails_vaga_id", "vaga_id"),
        Index("ix_pessoal_cand_emails_status", "status"),
    )

    def __repr__(self) -> str:
        return (
            f"<CandidaturaEmail id={self.id} tipo={self.tipo} "
            f"status={self.status}>"
        )

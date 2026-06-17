from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.pessoal.freela.projeto import Projeto


# Ciclo de vida da proposta = colunas do Kanban. A transição é MANUAL
# (você marca com 1 clique): a Workana não nos avisa programaticamente e
# não queremos automação.
STATUS_PROPOSTA = (
    "rascunho",
    "enviada",
    "visualizada",
    "respondida",
    "negociando",
    "fechada",
    "perdida",
)


class Proposta(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A proposta que VOCÊ envia na mão. A ferramenta gera o material e PARA;
    nada aqui toca na Workana. ``valor_cotado`` é o total; o líquido sai do
    precificador (desconta a comissão da faixa do cliente).
    """

    __tablename__ = "pessoal_freela_proposta"

    projeto_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("pessoal_freela_projeto.id", ondelete="CASCADE"),
        nullable=False,
    )

    valor_cotado: Mapped[float | None] = mapped_column(Numeric(12, 2))
    horas_estimadas: Mapped[float | None] = mapped_column(Numeric(8, 2))
    valor_liquido_estimado: Mapped[float | None] = mapped_column(Numeric(12, 2))

    texto_enviado: Mapped[str | None] = mapped_column(Text)
    projetos_destacados: Mapped[list | None] = mapped_column(JSONB)
    habilidades_destacadas: Mapped[list | None] = mapped_column(JSONB)
    prazo_proposto: Mapped[str | None] = mapped_column(String(100))

    status: Mapped[str] = mapped_column(
        String(20), default="rascunho", server_default="rascunho", nullable=False
    )

    enviada_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    data_resposta: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    data_fechamento: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    motivo_perda: Mapped[str | None] = mapped_column(Text)

    projeto: Mapped[Projeto] = relationship(
        back_populates="propostas", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Proposta id={self.id} status={self.status} valor={self.valor_cotado}>"

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Date, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Negocio(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Negócio/deal do pipeline de vendas (espelha a base 'Negócios' do Notion)."""

    __tablename__ = "negocios"

    nome: Mapped[str] = mapped_column(String(500), nullable=False)
    estagio: Mapped[str | None] = mapped_column(String(60))      # ⚪ Lead novo…
    valor_estimado: Mapped[float | None] = mapped_column(Numeric(15, 2))
    probabilidade: Mapped[str | None] = mapped_column(String(20))  # "75%"
    origem: Mapped[str | None] = mapped_column(String(80))
    tipo_servico: Mapped[list | None] = mapped_column(JSONB)        # multi_select
    notas: Mapped[str | None] = mapped_column(Text)
    motivo_perda: Mapped[str | None] = mapped_column(String(120))

    previsao_fechamento: Mapped[date | None] = mapped_column(Date)
    data_fechamento_real: Mapped[date | None] = mapped_column(Date)
    proxima_acao: Mapped[date | None] = mapped_column(Date)

    empresa_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="SET NULL")
    )
    contato_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("contatos.id", ondelete="SET NULL")
    )

    empresa = relationship("Empresa", lazy="selectin")
    contato = relationship("Contato", lazy="selectin")

    notion_page_id: Mapped[str | None] = mapped_column(String(50))
    notion_synced_at: Mapped[datetime | None] = mapped_column()

    __table_args__ = (
        Index("ix_negocios_estagio", "estagio"),
        Index("ix_negocios_empresa_id", "empresa_id"),
        Index("ix_negocios_notion_page_id", "notion_page_id"),
    )

    def __repr__(self) -> str:
        return f"<Negocio {self.nome!r} estagio={self.estagio}>"

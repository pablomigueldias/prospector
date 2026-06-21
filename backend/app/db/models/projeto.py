from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Date, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ProjetoCRM(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Projeto/entrega do CRM (espelha a base 'Projetos' do Notion).

    Nome ``ProjetoCRM`` (não ``Projeto``) pra não colidir no registry com o
    ``Projeto`` do freela (``pessoal_freela_projeto``). Tabela = ``projetos``.
    """

    __tablename__ = "projetos"

    nome: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str | None] = mapped_column(String(60))       # 🚀 Em produção…
    tipo_servico: Mapped[str | None] = mapped_column(String(120))
    valor_total: Mapped[float | None] = mapped_column(Numeric(15, 2))
    valor_recebido: Mapped[float | None] = mapped_column(Numeric(15, 2))
    briefing: Mapped[str | None] = mapped_column(Text)
    link_producao: Mapped[str | None] = mapped_column(String(500))
    repo_github: Mapped[str | None] = mapped_column(String(500))
    forma_pagamento: Mapped[str | None] = mapped_column(String(80))

    prazo_entrega: Mapped[date | None] = mapped_column(Date)
    data_inicio: Mapped[date | None] = mapped_column(Date)
    data_entrega_real: Mapped[date | None] = mapped_column(Date)

    empresa_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="SET NULL")
    )
    negocio_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("negocios.id", ondelete="SET NULL")
    )

    empresa = relationship("Empresa", lazy="selectin")
    negocio = relationship("Negocio", lazy="selectin")

    notion_page_id: Mapped[str | None] = mapped_column(String(50))
    notion_synced_at: Mapped[datetime | None] = mapped_column()

    __table_args__ = (
        Index("ix_projetos_status", "status"),
        Index("ix_projetos_empresa_id", "empresa_id"),
        Index("ix_projetos_notion_page_id", "notion_page_id"),
    )

    def __repr__(self) -> str:
        return f"<Projeto {self.nome!r} status={self.status}>"

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Index, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.contato import Contato
    from app.db.models.socio import Socio


class Empresa(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "empresas"

    # ── Identidade ───────────────────────────────────────────────
    nome: Mapped[str] = mapped_column(String(500), nullable=False)
    razao_social: Mapped[str | None] = mapped_column(String(500))


    cnpj: Mapped[str | None] = mapped_column(String(14), unique=True)

    # ── Localização ──────────────────────────────────────────────
    cidade: Mapped[str | None] = mapped_column(String(200))
    estado: Mapped[str | None] = mapped_column(String(2))
    local: Mapped[str | None] = mapped_column(Text)  # endereço completo

    # ── Presença digital ─────────────────────────────────────────
    site: Mapped[str | None] = mapped_column(String(500))
    instagram: Mapped[str | None] = mapped_column(String(300))
    facebook: Mapped[str | None] = mapped_column(String(300))

    # ── Classificação ────────────────────────────────────────────
    capital_social: Mapped[float | None] = mapped_column(Numeric(15, 2))
    setor: Mapped[str | None] = mapped_column(String(100))
    tamanho: Mapped[str | None] = mapped_column(String(50))
    score: Mapped[int | None] = mapped_column(Integer)
    analise_json: Mapped[dict | None] = mapped_column(JSONB)

    # ── Pipeline (status, origem) ────────────────────────────────
    como_conheceu: Mapped[str] = mapped_column(
        String(50), default="Outbound", server_default="Outbound"
    )
    status: Mapped[str] = mapped_column(
        String(50), default="🔵 Prospect", server_default="🔵 Prospect"
    )

    notas: Mapped[str | None] = mapped_column(Text)

    # ── Sincronização com Notion ─────────────────────────────────
    notion_page_id: Mapped[str | None] = mapped_column(String(50))
    notion_synced_at: Mapped[datetime | None] = mapped_column()


    socios: Mapped[list[Socio]] = relationship(
        back_populates="empresa",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    contatos: Mapped[list[Contato]] = relationship(
        back_populates="empresa",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        # Buscar empresas por estado/cidade vai acontecer MUITO
        # ("todas as empresas em SP", "filtrar São Paulo")
        Index("ix_empresas_estado", "estado"),
        Index("ix_empresas_cidade_estado", "cidade", "estado"),
        # Filtros por setor/tamanho são comuns em prospecção
        Index("ix_empresas_setor", "setor"),
        # Quem já foi pro Notion vs não foi
        Index("ix_empresas_notion_page_id", "notion_page_id"),
        Index("ix_empresas_score","score")
    )

    def __repr__(self) -> str:
        return f"<Empresa id={self.id} nome={self.nome!r} cnpj={self.cnpj}>"

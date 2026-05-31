from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Index, Numeric, String, Text,Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


if TYPE_CHECKING:
    from app.db.models.contato import Contato
    from app.db.models.socio import Socio


class Empresa(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "empresas"

    # ── Identidade ───────────────────────────────────────────────
    nome: Mapped[str] = mapped_column(String(500), nullable=False)
    razao_social: Mapped[Optional[str]] = mapped_column(String(500))


    cnpj: Mapped[Optional[str]] = mapped_column(String(14), unique=True)

    # ── Localização ──────────────────────────────────────────────
    cidade: Mapped[Optional[str]] = mapped_column(String(200))
    estado: Mapped[Optional[str]] = mapped_column(String(2))
    local: Mapped[Optional[str]] = mapped_column(Text)  # endereço completo

    # ── Presença digital ─────────────────────────────────────────
    site: Mapped[Optional[str]] = mapped_column(String(500))
    instagram: Mapped[Optional[str]] = mapped_column(String(300))
    facebook: Mapped[Optional[str]] = mapped_column(String(300))

    # ── Classificação ────────────────────────────────────────────
    capital_social: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    setor: Mapped[Optional[str]] = mapped_column(String(100))
    tamanho: Mapped[Optional[str]] = mapped_column(String(50))
    score: Mapped[Optional[int]] = mapped_column(Integer)
    analise_json: Mapped[Optional[dict]] = mapped_column(JSONB)

    # ── Pipeline (status, origem) ────────────────────────────────
    como_conheceu: Mapped[str] = mapped_column(
        String(50), default="Outbound", server_default="Outbound"
    )
    status: Mapped[str] = mapped_column(
        String(50), default="🔵 Prospect", server_default="🔵 Prospect"
    )

    notas: Mapped[Optional[str]] = mapped_column(Text)

    # ── Sincronização com Notion ─────────────────────────────────
    notion_page_id: Mapped[Optional[str]] = mapped_column(String(50))
    notion_synced_at: Mapped[Optional[datetime]] = mapped_column()


    socios: Mapped[List["Socio"]] = relationship(
        back_populates="empresa",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    contatos: Mapped[List["Contato"]] = relationship(
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
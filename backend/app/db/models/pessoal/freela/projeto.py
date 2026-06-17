from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.pessoal.freela.cliente import Cliente
    from app.db.models.pessoal.freela.proposta import Proposta


class Projeto(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """O projeto/vaga do cliente. Você COLA o texto (a IA nunca faz scraping).

    A IA destrincha em ``analise_json`` (fit score, red flags, ganchos) —
    espelha o ``analise_json`` da Empresa no Prospector.
    """

    __tablename__ = "pessoal_freela_projeto"

    plataforma_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("pessoal_freela_plataforma.id", ondelete="SET NULL"),
        nullable=True,
    )
    cliente_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("pessoal_freela_cliente.id", ondelete="SET NULL"),
        nullable=True,
    )

    titulo: Mapped[str] = mapped_column(String(400), nullable=False)
    descricao: Mapped[str] = mapped_column(Text, nullable=False)  # texto colado
    url: Mapped[str | None] = mapped_column(String(800))

    faixa_orcamento_min: Mapped[float | None] = mapped_column(Numeric(12, 2))
    faixa_orcamento_max: Mapped[float | None] = mapped_column(Numeric(12, 2))
    habilidades: Mapped[list | None] = mapped_column(JSONB)
    prazo_estimado: Mapped[str | None] = mapped_column(String(100))

    # analisando_propostas / selecionado / fechado (como o site mostra)
    status_no_site: Mapped[str | None] = mapped_column(String(50))
    n_propostas_concorrentes: Mapped[int | None] = mapped_column(Integer)
    n_interessados: Mapped[int | None] = mapped_column(Integer)

    coletado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # analise_json: {requisitos[], fit_score, red_flags[], sinais_cliente{},
    #   ganchos[], recomendacao, resumo}
    analise_json: Mapped[dict | None] = mapped_column(JSONB)

    cliente: Mapped[Cliente | None] = relationship(
        back_populates="projetos", lazy="selectin"
    )
    propostas: Mapped[list[Proposta]] = relationship(
        back_populates="projeto",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Projeto id={self.id} titulo={self.titulo!r}>"

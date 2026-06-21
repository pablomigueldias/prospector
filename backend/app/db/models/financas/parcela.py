from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, ForeignKey, Index, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import expression

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.financas.compra import Compra


class Parcela(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Uma parcela de uma compra. Mesmo conceito serve pra cartão (cai numa
    fatura) e pra boleto parcelado (sem fatura). ``valor_juros`` é quanto
    daquela parcela é juro."""

    __tablename__ = "parcelas"

    compra_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("financas.compras.id", ondelete="CASCADE"),
        nullable=False,
    )
    numero: Mapped[int] = mapped_column(Integer, nullable=False)        # 3 (de 12)
    total_parcelas: Mapped[int] = mapped_column(Integer, nullable=False)
    valor: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    tem_juros: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=expression.false()
    )
    valor_juros: Mapped[float] = mapped_column(
        Numeric(12, 2), nullable=False, default=0, server_default="0"
    )
    vencimento: Mapped[date] = mapped_column(Date, nullable=False)

    # Só pra parcelas de cartão; boleto fica nulo.
    fatura_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("financas.faturas.id", ondelete="SET NULL"),
        nullable=True,
    )

    compra: Mapped[Compra] = relationship(back_populates="parcelas")

    __table_args__ = (
        Index("ix_fin_parcelas_compra_id", "compra_id"),
        Index("ix_fin_parcelas_fatura_id", "fatura_id"),
        Index("ix_fin_parcelas_vencimento", "vencimento"),
        {"schema": "financas"},
    )

    def __repr__(self) -> str:
        return f"<Parcela {self.numero}/{self.total_parcelas} R${self.valor}>"

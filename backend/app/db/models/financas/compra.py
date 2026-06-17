from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.financas.parcela import Parcela


# Origem da compra parcelada — cartão (cai em faturas) ou boleto (sem fatura,
# ex.: reforma do condomínio 1/6). String, seguindo a convenção do projeto.
ORIGENS_COMPRA = ("cartao", "boleto")


class Compra(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Compra/compromisso parcelado: o pai que gera N parcelas.

    Generaliza o conceito de parcelamento pra cartão E boleto (Step 11). Para
    cartão, ``cartao_id`` aponta o cartão; para boleto fica nulo.
    """

    __tablename__ = "compras"

    usuario_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False
    )
    descricao: Mapped[str] = mapped_column(String(500), nullable=False)
    valor_total: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    total_parcelas: Mapped[int] = mapped_column(Integer, nullable=False)
    data_compra: Mapped[date] = mapped_column(Date, nullable=False)
    origem: Mapped[str] = mapped_column(
        String(20), nullable=False, default="cartao", server_default="cartao"
    )

    cartao_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("financas.cartoes.id", ondelete="SET NULL"),
        nullable=True,
    )
    categoria_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("financas.categorias.id", ondelete="SET NULL"),
        nullable=True,
    )
    # Quando a compra é a ocorrência mensal de uma recorrência no cartão
    # (ex.: assinatura). Liga pro mês não duplicar e pra rastrear o vínculo.
    recorrencia_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(
            "financas.recorrencias.id",
            ondelete="SET NULL",
            name="fk_fin_compras_recorrencia",
        ),
        nullable=True,
    )

    parcelas: Mapped[list[Parcela]] = relationship(
        back_populates="compra",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="Parcela.numero",
    )

    __table_args__ = (
        Index("ix_fin_compras_usuario_id", "usuario_id"),
        Index("ix_fin_compras_cartao_id", "cartao_id"),
        {"schema": "financas"},
    )

    def __repr__(self) -> str:
        return (
            f"<Compra id={self.id} {self.descricao!r} "
            f"{self.total_parcelas}x R${self.valor_total}>"
        )

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

TIPOS_CONSUMO = ("agua", "gas", "luz")


class LeituraConsumo(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Leitura de consumo (água/gás/luz) de um mês. O boleto do condomínio traz
    leitura atual/anterior/consumo; guardar permite ver a tendência no tempo."""

    __tablename__ = "leituras_consumo"

    usuario_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False
    )
    tipo: Mapped[str] = mapped_column(String(10), nullable=False)  # agua/gas/luz
    mes_referencia: Mapped[date] = mapped_column(Date, nullable=False)  # 1º dia do mês

    leitura_atual: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False)
    leitura_anterior: Mapped[float | None] = mapped_column(Numeric(12, 3))
    consumo: Mapped[float | None] = mapped_column(Numeric(12, 3))
    valor: Mapped[float | None] = mapped_column(Numeric(12, 2))

    # Boleto/transação que trouxe a leitura (preenchido pelo importador).
    transacao_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("financas.transacoes.id", ondelete="SET NULL"),
        nullable=True,
    )

    __table_args__ = (
        Index("ix_fin_leituras_usuario_tipo", "usuario_id", "tipo"),
        Index("ix_fin_leituras_mes", "mes_referencia"),
        {"schema": "financas"},
    )

    def __repr__(self) -> str:
        return f"<LeituraConsumo {self.tipo} {self.mes_referencia} consumo={self.consumo}>"

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Index, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

# String, seguindo a convenção do projeto.
STATUS_FATURA = ("aberta", "fechada", "paga")


class Fatura(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Fatura mensal de um cartão. valor_total é a soma das parcelas que caem
    nela. Uma só por (cartão, mês_referência)."""

    __tablename__ = "faturas"

    cartao_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("financas.cartoes.id", ondelete="CASCADE"),
        nullable=False,
    )
    mes_referencia: Mapped[date] = mapped_column(Date, nullable=False)  # 1º dia do mês
    valor_total: Mapped[float] = mapped_column(
        Numeric(12, 2), nullable=False, default=0, server_default="0"
    )
    vencimento: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="aberta", server_default="aberta"
    )

    # Despesa gerada ao pagar a fatura (move o saldo da conta). Liga a baixa da
    # fatura ao lançamento, pra ser reversível e aparecer no resumo do mês.
    transacao_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(
            "financas.transacoes.id",
            ondelete="SET NULL",
            name="fk_fin_faturas_transacao",
        ),
        nullable=True,
    )

    __table_args__ = (
        UniqueConstraint("cartao_id", "mes_referencia", name="uq_fin_faturas_cartao_mes"),
        Index("ix_fin_faturas_cartao_id", "cartao_id"),
        {"schema": "financas"},
    )

    def __repr__(self) -> str:
        return f"<Fatura cartao={self.cartao_id} mes={self.mes_referencia} R${self.valor_total}>"

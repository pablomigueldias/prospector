from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, Numeric
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.financas.transacao import Transacao


class TransacaoPagamento(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Forma de pagamento de uma transação (split).

    Uma transação pode ser paga por N contas: o mercado de R$ 125 sai R$ 80 do
    VR e R$ 45 do dinheiro → dois pagamentos. A soma dos pagamentos deve bater
    com o ``valor_total`` da transação (validado no service).
    """

    __tablename__ = "transacao_pagamentos"

    transacao_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("financas.transacoes.id", ondelete="CASCADE"),
        nullable=False,
    )
    conta_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("financas.contas.id"),
        nullable=False,
    )

    valor: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    transacao: Mapped["Transacao"] = relationship(back_populates="pagamentos")

    __table_args__ = (
        Index("ix_fin_transacao_pagamentos_transacao_id", "transacao_id"),
        Index("ix_fin_transacao_pagamentos_conta_id", "conta_id"),
        {"schema": "financas"},
    )

    def __repr__(self) -> str:
        return f"<TransacaoPagamento conta={self.conta_id} R${self.valor}>"

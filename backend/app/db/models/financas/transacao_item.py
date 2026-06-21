from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.financas.transacao import Transacao


class TransacaoItem(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Quebra de uma transação em subverbas (line item).

    É o que faz o boleto do condomínio funcionar: 1 transação de R$ 1.107,52
    com 7 itens, cada um numa subverba (gás, água, fundo de reserva...).
    """

    __tablename__ = "transacao_itens"

    transacao_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("financas.transacoes.id", ondelete="CASCADE"),
        nullable=False,
    )
    categoria_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("financas.categorias.id", ondelete="SET NULL"),
        nullable=True,
    )

    descricao: Mapped[str] = mapped_column(String(500), nullable=False)
    valor: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    transacao: Mapped[Transacao] = relationship(back_populates="itens")

    __table_args__ = (
        Index("ix_fin_transacao_itens_transacao_id", "transacao_id"),
        Index("ix_fin_transacao_itens_categoria_id", "categoria_id"),
        {"schema": "financas"},
    )

    def __repr__(self) -> str:
        return f"<TransacaoItem {self.descricao!r} R${self.valor}>"

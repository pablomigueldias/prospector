from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Date, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.financas.transacao_item import TransacaoItem
    from app.db.models.financas.transacao_pagamento import TransacaoPagamento


# String (não enum nativo), seguindo a convenção do projeto.
TIPOS_TRANSACAO = ("despesa", "receita", "transferencia")
STATUS_TRANSACAO = ("prevista", "paga", "atrasada")
ORIGENS_TRANSACAO = ("manual", "telegram", "importacao_boleto", "recorrencia")


class Transacao(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """O coração: um movimento de dinheiro (despesa/receita/transferência).

    Pode ser quebrada em ``itens`` (subverbas — caso do condomínio) e paga por
    N formas em ``pagamentos`` (split VR + dinheiro). O ``valor_total`` é a
    fonte da verdade; itens e pagamentos devem somar a ele (validado no service).
    """

    __tablename__ = "transacoes"

    usuario_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False
    )

    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    descricao: Mapped[str] = mapped_column(String(500), nullable=False)
    valor_total: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    data_competencia: Mapped[date] = mapped_column(Date, nullable=False)
    data_pagamento: Mapped[Optional[date]] = mapped_column(Date)

    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="prevista", server_default="prevista"
    )
    origem: Mapped[str] = mapped_column(
        String(30), nullable=False, default="manual", server_default="manual"
    )

    categoria_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("financas.categorias.id", ondelete="SET NULL"),
        nullable=True,
    )

    # FK ligada no step 12 (quando a tabela recorrencias existir). Por ora,
    # só a coluna nullable.
    recorrencia_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True
    )

    notas: Mapped[Optional[str]] = mapped_column(Text)

    # ── Quebra em subverbas e formas de pagamento ─────────────────────
    itens: Mapped[List["TransacaoItem"]] = relationship(
        back_populates="transacao",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    pagamentos: Mapped[List["TransacaoPagamento"]] = relationship(
        back_populates="transacao",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_fin_transacoes_usuario_id", "usuario_id"),
        Index("ix_fin_transacoes_competencia", "usuario_id", "data_competencia"),
        Index("ix_fin_transacoes_status", "status"),
        Index("ix_fin_transacoes_categoria_id", "categoria_id"),
        {"schema": "financas"},
    )

    def __repr__(self) -> str:
        return (
            f"<Transacao id={self.id} {self.tipo} "
            f"{self.descricao!r} R${self.valor_total}>"
        )

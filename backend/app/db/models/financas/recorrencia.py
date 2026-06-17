from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import expression

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

FREQUENCIAS = ("mensal",)  # por ora só mensal
# Como a recorrência é paga: numa conta (débito direto), no cartão (entra na
# fatura) ou por boleto (avulso). String, seguindo a convenção do projeto.
FORMAS_PAGAMENTO = ("conta", "cartao", "boleto")


class Recorrencia(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Despesa/receita fixa (aluguel, condomínio, Enel, salário). Um job gera
    as transações previstas do mês e marca atrasadas as que passam do
    vencimento sem pagamento."""

    __tablename__ = "recorrencias"

    usuario_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False
    )
    descricao: Mapped[str] = mapped_column(String(500), nullable=False)
    tipo: Mapped[str] = mapped_column(
        String(20), nullable=False, default="despesa", server_default="despesa"
    )
    valor_estimado: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    dia_vencimento: Mapped[int] = mapped_column(Integer, nullable=False)
    frequencia: Mapped[str] = mapped_column(
        String(20), nullable=False, default="mensal", server_default="mensal"
    )

    forma_pagamento: Mapped[str] = mapped_column(
        String(20), nullable=False, default="conta", server_default="conta"
    )

    categoria_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("financas.categorias.id", ondelete="SET NULL"),
        nullable=True,
    )
    conta_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("financas.contas.id", ondelete="SET NULL"),
        nullable=True,
    )
    # Cartão onde a recorrência é cobrada (quando forma_pagamento == "cartao").
    cartao_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("financas.cartoes.id", ondelete="SET NULL"),
        nullable=True,
    )

    ativa: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=expression.true()
    )

    __table_args__ = (
        Index("ix_fin_recorrencias_usuario_id", "usuario_id"),
        {"schema": "financas"},
    )

    def __repr__(self) -> str:
        return f"<Recorrencia id={self.id} {self.descricao!r} dia={self.dia_vencimento}>"

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Index, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import expression

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


# Tipos de conta — "onde o dinheiro mora". String (não enum nativo) seguindo
# a convenção do projeto (ver Empresa.status). cartao_credito é tratado à
# parte (faturas/parcelas), mas existe como conta pra fechar o saldo.
TIPOS_CONTA = (
    "corrente",
    "dinheiro",
    "vr",        # vale-refeição
    "va",        # vale-alimentação
    "reserva",   # dinheiro guardado (emergência, viagem...)
    "cartao_credito",
)


class Conta(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Onde o dinheiro mora: conta corrente, carteira, VR/VA, reserva, cartão.

    O ``saldo_atual`` é mantido pelo serviço de lançamento (não é trigger);
    nasce em 0 e é recalculado conforme as transações entram.
    """

    __tablename__ = "contas"

    # Multi-tenant leve: você e a Sandra são dois usuario_id distintos.
    # Por ora é só uma coluna UUID (sem FK/tabela usuarios) — integridade
    # referencial pode entrar depois.
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False
    )

    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    tipo: Mapped[str] = mapped_column(String(30), nullable=False)

    saldo_atual: Mapped[float] = mapped_column(
        Numeric(12, 2), nullable=False, default=0, server_default="0"
    )
    ativa: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=expression.true()
    )

    __table_args__ = (
        Index("ix_fin_contas_usuario_id", "usuario_id"),
        {"schema": "financas"},
    )

    def __repr__(self) -> str:
        return f"<Conta id={self.id} nome={self.nome!r} tipo={self.tipo}>"

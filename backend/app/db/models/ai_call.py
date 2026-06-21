from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base, UUIDPrimaryKeyMixin


class AiCall(Base, UUIDPrimaryKeyMixin):

    __tablename__ = "ai_calls"

    agente: Mapped[str] = mapped_column(
        String(50), default='desconhecido', server_default='desconecido'
    )

    operacao: Mapped[str | None] = mapped_column(String(100))

    provider: Mapped[str] = mapped_column(String(50))
    modelo: Mapped[str] = mapped_column(String(100))

    # Payload

    prompt: Mapped[str | None] = mapped_column(Text)
    resposta: Mapped[str | None] = mapped_column(Text)
    prompt_chars: Mapped[int | None] = mapped_column(Integer)
    resposta_chars: Mapped[int | None] = mapped_column(Integer)

    # Custo

    tokens_input: Mapped[int | None] = mapped_column(Integer)
    tokens_output: Mapped[int | None] = mapped_column(Integer)
    tokens_total: Mapped[int | None] = mapped_column(Integer)
    custo_usd: Mapped[float | None] = mapped_column(Numeric(12, 6))

    # Resultados

    latencia_ms: Mapped[int | None] = mapped_column(Integer)
    sucesso: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default='true', nullable=False
    )
    finish_reason: Mapped[str | None] = mapped_column(String(50))
    error_message: Mapped[str | None] = mapped_column(Text)

    empresa_cnpj: Mapped[str | None] = mapped_column(String(20))

    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index("ix_ai_calls_agente", "agente"),
        Index("ix_ai_calls_created_at", "created_at"),
        Index("ix_ai_calls_sucesso", "sucesso"),
        Index("ix_ai_calls_empresa_cnpj", "empresa_cnpj"),
    )

    def __repr__(self) -> str:
        return f"<AiCall {self.agente}/{self.operacao} ok={self.sucesso}>"

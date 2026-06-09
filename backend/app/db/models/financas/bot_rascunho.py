from __future__ import annotations

import uuid

from sqlalchemy import Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class BotRascunho(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Rascunho de transação interpretado pelo NLU, aguardando confirmação no
    Telegram. O id vai no callback_data dos botões; ao confirmar vira transação,
    ao cancelar é apagado."""

    __tablename__ = "bot_rascunhos"

    usuario_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False
    )
    chat_id: Mapped[str] = mapped_column(String(50), nullable=False)
    # payload = rascunho interpretado (tipo, valor, descricao, data, conta_id, categoria_id)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)

    __table_args__ = (
        Index("ix_fin_bot_rascunhos_usuario_id", "usuario_id"),
        {"schema": "financas"},
    )

    def __repr__(self) -> str:
        return f"<BotRascunho id={self.id} chat={self.chat_id}>"

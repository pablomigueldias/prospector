from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UUIDPrimaryKeyMixin


class Auditoria(Base, UUIDPrimaryKeyMixin):
    """Trilha de auditoria de eventos de segurança.

    ``usuario_id`` é UUID **sem FK** de propósito: a auditoria precisa sobreviver
    mesmo se o usuário for apagado. ``evento`` é uma string curta
    (login_ok, login_falha, logout, logout_all, senha_alterada, papel_alterado…).
    ``detalhe`` guarda contexto livre (ex.: email tentado, papéis mudados).
    """

    __tablename__ = "auditoria"

    usuario_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True
    )
    evento: Mapped[str] = mapped_column(String(50), nullable=False)
    ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(400), nullable=True)
    detalhe: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index("ix_auth_auditoria_usuario_created", "usuario_id", "created_at"),
        Index("ix_auth_auditoria_evento_created", "evento", "created_at"),
        {"schema": "auth"},
    )

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UsuarioPapel(Base):
    """N:N usuário ↔ papel."""

    __tablename__ = "usuario_papeis"

    usuario_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("auth.usuarios.id", ondelete="CASCADE", name="fk_auth_usuario_papeis_usuario"),
        primary_key=True,
    )
    papel_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("auth.papeis.id", ondelete="CASCADE", name="fk_auth_usuario_papeis_papel"),
        primary_key=True,
    )

    __table_args__ = ({"schema": "auth"},)

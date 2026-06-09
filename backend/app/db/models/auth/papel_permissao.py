from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PapelPermissao(Base):
    """N:N papel ↔ permissão."""

    __tablename__ = "papel_permissoes"

    papel_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("auth.papeis.id", ondelete="CASCADE", name="fk_auth_papel_permissoes_papel"),
        primary_key=True,
    )
    permissao_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("auth.permissoes.id", ondelete="CASCADE", name="fk_auth_papel_permissoes_permissao"),
        primary_key=True,
    )

    __table_args__ = ({"schema": "auth"},)

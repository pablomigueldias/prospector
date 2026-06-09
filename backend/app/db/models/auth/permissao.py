from __future__ import annotations

from typing import Optional

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Permissao(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Permissão nomeada. Ex.: "pessoal.ver", "financas.editar"."""

    __tablename__ = "permissoes"

    codigo: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    descricao: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    __table_args__ = ({"schema": "auth"},)

    def __repr__(self) -> str:
        return f"<Permissao codigo={self.codigo!r}>"

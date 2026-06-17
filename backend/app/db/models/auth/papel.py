from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Papel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Papel (role): um conjunto de permissões. Ex.: "admin", "padrao"."""

    __tablename__ = "papeis"

    nome: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    descricao: Mapped[str | None] = mapped_column(String(255), nullable=True)

    __table_args__ = ({"schema": "auth"},)

    def __repr__(self) -> str:
        return f"<Papel nome={self.nome!r}>"

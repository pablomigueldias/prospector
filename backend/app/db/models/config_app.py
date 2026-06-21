from __future__ import annotations

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ConfigApp(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Override de uma `Settings` feito pela UI (S3 — self-service).

    Guarda só o que o Pablo mudou na tela; o metadado (tipo, categoria, label,
    default) vive no CATÁLOGO curado em `config_service` — porque nem toda
    setting pode/deve ser editável (segredos e infra ficam de fora). O valor é
    texto e o `config_service` o converte conforme o tipo da chave.
    """

    __tablename__ = "config_app"

    chave: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    valor: Mapped[str] = mapped_column(Text(), nullable=False)

    def __repr__(self) -> str:
        return f"<ConfigApp {self.chave}={self.valor!r}>"

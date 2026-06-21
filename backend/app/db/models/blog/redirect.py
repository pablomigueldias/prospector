from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class BlogRedirect(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Histórico de slug → 301 permanente. Renomear um post publicado sem isso
    quebra a URL antiga (404) e queima o ranking conquistado no Google. O site
    consulta este mapa e emite o redirect.
    """

    __tablename__ = "blog_redirect"

    slug_antigo: Mapped[str] = mapped_column(
        String(160), unique=True, index=True, nullable=False
    )
    slug_novo: Mapped[str] = mapped_column(String(160), nullable=False)

    def __repr__(self) -> str:
        return f"<BlogRedirect {self.slug_antigo!r} -> {self.slug_novo!r}>"

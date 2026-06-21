from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

# Ciclo da pauta: ideia (no backlog) → escolhida (vai escrever) → escrita
# (virou post) / descartada.
STATUS_PAUTA = ("ideia", "escolhida", "escrita", "descartada")

# De onde a pauta veio (motor de 3 fontes — B3).
FONTE_PAUTA = ("projeto", "seo", "tendencia", "manual")


class BlogPauta(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Ideia de post no backlog editorial. O motor de pauta gera/ranqueia;
    o Pablo escolhe e manda pro redator (B2). Entidade própria — uma pauta tem
    ciclo de vida diferente do post (pode nunca virar post)."""

    __tablename__ = "blog_pauta"

    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    resumo: Mapped[str | None] = mapped_column(Text)  # ângulo/por que vale
    keyword_alvo: Mapped[str | None] = mapped_column(String(120))
    intencao: Mapped[str | None] = mapped_column(String(20))  # informacional|comercial|navegacional
    publico: Mapped[str | None] = mapped_column(String(20))   # recrutador|cliente
    estagio_funil: Mapped[str | None] = mapped_column(String(10))  # topo|meio|fundo

    fonte: Mapped[str] = mapped_column(
        String(20), default="manual", server_default="manual", nullable=False
    )
    # Prioridade 0-100 (impacto×esforço, dado pelo motor) — ordena o backlog.
    score: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20), default="ideia", server_default="ideia", nullable=False, index=True
    )
    notas: Mapped[str | None] = mapped_column(Text)

    # Se a pauta virou post, aponta pra ele (SET NULL se o post for apagado).
    post_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("blog_post.id", ondelete="SET NULL"),
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<BlogPauta {self.titulo!r} status={self.status} score={self.score}>"

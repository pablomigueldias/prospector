from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

# Ciclo de vida do post. A transição é humana (checkpoint): a IA escreve e PARA
# em "rascunho"; o Pablo aprova → "publicado" (seta published_at). "arquivado"
# tira do ar sem apagar (mantém URL pra eventual 301 via blog_redirect).
STATUS_POST = (
    "rascunho",
    "aprovado",
    "publicado",
    "arquivado",
)

# Origem da pauta — pra medir o que converte (motor de pauta de 3 fontes, B3).
FONTE_POST = ("projeto", "seo", "tendencia", "brief")


class BlogPost(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Post do blog headless da Reative. O studio é a fonte; o site
    (`reativesystems.com.br`) consome via API pública e renderiza por ISR.

    Modelo já nasce "completo" (campos pro JSON-LD/SEO, agendamento, i18n)
    pra não exigir migração quando o agente de IA e o motor de pauta entrarem.
    """

    __tablename__ = "blog_post"

    # ── Identidade / conteúdo ────────────────────────────────────
    slug: Mapped[str] = mapped_column(String(160), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    excerpt: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(String(60))
    body_md: Mapped[str | None] = mapped_column(Text)
    # Sumário/âncoras: [{"id": "sinal-1", "label": "1. ..."}]
    toc: Mapped[list | None] = mapped_column(JSONB)

    # ── Capa / imagens ───────────────────────────────────────────
    cover_url: Mapped[str | None] = mapped_column(String(500))
    cover_alt: Mapped[str | None] = mapped_column(String(255))
    # Fallback p/ migração do site (que hoje usa classe CSS "post-cover-N").
    cover_class: Mapped[str | None] = mapped_column(String(60))
    # Assets gerados/editados: [{"papel": "cover|secao", "url", "origem":
    # "gerada|editada", "prompt", "alt"}]
    imagens: Mapped[list | None] = mapped_column(JSONB)

    # ── Estado / autoria / i18n ──────────────────────────────────
    status: Mapped[str] = mapped_column(
        String(20), default="rascunho", server_default="rascunho", nullable=False, index=True
    )
    author: Mapped[str] = mapped_column(
        String(120), default="Pablo Dias", server_default="Pablo Dias", nullable=False
    )
    lang: Mapped[str] = mapped_column(
        String(10), default="pt-BR", server_default="pt-BR", nullable=False
    )
    tags: Mapped[list | None] = mapped_column(JSONB)

    # ── Métricas de leitura (computadas no save) ─────────────────
    reading_time: Mapped[int | None] = mapped_column(Integer)  # minutos
    word_count: Mapped[int | None] = mapped_column(Integer)

    # ── SEO ──────────────────────────────────────────────────────
    noindex: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )
    meta_description: Mapped[str | None] = mapped_column(String(200))
    keyword_alvo: Mapped[str | None] = mapped_column(String(120))
    keywords: Mapped[list | None] = mapped_column(JSONB)
    og_image: Mapped[str | None] = mapped_column(String(500))
    og_title: Mapped[str | None] = mapped_column(String(200))
    og_description: Mapped[str | None] = mapped_column(String(300))

    # ── Proveniência / agendamento ───────────────────────────────
    fonte: Mapped[str | None] = mapped_column(String(20))
    # Gate de visibilidade: público só vê publicado E published_at <= now().
    # No futuro = agendamento (o cron publica quando a hora chega).
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), index=True
    )

    def __repr__(self) -> str:
        return f"<BlogPost slug={self.slug!r} status={self.status}>"

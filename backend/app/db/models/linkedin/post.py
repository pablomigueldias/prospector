from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

# Ciclo de vida do post. A transição é humana (checkpoint): o agente escreve e
# PARA em "rascunho"; o Pablo aprova → "publicado" (carimba published_at, que
# aqui = "Pablo registrou que postou no LinkedIn na mão"). "arquivado" guarda
# sem apagar. NÃO auto-postamos no LinkedIn (API oficial exige app aprovado).
STATUS_LINKEDIN = (
    "rascunho",
    "aprovado",
    "publicado",
    "arquivado",
)

# Onde o post vai: a Página da Reative (institucional/serviço) ou o perfil
# pessoal do Pablo (1ª pessoa, autoridade técnica, recrutador). Muda o tom.
CONTA_LINKEDIN = ("reative", "pessoal")

# De onde o conteúdo veio (cross-agent + motor autônomo).
FONTE_LINKEDIN = ("blog", "projeto", "tendencia", "manual")

# Formato do post — orienta a redação (texto curto, roteiro de carrossel…).
FORMATO_LINKEDIN = ("post", "carrossel", "artigo")


class LinkedinPost(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Post de LinkedIn gerado pelo agente de presença da Reative.

    *Para no rascunho*: o agente vai sozinho até deixar o post pronto na fila +
    calendário; o Pablo revisa e copia/cola no LinkedIn (não auto-postamos). Um
    só modelo serve às duas contas (Página Reative e perfil pessoal) via `conta`.
    """

    __tablename__ = "linkedin_post"

    # ── Identidade / organização ─────────────────────────────────
    # Rótulo interno pra achar o post na lista/calendário (não vai pro LinkedIn).
    titulo: Mapped[str | None] = mapped_column(String(200))
    conta: Mapped[str] = mapped_column(
        String(10), default="reative", server_default="reative", nullable=False, index=True
    )
    formato: Mapped[str] = mapped_column(
        String(12), default="post", server_default="post", nullable=False
    )

    # ── Conteúdo (o que o Pablo copia pro LinkedIn) ──────────────
    hook: Mapped[str | None] = mapped_column(Text)   # 1ª linha que prende
    body: Mapped[str | None] = mapped_column(Text)   # corpo escaneável
    cta: Mapped[str | None] = mapped_column(Text)    # chamada pra ação
    hashtags: Mapped[list | None] = mapped_column(JSONB)

    # ── Estado / proveniência ────────────────────────────────────
    status: Mapped[str] = mapped_column(
        String(20), default="rascunho", server_default="rascunho", nullable=False, index=True
    )
    fonte: Mapped[str] = mapped_column(
        String(20), default="manual", server_default="manual", nullable=False
    )
    # Se nasceu de um post de blog (cross-agent B5), aponta pra ele.
    origem_blog_post_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("blog_post.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ── Calendário editorial / publicação ────────────────────────
    # Quando o post está agendado pra sair (slot do calendário). Não publica
    # sozinho — é só organização da fila.
    scheduled_for: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), index=True
    )
    # Carimbo de quando o Pablo marcou como publicado (postou na mão).
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # ── Direção de arte / mídia (L5) ─────────────────────────────
    # Recomendação do agente (social media pro): tipo de mídia, roteiro, prompt
    # de imagem etc. — ver schema MidiaSugestao.
    midia: Mapped[dict | None] = mapped_column(JSONB)
    # Imagens geradas/anexadas: [{"url", "alt", "prompt", "origem": "ia|upload"}].
    imagens: Mapped[list | None] = mapped_column(JSONB)

    # ── Métricas / notas ─────────────────────────────────────────
    char_count: Mapped[int | None] = mapped_column(Integer)  # tamanho do texto
    notas: Mapped[str | None] = mapped_column(Text)

    def __repr__(self) -> str:
        return f"<LinkedinPost titulo={self.titulo!r} conta={self.conta} status={self.status}>"

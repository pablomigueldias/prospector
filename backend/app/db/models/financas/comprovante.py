from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

TIPOS_COMPROVANTE = ("boleto", "comprovante", "nota_fiscal")

# tipo → bucket no MinIO
BUCKET_POR_TIPO = {
    "boleto": "boletos",
    "comprovante": "comprovantes",
    "nota_fiscal": "notas",
}


class Comprovante(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Arquivo (boleto/comprovante/nota) guardado no MinIO e vinculado a uma
    transação. ``extraido_json`` guarda o que o LLM leu do arquivo (Step 16)."""

    __tablename__ = "comprovantes"

    usuario_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False
    )
    # Nullable: no importador o arquivo chega antes da transação existir.
    transacao_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("financas.transacoes.id", ondelete="CASCADE"),
        nullable=True,
    )

    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    bucket: Mapped[str] = mapped_column(String(63), nullable=False)
    arquivo_path: Mapped[str] = mapped_column(String(500), nullable=False)  # key no bucket

    nome_original: Mapped[str | None] = mapped_column(String(500))
    content_type: Mapped[str | None] = mapped_column(String(150))
    tamanho: Mapped[int | None] = mapped_column(Integer)
    hash: Mapped[str] = mapped_column(String(64), nullable=False)  # sha256, dedup

    extraido_json: Mapped[dict | None] = mapped_column(JSONB)

    __table_args__ = (
        Index("ix_fin_comprovantes_usuario_id", "usuario_id"),
        Index("ix_fin_comprovantes_transacao_id", "transacao_id"),
        Index("ix_fin_comprovantes_hash", "hash"),
        {"schema": "financas"},
    )

    def __repr__(self) -> str:
        return f"<Comprovante {self.tipo} {self.bucket}/{self.arquivo_path}>"

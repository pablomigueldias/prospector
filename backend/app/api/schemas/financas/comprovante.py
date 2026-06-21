"""Comprovantes (arquivos no MinIO) — schemas do domínio financas."""
from __future__ import annotations

from pydantic import BaseModel

# ══════════════════════════════════════════════════════════════════
# Comprovantes (arquivos no MinIO)
# ══════════════════════════════════════════════════════════════════

class ComprovanteResponse(BaseModel):
    id: str
    usuario_id: str
    transacao_id: str | None = None
    tipo: str
    bucket: str
    arquivo_path: str
    nome_original: str | None = None
    content_type: str | None = None
    tamanho: int | None = None
    hash: str
    url: str | None = None        # presigned, preenchida sob demanda
    created_at: str | None = None
    updated_at: str | None = None


class ComprovanteListResponse(BaseModel):
    items: list[ComprovanteResponse]
    total: int



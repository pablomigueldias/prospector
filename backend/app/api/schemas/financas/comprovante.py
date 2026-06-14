"""Comprovantes (arquivos no MinIO) — schemas do domínio financas."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field


# ══════════════════════════════════════════════════════════════════
# Comprovantes (arquivos no MinIO)
# ══════════════════════════════════════════════════════════════════

class ComprovanteResponse(BaseModel):
    id: str
    usuario_id: str
    transacao_id: Optional[str] = None
    tipo: str
    bucket: str
    arquivo_path: str
    nome_original: Optional[str] = None
    content_type: Optional[str] = None
    tamanho: Optional[int] = None
    hash: str
    url: Optional[str] = None        # presigned, preenchida sob demanda
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ComprovanteListResponse(BaseModel):
    items: List[ComprovanteResponse]
    total: int



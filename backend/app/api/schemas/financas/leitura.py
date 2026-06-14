"""Leituras de consumo (água/gás/luz) — schemas do domínio financas."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field


# ══════════════════════════════════════════════════════════════════
# Leituras de consumo (água/gás/luz)
# ══════════════════════════════════════════════════════════════════

class LeituraConsumoCreate(BaseModel):
    usuario_id: str
    tipo: str = Field(..., description="agua/gas/luz")
    mes_referencia: date
    leitura_atual: Decimal
    leitura_anterior: Optional[Decimal] = None
    consumo: Optional[Decimal] = Field(
        None, description="Se omitido, calcula atual − anterior"
    )
    valor: Optional[Decimal] = None
    transacao_id: Optional[str] = None


class LeituraConsumoResponse(BaseModel):
    id: str
    usuario_id: str
    tipo: str
    mes_referencia: date
    leitura_atual: Decimal
    leitura_anterior: Optional[Decimal] = None
    consumo: Optional[Decimal] = None
    valor: Optional[Decimal] = None
    transacao_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class LeituraConsumoListResponse(BaseModel):
    items: List[LeituraConsumoResponse]
    total: int



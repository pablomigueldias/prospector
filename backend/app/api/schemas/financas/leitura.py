"""Leituras de consumo (água/gás/luz) — schemas do domínio financas."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field

# ══════════════════════════════════════════════════════════════════
# Leituras de consumo (água/gás/luz)
# ══════════════════════════════════════════════════════════════════

class LeituraConsumoCreate(BaseModel):
    usuario_id: str
    tipo: str = Field(..., description="agua/gas/luz")
    mes_referencia: date
    leitura_atual: Decimal
    leitura_anterior: Decimal | None = None
    consumo: Decimal | None = Field(
        None, description="Se omitido, calcula atual − anterior"
    )
    valor: Decimal | None = None
    transacao_id: str | None = None


class LeituraConsumoResponse(BaseModel):
    id: str
    usuario_id: str
    tipo: str
    mes_referencia: date
    leitura_atual: Decimal
    leitura_anterior: Decimal | None = None
    consumo: Decimal | None = None
    valor: Decimal | None = None
    transacao_id: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class LeituraConsumoListResponse(BaseModel):
    items: list[LeituraConsumoResponse]
    total: int



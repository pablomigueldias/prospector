"""Orçamento por categoria (teto mensal) — schemas do domínio financas."""
from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field

# ══════════════════════════════════════════════════════════════════
# Orçamento por categoria (teto mensal)
# ══════════════════════════════════════════════════════════════════

class OrcamentoCreate(BaseModel):
    usuario_id: str
    categoria_id: str
    valor_mensal: Decimal = Field(..., gt=0)


class OrcamentoUpdate(BaseModel):
    valor_mensal: Decimal | None = Field(None, gt=0)
    ativo: bool | None = None


class OrcamentoResponse(BaseModel):
    id: str
    usuario_id: str
    categoria_id: str
    categoria_nome: str | None = None
    valor_mensal: Decimal
    ativo: bool
    created_at: str | None = None
    updated_at: str | None = None


class OrcamentoListResponse(BaseModel):
    items: list[OrcamentoResponse]
    total: int


class OrcamentoStatusItem(BaseModel):
    """Quanto de um orçamento já foi consumido no mês."""
    orcamento_id: str
    categoria_id: str
    categoria_nome: str | None = None
    valor_mensal: Decimal
    consumido: Decimal
    restante: Decimal           # valor_mensal − consumido (pode ser negativo)
    percentual: float           # 0..100+ (consumido/valor_mensal)


class OrcamentoStatusResponse(BaseModel):
    competencia: str            # "YYYY-MM"
    items: list[OrcamentoStatusItem]
    total_orcado: Decimal
    total_consumido: Decimal



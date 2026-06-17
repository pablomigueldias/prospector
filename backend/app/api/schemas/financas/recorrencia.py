"""Recorrências (despesas/receitas fixas) — schemas do domínio financas."""
from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field

# ══════════════════════════════════════════════════════════════════
# Recorrências (despesas/receitas fixas)
# ══════════════════════════════════════════════════════════════════

class RecorrenciaCreate(BaseModel):
    usuario_id: str
    descricao: str
    tipo: str = Field("despesa", description="despesa/receita")
    valor_estimado: Decimal = Field(..., gt=0)
    dia_vencimento: int = Field(..., ge=1, le=31)
    categoria_id: str | None = None
    conta_id: str | None = None
    forma_pagamento: str = Field("conta", description="conta/cartao/boleto")
    cartao_id: str | None = None
    frequencia: str = "mensal"


class RecorrenciaUpdate(BaseModel):
    descricao: str | None = None
    tipo: str | None = None
    valor_estimado: Decimal | None = Field(None, gt=0)
    dia_vencimento: int | None = Field(None, ge=1, le=31)
    categoria_id: str | None = None
    conta_id: str | None = None
    forma_pagamento: str | None = None
    cartao_id: str | None = None
    ativa: bool | None = None


class RecorrenciaResponse(BaseModel):
    id: str
    usuario_id: str
    descricao: str
    tipo: str
    valor_estimado: Decimal
    dia_vencimento: int
    frequencia: str
    categoria_id: str | None = None
    conta_id: str | None = None
    forma_pagamento: str = "conta"
    cartao_id: str | None = None
    ativa: bool
    created_at: str | None = None
    updated_at: str | None = None


class RecorrenciaListResponse(BaseModel):
    items: list[RecorrenciaResponse]
    total: int


class ProcessarRecorrenciasResponse(BaseModel):
    previstas_criadas: int
    marcadas_atrasadas: int



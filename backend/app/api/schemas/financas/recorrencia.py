"""Recorrências (despesas/receitas fixas) — schemas do domínio financas."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import List, Optional

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
    categoria_id: Optional[str] = None
    conta_id: Optional[str] = None
    forma_pagamento: str = Field("conta", description="conta/cartao/boleto")
    cartao_id: Optional[str] = None
    frequencia: str = "mensal"


class RecorrenciaUpdate(BaseModel):
    descricao: Optional[str] = None
    tipo: Optional[str] = None
    valor_estimado: Optional[Decimal] = Field(None, gt=0)
    dia_vencimento: Optional[int] = Field(None, ge=1, le=31)
    categoria_id: Optional[str] = None
    conta_id: Optional[str] = None
    forma_pagamento: Optional[str] = None
    cartao_id: Optional[str] = None
    ativa: Optional[bool] = None


class RecorrenciaResponse(BaseModel):
    id: str
    usuario_id: str
    descricao: str
    tipo: str
    valor_estimado: Decimal
    dia_vencimento: int
    frequencia: str
    categoria_id: Optional[str] = None
    conta_id: Optional[str] = None
    forma_pagamento: str = "conta"
    cartao_id: Optional[str] = None
    ativa: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class RecorrenciaListResponse(BaseModel):
    items: List[RecorrenciaResponse]
    total: int


class ProcessarRecorrenciasResponse(BaseModel):
    previstas_criadas: int
    marcadas_atrasadas: int



"""Pagar o mês (fatura + boletos) e status das recorrências — schemas do domínio financas."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field


# ══════════════════════════════════════════════════════════════════
# Pagar o mês (fatura do cartão + boletos do mês de uma vez)
# ══════════════════════════════════════════════════════════════════

class PagamentoMesItem(BaseModel):
    """Uma pendência do mês (boleto a pagar ou fatura de cartão)."""
    tipo: str                       # "boleto" | "fatura"
    id: str
    descricao: str
    valor: Decimal                  # já com encargos (boleto) até hoje
    vencimento: Optional[date] = None
    conta_sugerida_id: Optional[str] = None
    conta_sugerida_nome: Optional[str] = None


class PagamentoMesPreview(BaseModel):
    competencia: str                # "YYYY-MM"
    itens: List[PagamentoMesItem]
    total: Decimal


class PagamentoMesItemInput(BaseModel):
    tipo: str                       # "boleto" | "fatura"
    id: str
    conta_id: str


class PagamentoMesRequest(BaseModel):
    data_pagamento: Optional[date] = None
    itens: List[PagamentoMesItemInput] = Field(..., min_length=1)


class PagamentoMesResultado(BaseModel):
    pagos: int
    total_pago: Decimal
    falhas: List[str] = Field(default_factory=list)


class RecorrenciaStatusItem(BaseModel):
    """Situação de uma recorrência num mês específico."""
    recorrencia_id: str
    descricao: str
    forma_pagamento: str
    valor_estimado: Decimal
    dia_vencimento: int
    cartao_id: Optional[str] = None
    # do mês: "paga" | "prevista" | "atrasada" | "lancada_cartao" | "nenhuma"
    situacao: str
    transacao_id: Optional[str] = None
    compra_id: Optional[str] = None


class RecorrenciaStatusResponse(BaseModel):
    competencia: str  # "YYYY-MM"
    items: List[RecorrenciaStatusItem]


class PagarMesRequest(BaseModel):
    """Marca/lança a recorrência num mês (default = mês atual)."""
    competencia: Optional[str] = None  # "YYYY-MM"
    conta_id: Optional[str] = None
    data_pagamento: Optional[date] = None
    valor_pago: Optional[Decimal] = Field(None, gt=0)



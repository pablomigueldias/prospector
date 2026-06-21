"""Pagar o mês (fatura + boletos) e status das recorrências — schemas do domínio financas."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

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
    vencimento: date | None = None
    conta_sugerida_id: str | None = None
    conta_sugerida_nome: str | None = None


class PagamentoMesPreview(BaseModel):
    competencia: str                # "YYYY-MM"
    itens: list[PagamentoMesItem]
    total: Decimal


class PagamentoMesItemInput(BaseModel):
    tipo: str                       # "boleto" | "fatura"
    id: str
    conta_id: str


class PagamentoMesRequest(BaseModel):
    data_pagamento: date | None = None
    itens: list[PagamentoMesItemInput] = Field(..., min_length=1)


class PagamentoMesResultado(BaseModel):
    pagos: int
    total_pago: Decimal
    falhas: list[str] = Field(default_factory=list)


class RecorrenciaStatusItem(BaseModel):
    """Situação de uma recorrência num mês específico."""
    recorrencia_id: str
    descricao: str
    forma_pagamento: str
    valor_estimado: Decimal
    dia_vencimento: int
    cartao_id: str | None = None
    # do mês: "paga" | "prevista" | "atrasada" | "lancada_cartao" | "nenhuma"
    situacao: str
    transacao_id: str | None = None
    compra_id: str | None = None


class RecorrenciaStatusResponse(BaseModel):
    competencia: str  # "YYYY-MM"
    items: list[RecorrenciaStatusItem]


class PagarMesRequest(BaseModel):
    """Marca/lança a recorrência num mês (default = mês atual)."""
    competencia: str | None = None  # "YYYY-MM"
    conta_id: str | None = None
    data_pagamento: date | None = None
    valor_pago: Decimal | None = Field(None, gt=0)



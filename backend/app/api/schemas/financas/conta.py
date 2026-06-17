"""Contas e transferências — schemas do domínio financas."""
from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field

# ══════════════════════════════════════════════════════════════════
# Contas (onde o dinheiro mora)
# ══════════════════════════════════════════════════════════════════

class ContaCreate(BaseModel):
    usuario_id: str = Field(..., description="Perfil dono da conta (você/Sandra)")
    nome: str = Field(..., description='ex: "Nubank", "Carteira", "VR Caju"')
    tipo: str = Field(..., description="corrente/dinheiro/vr/va/reserva/cartao_credito")
    saldo_atual: Decimal = Field(
        Decimal("0"), description="Saldo inicial (de abertura). Default 0."
    )
    meta: Decimal | None = Field(
        None, description="Objetivo de valor (ex.: reserva 'viagem: 5000'). Null = sem meta."
    )


class ContaUpdate(BaseModel):
    nome: str | None = None
    tipo: str | None = None
    ativa: bool | None = None
    meta: Decimal | None = None


class ContaResponse(BaseModel):
    id: str
    usuario_id: str
    nome: str
    tipo: str
    saldo_atual: Decimal
    meta: Decimal | None = None
    ativa: bool
    created_at: str | None = None
    updated_at: str | None = None


class ContaListResponse(BaseModel):
    items: list[ContaResponse]
    total: int



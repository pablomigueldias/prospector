"""Schemas do Organizador Financeiro pessoal (domínio `financas`).

Isolado dos schemas da Reative (prospector/copywriter/outreach) e dos
pessoais (perfil/vagas).
"""
from __future__ import annotations

from decimal import Decimal
from typing import List, Optional

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


class ContaUpdate(BaseModel):
    nome: Optional[str] = None
    tipo: Optional[str] = None
    ativa: Optional[bool] = None


class ContaResponse(BaseModel):
    id: str
    usuario_id: str
    nome: str
    tipo: str
    saldo_atual: Decimal
    ativa: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ContaListResponse(BaseModel):
    items: List[ContaResponse]
    total: int

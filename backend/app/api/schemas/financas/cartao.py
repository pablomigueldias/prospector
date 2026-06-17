"""Cartões, faturas, compras parceladas, parcelas e PIX — schemas do domínio financas."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field

# ══════════════════════════════════════════════════════════════════
# Cartões, faturas, compras parceladas e parcelas
# ══════════════════════════════════════════════════════════════════

class CartaoCreate(BaseModel):
    usuario_id: str
    nome: str
    bandeira: str | None = None
    dia_fechamento: int = Field(..., ge=1, le=31)
    dia_vencimento: int = Field(..., ge=1, le=31)
    limite: Decimal | None = Field(None, ge=0)


class CartaoUpdate(BaseModel):
    nome: str | None = None
    bandeira: str | None = None
    dia_fechamento: int | None = Field(None, ge=1, le=31)
    dia_vencimento: int | None = Field(None, ge=1, le=31)
    limite: Decimal | None = Field(None, ge=0)
    ativo: bool | None = None


class CartaoResponse(BaseModel):
    id: str
    usuario_id: str
    nome: str
    bandeira: str | None = None
    dia_fechamento: int
    dia_vencimento: int
    limite: Decimal | None = None
    ativo: bool
    created_at: str | None = None
    updated_at: str | None = None


class CartaoListResponse(BaseModel):
    items: list[CartaoResponse]
    total: int


class FaturaResponse(BaseModel):
    id: str
    cartao_id: str
    mes_referencia: date
    valor_total: Decimal
    vencimento: date
    status: str


class FaturasCartaoResponse(BaseModel):
    cartao_id: str
    faturas: list[FaturaResponse]
    total_em_aberto: Decimal       # soma das faturas não pagas
    total_juros: Decimal           # soma de valor_juros das parcelas do cartão


class ProjecaoMesItem(BaseModel):
    """Quanto está comprometido em faturas de cartão num mês (todos os cartões
    somados)."""
    mes_referencia: date           # 1º dia do mês
    total: Decimal


class ProjecaoFaturasResponse(BaseModel):
    """Comprometido por mês nos próximos N meses, somando as faturas não pagas
    de todos os cartões do usuário."""
    meses: list[ProjecaoMesItem]
    total: Decimal                 # soma do período


class PagarFaturaRequest(BaseModel):
    """Pagamento de uma fatura: debita de uma conta e baixa a fatura."""
    conta_id: str
    data_pagamento: date | None = None
    valor_pago: Decimal | None = Field(
        None, gt=0, description="Valor real que saiu (default = total da fatura)"
    )
    categoria_id: str | None = None


class FaturaExtratoItem(BaseModel):
    """Uma parcela que compõe a fatura (com os dados da compra de origem)."""
    parcela_id: str
    compra_id: str
    descricao: str
    numero: int
    total_parcelas: int
    valor: Decimal
    valor_juros: Decimal
    vencimento: date
    categoria_id: str | None = None
    categoria_nome: str | None = None


class FaturaExtratoResponse(BaseModel):
    fatura: FaturaResponse
    cartao_nome: str
    itens: list[FaturaExtratoItem]
    total_juros: Decimal


class CompraParceladaCreate(BaseModel):
    """Compra no cartão parcelada em N vezes."""
    usuario_id: str
    cartao_id: str
    descricao: str
    valor_total: Decimal = Field(..., gt=0, description="Total a pagar (já com juros)")
    total_parcelas: int = Field(..., ge=1, le=120)
    data_compra: date | None = None
    categoria_id: str | None = None
    valor_juros_total: Decimal = Field(
        Decimal("0"), ge=0, description="Quanto do total é juro (distribuído nas parcelas)"
    )


class BoletoParceladoCreate(BaseModel):
    """Despesa parcelada em boleto (sem cartão/fatura), ex.: reforma do
    condomínio em 6x. As parcelas vencem mês a mês a partir de primeiro_vencimento."""
    usuario_id: str
    descricao: str
    valor_total: Decimal = Field(..., gt=0)
    total_parcelas: int = Field(..., ge=1, le=120)
    primeiro_vencimento: date
    categoria_id: str | None = None
    valor_juros_total: Decimal = Field(Decimal("0"), ge=0)


class ParcelaResponse(BaseModel):
    id: str
    numero: int
    total_parcelas: int
    valor: Decimal
    tem_juros: bool
    valor_juros: Decimal
    vencimento: date
    fatura_id: str | None = None


class CompraResponse(BaseModel):
    id: str
    usuario_id: str
    cartao_id: str | None = None
    descricao: str
    valor_total: Decimal
    total_parcelas: int
    data_compra: date
    origem: str
    categoria_id: str | None = None
    parcelas: list[ParcelaResponse] = Field(default_factory=list)
    created_at: str | None = None
    updated_at: str | None = None


class CompraCategoriaSugestao(BaseModel):
    """Categoria da última compra com a mesma descrição (auto-categoria do
    cartão). Vem nula quando não há histórico."""
    categoria_id: str | None = None
    categoria_nome: str | None = None


class PixParseRequest(BaseModel):
    """Código PIX copia-e-cola (BR Code) pra extrair valor/beneficiário."""
    codigo: str


class PixParseResponse(BaseModel):
    """Dados extraídos do PIX copia-e-cola (campos podem vir nulos)."""
    valor: Decimal | None = None
    beneficiario: str | None = None
    cidade: str | None = None
    chave: str | None = None



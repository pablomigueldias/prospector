"""Schemas do Organizador Financeiro pessoal (domínio `financas`).

Isolado dos schemas da Reative (prospector/copywriter/outreach) e dos
pessoais (perfil/vagas).
"""
from __future__ import annotations

from datetime import date
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


# ══════════════════════════════════════════════════════════════════
# Categorias (hierárquicas, compartilhadas)
# ══════════════════════════════════════════════════════════════════

class CategoriaCreate(BaseModel):
    nome: str
    categoria_pai_id: Optional[str] = Field(
        None, description="Pai na hierarquia. Null = categoria raiz."
    )


class CategoriaUpdate(BaseModel):
    nome: Optional[str] = None
    categoria_pai_id: Optional[str] = None
    ativa: Optional[bool] = None


class CategoriaResponse(BaseModel):
    id: str
    nome: str
    categoria_pai_id: Optional[str] = None
    ativa: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class CategoriaTreeItem(BaseModel):
    """Nó da árvore de categorias (pai com seus filhos aninhados)."""
    id: str
    nome: str
    ativa: bool
    filhos: List["CategoriaTreeItem"] = Field(default_factory=list)


class CategoriaTreeResponse(BaseModel):
    items: List[CategoriaTreeItem]   # raízes
    total: int                       # total de categorias (todos os níveis)


CategoriaTreeItem.model_rebuild()


# ══════════════════════════════════════════════════════════════════
# Transações
# ══════════════════════════════════════════════════════════════════

class DespesaCreate(BaseModel):
    """Lançamento de despesa simples (uma conta, uma categoria opcional)."""
    usuario_id: str
    descricao: str
    valor_total: Decimal = Field(..., gt=0)
    conta_id: str = Field(..., description="Conta de onde o dinheiro saiu")
    categoria_id: Optional[str] = None
    data_competencia: Optional[date] = Field(
        None, description="Mês de competência. Default: hoje."
    )
    data_pagamento: Optional[date] = Field(
        None, description="Quando saiu de fato. Default: hoje se status=paga."
    )
    status: str = Field("paga", description="prevista/paga/atrasada")
    notas: Optional[str] = None


class PagamentoIn(BaseModel):
    conta_id: str
    valor: Decimal = Field(..., gt=0)


class DespesaDivididaCreate(BaseModel):
    """Despesa paga por N contas (split explícito). A soma dos pagamentos
    precisa bater com valor_total."""
    usuario_id: str
    descricao: str
    valor_total: Decimal = Field(..., gt=0)
    pagamentos: List[PagamentoIn] = Field(..., min_length=1)
    categoria_id: Optional[str] = None
    data_competencia: Optional[date] = None
    data_pagamento: Optional[date] = None
    status: str = "paga"
    notas: Optional[str] = None


class DespesaAutoSplitCreate(BaseModel):
    """Despesa que esgota o VR/VA e joga o resto no dinheiro automaticamente.
    Resolve o 'às vezes acaba o VR'. Sempre lançada como paga."""
    usuario_id: str
    descricao: str
    valor_total: Decimal = Field(..., gt=0)
    conta_vr_id: str = Field(..., description="Conta que esgota primeiro (VR/VA)")
    conta_fallback_id: str = Field(..., description="Conta que cobre o resto (dinheiro)")
    categoria_id: Optional[str] = None
    data_competencia: Optional[date] = None
    notas: Optional[str] = None


class TransacaoItemResponse(BaseModel):
    id: str
    categoria_id: Optional[str] = None
    descricao: str
    valor: Decimal


class TransacaoPagamentoResponse(BaseModel):
    id: str
    conta_id: str
    valor: Decimal


class TransacaoResponse(BaseModel):
    id: str
    usuario_id: str
    tipo: str
    descricao: str
    valor_total: Decimal
    data_competencia: date
    data_pagamento: Optional[date] = None
    status: str
    origem: str
    categoria_id: Optional[str] = None
    notas: Optional[str] = None
    itens: List[TransacaoItemResponse] = Field(default_factory=list)
    pagamentos: List[TransacaoPagamentoResponse] = Field(default_factory=list)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# ══════════════════════════════════════════════════════════════════
# Resumo do mês
# ══════════════════════════════════════════════════════════════════

class CategoriaResumoItem(BaseModel):
    categoria_id: Optional[str] = None
    categoria_nome: str            # "Sem categoria" quando null
    total: Decimal


class ResumoMesResponse(BaseModel):
    ano: int
    mes: int
    total_receitas: Decimal
    total_despesas: Decimal
    saldo: Decimal                 # receitas − despesas (sobra/déficit)
    por_categoria: List[CategoriaResumoItem]   # despesas, maior → menor

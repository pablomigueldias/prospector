"""Resumo do mês, projeção e relatório — schemas do domínio financas."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field


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


class ProjecaoMesResponse(BaseModel):
    """Projeção de fim de mês: parte do saldo atual e desconta o que ainda há a
    pagar (previstas/atrasadas até o fim do mês), somando o a receber."""
    ano: int
    mes: int
    saldo_atual: Decimal           # soma das contas ativas hoje
    a_pagar: Decimal               # despesas não pagas com vencimento até o fim do mês
    a_receber: Decimal             # receitas previstas até o fim do mês
    estimativa_sobra: Decimal      # saldo_atual + a_receber − a_pagar


class RelatorioMesItem(BaseModel):
    """Um mês na série do relatório (cronológico, mais antigo → mais novo)."""
    ano: int
    mes: int
    total_receitas: Decimal
    total_despesas: Decimal
    saldo: Decimal                 # resultado do mês (receitas − despesas)


class RelatorioResponse(BaseModel):
    """Relatório do período (N meses até o mês âncora): série mês a mês,
    top categorias e totais consolidados."""
    meses: List[RelatorioMesItem]
    por_categoria: List[CategoriaResumoItem]   # despesas do período, maior → menor
    total_receitas: Decimal
    total_despesas: Decimal
    saldo: Decimal
    media_despesas: Decimal        # média mensal de despesa no período

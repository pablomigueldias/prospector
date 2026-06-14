"""Transações (despesa/receita/dividida/auto-split/editar/pagar/listar) — schemas do domínio financas."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field


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
    data_vencimento: Optional[date] = Field(
        None, description="Vencimento (pra prevista/agendada aparecer em 'A pagar')."
    )
    status: str = Field("paga", description="prevista/paga/atrasada")
    notas: Optional[str] = None


class TransferenciaCreate(BaseModel):
    """Move dinheiro entre contas (ex.: guardar na reserva). Debita a origem e
    credita o destino; não conta como receita/despesa no resumo do mês."""
    usuario_id: str
    origem_conta_id: str = Field(..., description="Conta de onde sai o dinheiro")
    destino_conta_id: str = Field(..., description="Conta que recebe (ex.: reserva)")
    valor: Decimal = Field(..., gt=0)
    descricao: Optional[str] = None
    data: Optional[date] = None


class TransferenciaResponse(BaseModel):
    origem_conta_id: str
    destino_conta_id: str
    valor: Decimal


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


class ReceitaCreate(BaseModel):
    """Lançamento de receita simples (entra dinheiro numa conta)."""
    usuario_id: str
    descricao: str
    valor_total: Decimal = Field(..., gt=0)
    conta_id: str = Field(..., description="Conta que recebeu o dinheiro")
    categoria_id: Optional[str] = None
    data_competencia: Optional[date] = None
    data_pagamento: Optional[date] = None
    status: str = Field("paga", description="prevista/paga/atrasada")
    notas: Optional[str] = None


class TransacaoUpdate(BaseModel):
    """Edição de uma transação simples (uma conta). Espelha o formulário do
    dashboard: tipo, descrição, valor, conta, categoria, data e status. O saldo
    da conta é reajustado (reverte o efeito antigo e aplica o novo)."""
    tipo: str = Field(..., description="despesa | receita")
    descricao: str
    valor_total: Decimal = Field(..., gt=0)
    conta_id: str = Field(..., description="Conta da transação")
    categoria_id: Optional[str] = None
    data_competencia: Optional[date] = None
    status: str = Field("paga", description="prevista/paga/atrasada")


class SugestaoContaResponse(BaseModel):
    """Conta sugerida pra pagar (última usada com o mesmo beneficiário)."""
    conta_id: Optional[str] = None
    conta_nome: Optional[str] = None


class ItemPrevistaInput(BaseModel):
    descricao: str
    valor: Decimal = Field(..., gt=0)


class PrevistaUpdate(BaseModel):
    """Edição de uma conta **a pagar** (prevista/atrasada) — sem mexer no saldo
    (ela ainda não foi paga). Permite detalhar/corrigir o que a IA importou do
    boleto: descrição, valor, categoria, vencimento, encargos e as verbas
    (itens). Se ``itens`` vier, substitui as verbas atuais."""
    descricao: str
    valor_total: Decimal = Field(..., gt=0)
    categoria_id: Optional[str] = None
    data_vencimento: Optional[date] = None
    multa_percentual: Optional[Decimal] = None
    juros_mensal_percentual: Optional[Decimal] = None
    itens: Optional[List[ItemPrevistaInput]] = None
    # Conta fixa (recorrência) à qual esta despesa pertence. Só altera quando o
    # campo é enviado (None envia = desvincular; ausente = mantém).
    recorrencia_id: Optional[str] = None


class PagarTransacaoRequest(BaseModel):
    """Quita uma transação prevista/atrasada (move o saldo). ``conta_id`` só é
    exigido quando a transação ainda não tem conta (boleto importado /
    recorrência); se já tem pagamento(s), efetiva nas contas existentes.

    ``multa_percentual``/``juros_mensal_percentual``: quando informados,
    sobrescrevem (e salvam) os encargos da transação — pra corrigir o que a IA
    leu ou preencher boletos antigos que não traziam essa informação."""
    conta_id: Optional[str] = None
    data_pagamento: Optional[date] = None
    multa_percentual: Optional[Decimal] = None
    juros_mensal_percentual: Optional[Decimal] = None
    # Valor realmente pago — sobrescreve o total calculado (valor + encargos).
    # Pra acordo/desconto/arredondamento; o saldo desce por esse valor.
    valor_pago: Optional[Decimal] = None


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
    data_vencimento: Optional[date] = None
    multa_percentual: Optional[Decimal] = None
    juros_mensal_percentual: Optional[Decimal] = None
    encargos_pagos: Optional[Decimal] = None
    linha_digitavel: Optional[str] = None
    desconto_valor: Optional[Decimal] = None
    desconto_ate: Optional[date] = None
    status: str
    origem: str
    categoria_id: Optional[str] = None
    recorrencia_id: Optional[str] = None
    notas: Optional[str] = None
    itens: List[TransacaoItemResponse] = Field(default_factory=list)
    pagamentos: List[TransacaoPagamentoResponse] = Field(default_factory=list)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class TransacaoListItem(BaseModel):
    """Linha enxuta para a lista filtrável do dashboard (sem itens/pagamentos
    completos — só os nomes das contas pagadoras e da categoria)."""
    id: str
    tipo: str
    descricao: str
    valor_total: Decimal
    data_competencia: date
    data_pagamento: Optional[date] = None
    data_vencimento: Optional[date] = None
    multa_percentual: Optional[Decimal] = None
    juros_mensal_percentual: Optional[Decimal] = None
    encargos_pagos: Optional[Decimal] = None
    linha_digitavel: Optional[str] = None
    desconto_valor: Optional[Decimal] = None
    desconto_ate: Optional[date] = None
    status: str
    categoria_id: Optional[str] = None
    categoria_nome: Optional[str] = None
    recorrencia_id: Optional[str] = None
    contas: List[str] = Field(default_factory=list)


class TransacaoListResponse(BaseModel):
    items: List[TransacaoListItem]
    total: int
    limit: int
    offset: int



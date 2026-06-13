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


class PagarTransacaoRequest(BaseModel):
    """Quita uma transação prevista/atrasada (move o saldo). ``conta_id`` só é
    exigido quando a transação ainda não tem conta (boleto importado /
    recorrência); se já tem pagamento(s), efetiva nas contas existentes."""
    conta_id: Optional[str] = None
    data_pagamento: Optional[date] = None


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
    status: str
    origem: str
    categoria_id: Optional[str] = None
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
    status: str
    categoria_id: Optional[str] = None
    categoria_nome: Optional[str] = None
    contas: List[str] = Field(default_factory=list)


class TransacaoListResponse(BaseModel):
    items: List[TransacaoListItem]
    total: int
    limit: int
    offset: int


# ══════════════════════════════════════════════════════════════════
# Cartões, faturas, compras parceladas e parcelas
# ══════════════════════════════════════════════════════════════════

class CartaoCreate(BaseModel):
    usuario_id: str
    nome: str
    bandeira: Optional[str] = None
    dia_fechamento: int = Field(..., ge=1, le=31)
    dia_vencimento: int = Field(..., ge=1, le=31)
    limite: Optional[Decimal] = Field(None, ge=0)


class CartaoUpdate(BaseModel):
    nome: Optional[str] = None
    bandeira: Optional[str] = None
    dia_fechamento: Optional[int] = Field(None, ge=1, le=31)
    dia_vencimento: Optional[int] = Field(None, ge=1, le=31)
    limite: Optional[Decimal] = Field(None, ge=0)
    ativo: Optional[bool] = None


class CartaoResponse(BaseModel):
    id: str
    usuario_id: str
    nome: str
    bandeira: Optional[str] = None
    dia_fechamento: int
    dia_vencimento: int
    limite: Optional[Decimal] = None
    ativo: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class CartaoListResponse(BaseModel):
    items: List["CartaoResponse"]
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
    faturas: List[FaturaResponse]
    total_em_aberto: Decimal       # soma das faturas não pagas
    total_juros: Decimal           # soma de valor_juros das parcelas do cartão


class CompraParceladaCreate(BaseModel):
    """Compra no cartão parcelada em N vezes."""
    usuario_id: str
    cartao_id: str
    descricao: str
    valor_total: Decimal = Field(..., gt=0, description="Total a pagar (já com juros)")
    total_parcelas: int = Field(..., ge=1, le=120)
    data_compra: Optional[date] = None
    categoria_id: Optional[str] = None
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
    categoria_id: Optional[str] = None
    valor_juros_total: Decimal = Field(Decimal("0"), ge=0)


class ParcelaResponse(BaseModel):
    id: str
    numero: int
    total_parcelas: int
    valor: Decimal
    tem_juros: bool
    valor_juros: Decimal
    vencimento: date
    fatura_id: Optional[str] = None


class CompraResponse(BaseModel):
    id: str
    usuario_id: str
    cartao_id: Optional[str] = None
    descricao: str
    valor_total: Decimal
    total_parcelas: int
    data_compra: date
    origem: str
    categoria_id: Optional[str] = None
    parcelas: List[ParcelaResponse] = Field(default_factory=list)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


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
    frequencia: str = "mensal"


class RecorrenciaUpdate(BaseModel):
    descricao: Optional[str] = None
    tipo: Optional[str] = None
    valor_estimado: Optional[Decimal] = Field(None, gt=0)
    dia_vencimento: Optional[int] = Field(None, ge=1, le=31)
    categoria_id: Optional[str] = None
    conta_id: Optional[str] = None
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
    ativa: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class RecorrenciaListResponse(BaseModel):
    items: List[RecorrenciaResponse]
    total: int


class ProcessarRecorrenciasResponse(BaseModel):
    previstas_criadas: int
    marcadas_atrasadas: int


# ══════════════════════════════════════════════════════════════════
# NLU do Telegram (texto livre → estrutura)
# ══════════════════════════════════════════════════════════════════

class NLUResult(BaseModel):
    """Saída crua do LLM ao interpretar o texto livre."""
    tipo: str                              # despesa/receita
    valor: Decimal
    descricao: str
    categoria: Optional[str] = None        # nome (o service resolve pro id)
    conta: Optional[str] = None            # nome (o service resolve pro id)
    data: Optional[date] = None


class InterpretarTextoRequest(BaseModel):
    usuario_id: str
    texto: str


class InterpretacaoResponse(BaseModel):
    """Rascunho interpretado — o usuário confirma antes de virar transação."""
    tipo: str
    valor: Decimal
    descricao: str
    data: date
    conta_id: Optional[str] = None
    conta_nome: Optional[str] = None
    categoria_id: Optional[str] = None
    categoria_nome: Optional[str] = None
    texto_original: str


# ══════════════════════════════════════════════════════════════════
# Importador de boleto (LLM multimodal)
# ══════════════════════════════════════════════════════════════════

class VerbaBoleto(BaseModel):
    descricao: str
    valor: Decimal


class LeituraBoleto(BaseModel):
    tipo: str                              # agua/gas/luz
    leitura_atual: Optional[Decimal] = None
    leitura_anterior: Optional[Decimal] = None
    consumo: Optional[Decimal] = None
    valor: Optional[Decimal] = None


class BoletoExtraido(BaseModel):
    beneficiario: Optional[str] = None
    vencimento: Optional[date] = None
    valor_total: Decimal
    verbas: List[VerbaBoleto] = Field(default_factory=list)
    leituras: List[LeituraBoleto] = Field(default_factory=list)


class ImportarBoletoResponse(BaseModel):
    success: bool                          # conseguiu ler o arquivo?
    conferido: bool                        # soma das verbas == total?
    mensagem: str
    comprovante_id: Optional[str] = None
    transacao_id: Optional[str] = None     # criada só quando conferido
    extraido: Optional[BoletoExtraido] = None


# ══════════════════════════════════════════════════════════════════
# Comprovantes (arquivos no MinIO)
# ══════════════════════════════════════════════════════════════════

class ComprovanteResponse(BaseModel):
    id: str
    usuario_id: str
    transacao_id: Optional[str] = None
    tipo: str
    bucket: str
    arquivo_path: str
    nome_original: Optional[str] = None
    content_type: Optional[str] = None
    tamanho: Optional[int] = None
    hash: str
    url: Optional[str] = None        # presigned, preenchida sob demanda
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ComprovanteListResponse(BaseModel):
    items: List[ComprovanteResponse]
    total: int


# ══════════════════════════════════════════════════════════════════
# Leituras de consumo (água/gás/luz)
# ══════════════════════════════════════════════════════════════════

class LeituraConsumoCreate(BaseModel):
    usuario_id: str
    tipo: str = Field(..., description="agua/gas/luz")
    mes_referencia: date
    leitura_atual: Decimal
    leitura_anterior: Optional[Decimal] = None
    consumo: Optional[Decimal] = Field(
        None, description="Se omitido, calcula atual − anterior"
    )
    valor: Optional[Decimal] = None
    transacao_id: Optional[str] = None


class LeituraConsumoResponse(BaseModel):
    id: str
    usuario_id: str
    tipo: str
    mes_referencia: date
    leitura_atual: Decimal
    leitura_anterior: Optional[Decimal] = None
    consumo: Optional[Decimal] = None
    valor: Optional[Decimal] = None
    transacao_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class LeituraConsumoListResponse(BaseModel):
    items: List[LeituraConsumoResponse]
    total: int


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

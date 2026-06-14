"""Importador de boleto (LLM multimodal) — schemas do domínio financas."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field


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
    # Linha digitável (com ou sem pontos/espaços — normalizada no service).
    linha_digitavel: Optional[str] = None
    # Encargos por atraso impressos no boleto (ex.: multa 2% + juros 1% a.m.).
    multa_percentual: Optional[Decimal] = None
    juros_mensal_percentual: Optional[Decimal] = None
    # Desconto por antecipação (ex.: "desconto de R$X até DD/MM").
    desconto_valor: Optional[Decimal] = None
    desconto_ate: Optional[date] = None
    verbas: List[VerbaBoleto] = Field(default_factory=list)
    leituras: List[LeituraBoleto] = Field(default_factory=list)


class ImportarBoletoResponse(BaseModel):
    success: bool                          # conseguiu ler o arquivo?
    conferido: bool                        # soma das verbas == total?
    duplicado: bool = False                # já existe um boleto igual lançado?
    mensagem: str
    comprovante_id: Optional[str] = None
    transacao_id: Optional[str] = None     # criada (ou a já existente, se duplicado)
    extraido: Optional[BoletoExtraido] = None



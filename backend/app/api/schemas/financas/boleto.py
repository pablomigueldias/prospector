"""Importador de boleto (LLM multimodal) — schemas do domínio financas."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field

# ══════════════════════════════════════════════════════════════════
# Importador de boleto (LLM multimodal)
# ══════════════════════════════════════════════════════════════════

class VerbaBoleto(BaseModel):
    descricao: str
    valor: Decimal


class LeituraBoleto(BaseModel):
    tipo: str                              # agua/gas/luz
    leitura_atual: Decimal | None = None
    leitura_anterior: Decimal | None = None
    consumo: Decimal | None = None
    valor: Decimal | None = None


class BoletoExtraido(BaseModel):
    beneficiario: str | None = None
    vencimento: date | None = None
    valor_total: Decimal
    # Linha digitável (com ou sem pontos/espaços — normalizada no service).
    linha_digitavel: str | None = None
    # Encargos por atraso impressos no boleto (ex.: multa 2% + juros 1% a.m.).
    multa_percentual: Decimal | None = None
    juros_mensal_percentual: Decimal | None = None
    # Desconto por antecipação (ex.: "desconto de R$X até DD/MM").
    desconto_valor: Decimal | None = None
    desconto_ate: date | None = None
    verbas: list[VerbaBoleto] = Field(default_factory=list)
    leituras: list[LeituraBoleto] = Field(default_factory=list)


class ImportarBoletoResponse(BaseModel):
    success: bool                          # conseguiu ler o arquivo?
    conferido: bool                        # soma das verbas == total?
    duplicado: bool = False                # já existe um boleto igual lançado?
    mensagem: str
    comprovante_id: str | None = None
    transacao_id: str | None = None     # criada (ou a já existente, se duplicado)
    extraido: BoletoExtraido | None = None



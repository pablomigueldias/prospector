"""Encargos por atraso de boleto: multa (uma vez) + juros de mora (por dia).

Padrão brasileiro: ao vencer, incide uma **multa** percentual única sobre o
valor e **juros de mora** mensais cobrados pró-rata por dia de atraso (juros
simples). Ex.: "multa de 2% + juros de 1% ao mês" → no 10º dia de atraso de um
boleto de R$100: multa 2,00 + juros 100·1%·(10/30) = 0,33 → encargos 2,33.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

CENTAVO = Decimal("0.01")


def calcular_encargos(
    valor: Decimal,
    vencimento: Optional[date],
    multa_percentual: Optional[Decimal],
    juros_mensal_percentual: Optional[Decimal],
    referencia: date,
) -> Decimal:
    """Multa + juros projetados sobre ``valor`` até ``referencia``.

    Retorna 0 se não há vencimento, não está atrasado, ou não há encargos.
    Juros mensais são convertidos linearmente pra diário (÷30)."""
    if vencimento is None or referencia <= vencimento:
        return Decimal("0")
    dias = (referencia - vencimento).days
    valor = Decimal(valor)
    total = Decimal("0")
    if multa_percentual:
        total += valor * Decimal(multa_percentual) / Decimal("100")
    if juros_mensal_percentual:
        total += (
            valor
            * Decimal(juros_mensal_percentual) / Decimal("100")
            * Decimal(dias) / Decimal("30")
        )
    return total.quantize(CENTAVO, rounding=ROUND_HALF_UP)

"""Cálculo de saldo das contas.

Estratégia incremental: ``saldo_atual`` nasce como saldo de abertura (no
create da conta) e cada transação *paga* ajusta o saldo dentro da mesma
transação de banco. Despesa diminui, receita aumenta.
"""
from __future__ import annotations

from decimal import Decimal

from app.db.models.financas.conta import Conta


def delta_por_tipo(tipo: str, valor: Decimal) -> Decimal:
    """Quanto o saldo da conta varia por um movimento de ``valor`` do ``tipo``.

    despesa → sai dinheiro (−); receita → entra (+). transferência é tratada
    à parte (dois lados), então aqui retorna 0.
    """
    if tipo == "despesa":
        return -Decimal(valor)
    if tipo == "receita":
        return Decimal(valor)
    return Decimal("0")


def aplicar_movimento(conta: Conta, tipo: str, valor: Decimal) -> None:
    """Aplica o movimento no saldo da conta (muta o objeto ORM)."""
    conta.saldo_atual = Decimal(conta.saldo_atual) + delta_por_tipo(tipo, valor)

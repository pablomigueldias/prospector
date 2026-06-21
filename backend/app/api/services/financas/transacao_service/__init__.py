"""Service de Transações — lançar/transferir/consultar/editar/pagar/excluir.

Era um arquivo-deus de ~788 linhas; foi quebrado por responsabilidade. Este
`__init__` re-exporta a API pública, então
`from ...transacao_service import X` e `transacao_service.X(...)` seguem válidos.
Os helpers privados e os imports compartilhados moram em `_base.py`.
"""
from __future__ import annotations

from ._base import TransacaoError
from .consultas import (
    get_transacao,
    listar_transacoes,
    sugerir_categoria,
    sugestao_conta_pagamento,
    ultima_transacao,
)
from .editar import editar_prevista, editar_transacao
from .excluir import excluir_transacao
from .lancar import (
    lancar_despesa,
    lancar_despesa_auto_split,
    lancar_despesa_dividida,
    lancar_receita,
)
from .pagar import pagar_transacao
from .transferir import transferir

__all__ = [
    "TransacaoError",
    "lancar_despesa",
    "lancar_receita",
    "lancar_despesa_dividida",
    "lancar_despesa_auto_split",
    "transferir",
    "sugestao_conta_pagamento",
    "sugerir_categoria",
    "get_transacao",
    "listar_transacoes",
    "ultima_transacao",
    "editar_transacao",
    "editar_prevista",
    "pagar_transacao",
    "excluir_transacao",
]

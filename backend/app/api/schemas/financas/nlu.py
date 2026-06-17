"""NLU do Telegram (texto livre → estrutura) — schemas do domínio financas."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel

# ══════════════════════════════════════════════════════════════════
# NLU do Telegram (texto livre → estrutura)
# ══════════════════════════════════════════════════════════════════

class NLUResult(BaseModel):
    """Saída crua do LLM ao interpretar o texto livre."""
    tipo: str                              # despesa/receita
    valor: Decimal
    descricao: str
    categoria: str | None = None        # nome (o service resolve pro id)
    conta: str | None = None            # nome (o service resolve pro id)
    data: date | None = None


class InterpretarTextoRequest(BaseModel):
    usuario_id: str
    texto: str


class InterpretacaoResponse(BaseModel):
    """Rascunho interpretado — o usuário confirma antes de virar transação."""
    tipo: str
    valor: Decimal
    descricao: str
    data: date
    conta_id: str | None = None
    conta_nome: str | None = None
    categoria_id: str | None = None
    categoria_nome: str | None = None
    texto_original: str



"""NLU do Telegram (texto livre → estrutura) — schemas do domínio financas."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field


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



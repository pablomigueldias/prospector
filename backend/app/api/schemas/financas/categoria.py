"""Categorias hierárquicas — schemas do domínio financas."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field


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



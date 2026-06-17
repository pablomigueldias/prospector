"""Categorias hierárquicas — schemas do domínio financas."""
from __future__ import annotations

from pydantic import BaseModel, Field

# ══════════════════════════════════════════════════════════════════
# Categorias (hierárquicas, compartilhadas)
# ══════════════════════════════════════════════════════════════════

class CategoriaCreate(BaseModel):
    nome: str
    categoria_pai_id: str | None = Field(
        None, description="Pai na hierarquia. Null = categoria raiz."
    )


class CategoriaUpdate(BaseModel):
    nome: str | None = None
    categoria_pai_id: str | None = None
    ativa: bool | None = None


class CategoriaResponse(BaseModel):
    id: str
    nome: str
    categoria_pai_id: str | None = None
    ativa: bool
    created_at: str | None = None
    updated_at: str | None = None


class CategoriaTreeItem(BaseModel):
    """Nó da árvore de categorias (pai com seus filhos aninhados)."""
    id: str
    nome: str
    ativa: bool
    filhos: list[CategoriaTreeItem] = Field(default_factory=list)


class CategoriaTreeResponse(BaseModel):
    items: list[CategoriaTreeItem]   # raízes
    total: int                       # total de categorias (todos os níveis)


CategoriaTreeItem.model_rebuild()



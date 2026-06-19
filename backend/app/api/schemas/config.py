"""Schemas do self-service de configurações (S3)."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ConfigItemOut(BaseModel):
    chave: str
    categoria: str
    label: str
    tipo: str  # bool | int | select
    ajuda: str
    opcoes: list[str]
    minimo: int | None
    maximo: int | None
    requer_restart: bool
    valor: Any  # valor efetivo atual
    default: Any
    sobrescrito: bool


class ConfigUpdate(BaseModel):
    """Mapa chave→novo valor. Só chaves do catálogo são aceitas."""

    mudancas: dict[str, Any]

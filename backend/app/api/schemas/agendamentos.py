"""Schemas dos agendamentos (S4)."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class JobOut(BaseModel):
    id: str
    nome: str
    descricao: str
    hora: int
    ligado: bool
    hora_key: str
    enabled_key: str


class JobRunResult(BaseModel):
    job: str
    executado_em: str
    resultado: dict[str, Any]

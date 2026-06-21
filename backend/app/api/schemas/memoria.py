"""Schemas da memória compartilhada do MAS (blackboard) — ver agente_evento."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class EventoOut(BaseModel):
    id: str
    agente: str
    alvo_tipo: str
    alvo_id: str
    tipo: str
    resumo: str | None = None
    payload: dict[str, Any] | None = None
    origem: str
    created_at: str


class EventoCreate(BaseModel):
    agente: str = "usuario"
    alvo_tipo: str
    alvo_id: str
    tipo: str = "nota"
    resumo: str | None = None
    payload: dict[str, Any] | None = None
    origem: str = "manual"


class TimelineResponse(BaseModel):
    alvo_tipo: str
    alvo_id: str
    eventos: list[EventoOut] = Field(default_factory=list)


class OutcomeCreate(BaseModel):
    alvo_tipo: str
    alvo_id: str
    resultado: str
    nota: str | None = None


class OutcomeResumo(BaseModel):
    total: int = 0
    positivos: int = 0
    negativos: int = 0
    taxa_positiva: float | None = None
    por_resultado: dict[str, int] = Field(default_factory=dict)
    por_alvo_tipo: dict[str, dict[str, int]] = Field(default_factory=dict)

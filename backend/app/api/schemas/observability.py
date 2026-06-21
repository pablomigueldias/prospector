"""Schemas da observabilidade de IA (S2)."""
from __future__ import annotations

from pydantic import BaseModel


class ObsTotais(BaseModel):
    chamadas: int
    falhas: int
    taxa_erro: float
    tokens: int
    custo_usd: float
    latencia_media_ms: int | None


class ObsPorAgente(BaseModel):
    agente: str
    chamadas: int
    falhas: int
    taxa_erro: float
    tokens: int
    custo_usd: float
    latencia_media_ms: int | None


class ObsPorDia(BaseModel):
    dia: str
    chamadas: int
    tokens: int
    custo_usd: float


class ObsChamada(BaseModel):
    created_at: str | None
    agente: str
    operacao: str | None
    provider: str
    modelo: str
    tokens_total: int | None
    custo_usd: float
    latencia_ms: int | None
    sucesso: bool
    error_message: str | None


class ObsResumo(BaseModel):
    periodo_dias: int
    totais: ObsTotais
    por_agente: list[ObsPorAgente]
    por_dia: list[ObsPorDia]
    ultimas: list[ObsChamada]

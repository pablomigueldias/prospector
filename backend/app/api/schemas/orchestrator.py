"""Schemas do coordenador (MAS-2). Ver app/orchestrator/ e docs/plano-agentes-autonomos.md."""
from __future__ import annotations

from pydantic import BaseModel, Field

from app.api.schemas.pessoal import (
    CartaCandidatura,
    CurriculoVaga,
    EmailCandidatura,
)


class CandidaturaAlvo(BaseModel):
    vaga_id: str


class CandidaturaAnalise(BaseModel):
    """Resultado da fase 1 (análise) — o que o checkpoint humano avalia."""
    vaga_id: str
    titulo: str | None = None
    empresa: str | None = None
    aderencia: int = 0
    match_score: int = 0
    veredito: str | None = None
    recomenda: bool = True
    gaps: list[str] = Field(default_factory=list)
    destaques: list[str] = Field(default_factory=list)
    resumo: str | None = None


class CandidaturaEntrega(BaseModel):
    """Resultado da fase 2 (preparação) — pronto pra revisar e enviar."""
    vaga_id: str
    curriculo: CurriculoVaga | None = None
    email: EmailCandidatura | None = None
    carta: CartaCandidatura | None = None
    checklist: list[str] = Field(default_factory=list)
    rascunho_id: str | None = None


# ── Briefing noturno (MAS-4) ─────────────────────────────────────────

class BriefingItem(BaseModel):
    total: int = 0
    exemplos: list[str] = Field(default_factory=list)


class Briefing(BaseModel):
    data: str
    vagas_triar: BriefingItem = Field(default_factory=BriefingItem)
    freela_followups: BriefingItem = Field(default_factory=BriefingItem)
    atividades_pendentes: int = 0
    atividades_atrasadas: int = 0
    micro_acao: str | None = None
    texto: str = ""

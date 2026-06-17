from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


class GerarRascunhosRequest(BaseModel):
    limit: Optional[int] = Field(None, description="Máx de rascunhos a gerar; None = todos pendentes")
    pausa: float = Field(8.0, description="Segundos entre cada rascunho")


class GerarRascunhosResponse(BaseModel):
    success: bool = True
    gerados: int
    falhas: int
    pulados: int


class SyncResponse(BaseModel):
    success: bool = True
    enviados_confirmados: int
    respostas_detectadas: int


class EmailItem(BaseModel):
    id: str
    destinatario: str
    assunto: str
    tom: Optional[str] = None
    status: str
    follow_up_num: int = 0
    draft_criado_em: Optional[str] = None
    enviado_em: Optional[str] = None
    primeira_resposta_em: Optional[str] = None


class EmailHistoryResponse(BaseModel):
    items: List[EmailItem]
    total: int

class GerarFollowupsRequest(BaseModel):
    dias: int = Field(3, description="Só faz follow-up de e-mails enviados há mais de X dias")
    max_followups: int = Field(2, description="Teto de toques por thread")
    limit: Optional[int] = Field(None, description="Máx de follow-ups a gerar; None = todos")
    pausa: float = Field(8.0, description="Segundos entre cada follow-up")


class GerarFollowupsResponse(BaseModel):
    success: bool = True
    gerados: int
    falhas: int

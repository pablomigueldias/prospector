from __future__ import annotations

from pydantic import BaseModel, Field


class GerarRascunhosRequest(BaseModel):
    limit: int | None = Field(None, description="Máx de rascunhos a gerar; None = todos pendentes")
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
    tom: str | None = None
    status: str
    follow_up_num: int = 0
    draft_criado_em: str | None = None
    enviado_em: str | None = None
    primeira_resposta_em: str | None = None


class EmailHistoryResponse(BaseModel):
    items: list[EmailItem]
    total: int

class GerarFollowupsRequest(BaseModel):
    dias: int = Field(3, description="Só faz follow-up de e-mails enviados há mais de X dias")
    max_followups: int = Field(2, description="Teto de toques por thread")
    limit: int | None = Field(None, description="Máx de follow-ups a gerar; None = todos")
    pausa: float = Field(8.0, description="Segundos entre cada follow-up")


class GerarFollowupsResponse(BaseModel):
    success: bool = True
    gerados: int
    falhas: int

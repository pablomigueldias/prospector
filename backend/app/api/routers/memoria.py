"""Memória compartilhada do MAS (blackboard) — linha do tempo por alvo."""
from fastapi import APIRouter

from app.api.schemas.memoria import (
    EventoCreate,
    EventoOut,
    OutcomeCreate,
    OutcomeResumo,
    TimelineResponse,
)
from app.api.services import memoria_service

router = APIRouter(prefix="/api/memoria", tags=["memoria"])


# ── Outcomes (MAS-3) — declarados ANTES do /{alvo_tipo}/{alvo_id} pra não colidir.
@router.get("/outcomes/resumo", response_model=OutcomeResumo,
            summary="Agregado dos resultados — o que tem dado retorno")
async def outcomes_resumo() -> OutcomeResumo:
    return OutcomeResumo(**await memoria_service.resumo_outcomes())


@router.get("/outcomes/vocabulario",
            summary="Resultados possíveis e seus sinais (+1/-1)")
def outcomes_vocabulario() -> dict[str, int]:
    return memoria_service.outcomes_vocabulario()


@router.post("/outcome", status_code=201,
             summary="Registra o resultado de um alvo (loop de aprendizado)")
async def registrar_outcome(body: OutcomeCreate) -> dict[str, bool]:
    await memoria_service.registrar_outcome(
        body.alvo_tipo, body.alvo_id, body.resultado, body.nota,
    )
    return {"ok": True}


@router.get("/{alvo_tipo}/{alvo_id}", response_model=TimelineResponse,
            summary="Linha do tempo de um alvo (o que os agentes já fizeram)")
async def timeline(alvo_tipo: str, alvo_id: str) -> TimelineResponse:
    return await memoria_service.timeline(alvo_tipo, alvo_id)


@router.post("", response_model=EventoOut, status_code=201,
             summary="Registra um evento na memória (ex: nota manual)")
async def criar(body: EventoCreate) -> EventoOut:
    return await memoria_service.criar(body)

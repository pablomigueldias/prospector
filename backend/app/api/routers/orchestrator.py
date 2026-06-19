"""Coordenador (MAS-2). Encadeia agentes com checkpoint humano."""
from fastapi import APIRouter, HTTPException

from app.api.schemas.orchestrator import (
    Briefing,
    CandidaturaAlvo,
    CandidaturaAnalise,
    CandidaturaEntrega,
)
from app.api.services.pessoal.vaga_service import VagaError
from app.orchestrator import briefing as briefing_chain
from app.orchestrator import candidatura

router = APIRouter(prefix="/api/orchestrator", tags=["orchestrator"])


@router.get("/briefing", response_model=Briefing,
            summary="Resumo da Noite — o que precisa de você (MAS-4)")
async def briefing() -> Briefing:
    return await briefing_chain.gerar()


@router.post("/candidatura/analisar", response_model=CandidaturaAnalise,
             summary="Cadeia candidatura — fase 1: análise (pré-checkpoint)")
async def analisar(body: CandidaturaAlvo) -> CandidaturaAnalise:
    try:
        return await candidatura.analisar(body.vaga_id)
    except VagaError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/candidatura/preparar", response_model=CandidaturaEntrega,
             summary="Cadeia candidatura — fase 2: CV+carta+checklist (após OK)")
async def preparar(body: CandidaturaAlvo) -> CandidaturaEntrega:
    try:
        return await candidatura.preparar(body.vaga_id)
    except VagaError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

"""Coordenador (MAS-2). Encadeia agentes com checkpoint humano."""
from fastapi import APIRouter, HTTPException

from app.api.schemas.orchestrator import (
    Briefing,
    CandidaturaAlvo,
    CandidaturaAnalise,
    CandidaturaEntrega,
    ProjetoFreelaAlvo,
    PropostaFreelaAnalise,
    PropostaFreelaEntrega,
)
from app.api.services.pessoal.freela_service import FreelaError
from app.api.services.pessoal.vaga_service import VagaError
from app.orchestrator import briefing as briefing_chain
from app.orchestrator import candidatura, proposta_freela

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


@router.post("/proposta-freela/analisar", response_model=PropostaFreelaAnalise,
             summary="Cadeia freela — fase 1: análise do projeto (pré-checkpoint)")
async def freela_analisar(body: ProjetoFreelaAlvo) -> PropostaFreelaAnalise:
    try:
        return await proposta_freela.analisar(body.projeto_id)
    except FreelaError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/proposta-freela/preparar", response_model=PropostaFreelaEntrega,
             summary="Cadeia freela — fase 2: cotar+redigir+conferir (após OK)")
async def freela_preparar(body: ProjetoFreelaAlvo) -> PropostaFreelaEntrega:
    try:
        return await proposta_freela.preparar(body.projeto_id)
    except FreelaError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

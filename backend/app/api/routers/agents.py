
from fastapi import APIRouter, HTTPException

from app.api.registry import get_agent, list_agents

router = APIRouter(prefix="/api/agents", tags=["agents"])


@router.get("", summary="Lista todos os agentes da plataforma")
def list_all() -> list[dict]:
    return [a.to_dict() for a in list_agents()]


@router.get("/{slug}", summary="Detalhe de um agente")
def get_one(slug: str) -> dict:
    agent = get_agent(slug)
    if agent is None:
        raise HTTPException(
            status_code=404, detail=f"Agente '{slug}' não encontrado"
        )
    return agent.to_dict()

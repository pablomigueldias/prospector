"""Agendamentos na UI — /api/agendamentos (S4, self-service).

Exige `usuarios.gerenciar` (admin). Lista os jobs e dispara on-demand; o
ligar/desligar e a hora são gravados pela tela via `/api/config` (S3).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies.auth import require_permission
from app.api.schemas.agendamentos import JobOut, JobRunResult
from app.api.services import agendamentos_service
from app.db.models.auth.usuario import Usuario

router = APIRouter(prefix="/api/agendamentos", tags=["agendamentos"])

_admin = require_permission("usuarios.gerenciar")


@router.get("", response_model=list[JobOut], summary="Lista os jobs agendados")
async def listar(_: Usuario = Depends(_admin)) -> list[JobOut]:
    return agendamentos_service.listar()


@router.post("/{job_id}/rodar", response_model=JobRunResult,
             summary="Dispara um job agora (on-demand)")
async def rodar(job_id: str, _: Usuario = Depends(_admin)) -> JobRunResult:
    try:
        return await agendamentos_service.rodar(job_id)
    except agendamentos_service.AgendamentoError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

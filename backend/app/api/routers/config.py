"""Configurações na UI — /api/config (S3, self-service).

Exige `usuarios.gerenciar` (admin): mexer no comportamento do sistema é coisa de
dono. A trava real é aqui no backend; a UI só esconde pra quem não pode.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import require_permission
from app.api.schemas.config import ConfigItemOut, ConfigUpdate
from app.api.services import config_service
from app.db.models.auth.usuario import Usuario
from app.db.session import get_session

router = APIRouter(prefix="/api/config", tags=["config"])

_admin = require_permission("usuarios.gerenciar")


@router.get("", response_model=list[ConfigItemOut],
            summary="Lista as configurações editáveis")
async def listar(
    session: AsyncSession = Depends(get_session),
    _: Usuario = Depends(_admin),
) -> list[ConfigItemOut]:
    return await config_service.listar(session)


@router.patch("", response_model=list[ConfigItemOut],
              summary="Atualiza configurações (override em runtime)")
async def atualizar(
    body: ConfigUpdate,
    session: AsyncSession = Depends(get_session),
    _: Usuario = Depends(_admin),
) -> list[ConfigItemOut]:
    try:
        await config_service.atualizar(session, body.mudancas)
    except config_service.ConfigError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return await config_service.listar(session)

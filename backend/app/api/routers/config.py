"""Configurações na UI — /api/config (S3, self-service).

Exige `usuarios.gerenciar` (admin): mexer no comportamento do sistema é coisa de
dono. A trava real é aqui no backend; a UI só esconde pra quem não pode. O
service abre a própria sessão (convenção do projeto), então o router só roteia.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies.auth import require_permission
from app.api.schemas.config import ConfigItemOut, ConfigUpdate
from app.api.services import config_service
from app.db.models.auth.usuario import Usuario

router = APIRouter(prefix="/api/config", tags=["config"])

_admin = require_permission("usuarios.gerenciar")


@router.get("", response_model=list[ConfigItemOut],
            summary="Lista as configurações editáveis")
async def listar(_: Usuario = Depends(_admin)) -> list[ConfigItemOut]:
    return await config_service.listar()


@router.patch("", response_model=list[ConfigItemOut],
              summary="Atualiza configurações (override em runtime)")
async def atualizar(
    body: ConfigUpdate,
    _: Usuario = Depends(_admin),
) -> list[ConfigItemOut]:
    try:
        await config_service.atualizar(body.mudancas)
    except config_service.ConfigError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return await config_service.listar()

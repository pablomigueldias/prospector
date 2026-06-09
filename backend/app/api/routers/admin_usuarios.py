"""Admin de usuários — /api/admin/* (exige usuarios.gerenciar)."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.dependencies.auth import require_permission
from app.api.schemas.auth import (
    PapelItem,
    UsuarioAdminCreate,
    UsuarioAdminItem,
    UsuarioAdminListResponse,
    UsuarioAdminUpdate,
)
from app.api.services.auth import admin_service, usuario_service
from app.api.services.auth.admin_service import AdminError
from app.db.models.auth.usuario import Usuario

router = APIRouter(prefix="/api/admin", tags=["admin:usuarios"])

# Quem manda nessas rotas.
_admin = require_permission("usuarios.gerenciar")


def _handle(e: Exception) -> HTTPException:
    if isinstance(e, AdminError):
        msg = str(e)
        low = msg.lower()
        status = 404 if "não encontrado" in low else (409 if "já existe" in low else 400)
        return HTTPException(status_code=status, detail=msg)
    return HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")


@router.get("/papeis", response_model=List[PapelItem], summary="Lista os papéis")
async def listar_papeis(_: Usuario = Depends(_admin)) -> List[PapelItem]:
    return await admin_service.listar_papeis()


@router.get("/usuarios", response_model=UsuarioAdminListResponse,
            summary="Lista os usuários")
async def listar(_: Usuario = Depends(_admin)) -> UsuarioAdminListResponse:
    return await admin_service.listar_usuarios()


@router.post("/usuarios", response_model=UsuarioAdminItem, status_code=201,
             summary="Cria um usuário")
async def criar(
    body: UsuarioAdminCreate, request: Request, ator: Usuario = Depends(_admin)
) -> UsuarioAdminItem:
    try:
        return await admin_service.criar_usuario(
            body, ator_id=ator.id,
            ip=usuario_service.ip_do_request(request),
            user_agent=usuario_service.user_agent_do_request(request),
        )
    except Exception as e:
        raise _handle(e)


@router.patch("/usuarios/{usuario_id}", response_model=UsuarioAdminItem,
              summary="Edita um usuário (nome/ativo/papéis)")
async def atualizar(
    usuario_id: str,
    body: UsuarioAdminUpdate,
    request: Request,
    ator: Usuario = Depends(_admin),
) -> UsuarioAdminItem:
    try:
        return await admin_service.atualizar_usuario(
            usuario_id, body, ator_id=ator.id,
            ip=usuario_service.ip_do_request(request),
            user_agent=usuario_service.user_agent_do_request(request),
        )
    except Exception as e:
        raise _handle(e)

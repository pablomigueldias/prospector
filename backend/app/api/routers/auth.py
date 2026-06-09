"""Rotas de autenticação — /api/auth/*."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, Response

from app.api.schemas.auth import LoginRequest, UsuarioResponse
from app.api.services.auth import login_service, usuario_service
from app.api.services.auth.cookie import set_session_cookie
from app.api.services.auth.login_service import CredenciaisInvalidas

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=UsuarioResponse, summary="Login (email+senha)")
async def login(body: LoginRequest, request: Request, response: Response) -> UsuarioResponse:
    try:
        token, usuario = await login_service.login(
            body.email,
            body.senha,
            ip=usuario_service.ip_do_request(request),
            user_agent=usuario_service.user_agent_do_request(request),
        )
    except CredenciaisInvalidas as e:
        # 401 genérico — não vaza se o email existe.
        raise HTTPException(status_code=401, detail=str(e))

    set_session_cookie(response, token)
    return usuario_service.to_response(usuario)

"""Rotas de autenticação — /api/auth/*."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from app.api.dependencies.auth import usuario_atual
from app.api.schemas.auth import LoginRequest, MensagemResponse, UsuarioResponse
from app.api.services.auth import login_service, sessao_service, usuario_service
from app.api.services.auth import permissoes as permissoes_service
from app.api.services.auth.cookie import clear_session_cookie, cookie_name, set_session_cookie
from app.api.services.auth.login_service import CredenciaisInvalidas
from app.db.models.auth.usuario import Usuario
from app.db.session import get_session

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
    async with get_session() as session:
        codigos = await permissoes_service.listar_codigos(session, usuario.id)
    return usuario_service.to_response(usuario, permissoes=codigos)


@router.get("/me", response_model=UsuarioResponse, summary="Usuário logado + permissões")
async def me(usuario: Usuario = Depends(usuario_atual)) -> UsuarioResponse:
    async with get_session() as session:
        codigos = await permissoes_service.listar_codigos(session, usuario.id)
    return usuario_service.to_response(usuario, permissoes=codigos)


@router.post("/logout", response_model=MensagemResponse, summary="Encerra a sessão atual")
async def logout(request: Request, response: Response) -> MensagemResponse:
    token = request.cookies.get(cookie_name())
    if token:
        async with get_session() as session:
            await sessao_service.revogar_token(session, token)
            await session.commit()
    clear_session_cookie(response)
    return MensagemResponse(ok=True, mensagem="Sessão encerrada.")


@router.post("/logout-all", response_model=MensagemResponse,
             summary="Sai de todos os dispositivos")
async def logout_all(
    response: Response, usuario: Usuario = Depends(usuario_atual)
) -> MensagemResponse:
    async with get_session() as session:
        n = await sessao_service.revogar_todas(session, usuario.id)
        await session.commit()
    clear_session_cookie(response)
    return MensagemResponse(ok=True, mensagem=f"{n} sessão(ões) encerrada(s).")

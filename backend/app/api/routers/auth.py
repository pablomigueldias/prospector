"""Rotas de autenticação — /api/auth/*."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from app.api.dependencies.auth import usuario_atual
from app.api.schemas.auth import (
    LoginRequest,
    MensagemResponse,
    TrocaSenhaRequest,
    TwoFAAtivarResponse,
    TwoFACodigoRequest,
    TwoFADesativarRequest,
    TwoFASetupResponse,
    UsuarioResponse,
)
from app.api.services.auth import senha_service
from app.api.services.auth.senha_service import SenhaFraca
from app.api.services.auth import (
    auditoria_service,
    login_service,
    sessao_service,
    twofa_service,
    usuario_service,
)
from app.api.services.auth.twofa_service import TwoFAError
from app.api.services.auth import permissoes as permissoes_service
from app.api.services.auth.cookie import clear_session_cookie, cookie_name, set_session_cookie
from app.api.services.auth.csrf import set_csrf_cookie
from app.api.services.auth.login_service import (
    Bloqueado,
    CredenciaisInvalidas,
    DoisFatoresRequerido,
)
from app.db.models.auth.usuario import Usuario
from app.db.session import get_session

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=UsuarioResponse, summary="Login (email+senha)")
async def login(body: LoginRequest, request: Request, response: Response) -> UsuarioResponse:
    try:
        token, usuario = await login_service.login(
            body.email,
            body.senha,
            codigo_2fa=body.codigo_2fa,
            ip=usuario_service.ip_do_request(request),
            user_agent=usuario_service.user_agent_do_request(request),
        )
    except Bloqueado as e:
        # 429 — excesso de tentativas (rate limit / lockout).
        raise HTTPException(status_code=429, detail=str(e))
    except DoisFatoresRequerido:
        # 401 com marcador: o front mostra o campo de código e reenvia.
        raise HTTPException(status_code=401, detail="2fa_requerido")
    except CredenciaisInvalidas as e:
        # 401 genérico — não vaza se o email existe.
        raise HTTPException(status_code=401, detail=str(e))

    set_session_cookie(response, token)
    set_csrf_cookie(response)  # par do double-submit, legível pelo JS
    async with get_session() as session:
        codigos = await permissoes_service.listar_codigos(session, usuario.id)
    return usuario_service.to_response(usuario, permissoes=codigos)


@router.get("/me", response_model=UsuarioResponse, summary="Usuário logado + permissões")
async def me(
    response: Response, usuario: Usuario = Depends(usuario_atual)
) -> UsuarioResponse:
    set_csrf_cookie(response)  # garante o cookie CSRF a cada carga do app
    async with get_session() as session:
        codigos = await permissoes_service.listar_codigos(session, usuario.id)
    return usuario_service.to_response(usuario, permissoes=codigos)


@router.post("/senha", response_model=MensagemResponse,
             summary="Troca a senha (revoga as outras sessões)")
async def trocar_senha(
    body: TrocaSenhaRequest,
    request: Request,
    usuario: Usuario = Depends(usuario_atual),
) -> MensagemResponse:
    async with get_session() as session:
        u = await session.get(Usuario, usuario.id)
        if u is None or not senha_service.conferir_senha(u.senha_hash, body.senha_atual):
            raise HTTPException(status_code=400, detail="Senha atual incorreta.")
        try:
            senha_service.validar_forca(body.senha_nova)
        except SenhaFraca as e:
            raise HTTPException(status_code=400, detail=str(e))

        u.senha_hash = senha_service.hash_senha(body.senha_nova)
        token_atual = request.cookies.get(cookie_name())
        n = await sessao_service.revogar_outras(session, u.id, token_atual)
        await auditoria_service.registrar(
            session, auditoria_service.SENHA_ALTERADA, usuario_id=u.id,
            ip=usuario_service.ip_do_request(request),
            user_agent=usuario_service.user_agent_do_request(request),
            detalhe={"sessoes_revogadas": n},
        )
        await session.commit()
    return MensagemResponse(
        ok=True, mensagem=f"Senha alterada. {n} outra(s) sessão(ões) encerrada(s)."
    )


@router.post("/logout", response_model=MensagemResponse, summary="Encerra a sessão atual")
async def logout(request: Request, response: Response) -> MensagemResponse:
    token = request.cookies.get(cookie_name())
    if token:
        async with get_session() as session:
            uid = await sessao_service.revogar_token(session, token)
            if uid:
                await auditoria_service.registrar(
                    session, auditoria_service.LOGOUT, usuario_id=uid,
                    ip=usuario_service.ip_do_request(request),
                    user_agent=usuario_service.user_agent_do_request(request),
                )
            await session.commit()
    clear_session_cookie(response)
    return MensagemResponse(ok=True, mensagem="Sessão encerrada.")


@router.post("/logout-all", response_model=MensagemResponse,
             summary="Sai de todos os dispositivos")
async def logout_all(
    request: Request, response: Response, usuario: Usuario = Depends(usuario_atual)
) -> MensagemResponse:
    async with get_session() as session:
        n = await sessao_service.revogar_todas(session, usuario.id)
        await auditoria_service.registrar(
            session, auditoria_service.LOGOUT_ALL, usuario_id=usuario.id,
            ip=usuario_service.ip_do_request(request),
            user_agent=usuario_service.user_agent_do_request(request),
            detalhe={"sessoes": n},
        )
        await session.commit()
    clear_session_cookie(response)
    return MensagemResponse(ok=True, mensagem=f"{n} sessão(ões) encerrada(s).")


# ── 2FA (TOTP) ─────────────────────────────────────────────────────
@router.post("/2fa/setup", response_model=TwoFASetupResponse,
             summary="Inicia o 2FA: devolve secret + QR (ainda não ativa)")
async def twofa_setup(
    usuario: Usuario = Depends(usuario_atual),
) -> TwoFASetupResponse:
    async with get_session() as session:
        u = await session.get(Usuario, usuario.id)
        try:
            dados = await twofa_service.gerar_setup(session, u)
        except TwoFAError as e:
            raise HTTPException(status_code=400, detail=str(e))
        await session.commit()
    return TwoFASetupResponse(**dados)


@router.post("/2fa/ativar", response_model=TwoFAAtivarResponse,
             summary="Confirma o 1º código e ativa o 2FA (devolve backup codes)")
async def twofa_ativar(
    body: TwoFACodigoRequest,
    request: Request,
    usuario: Usuario = Depends(usuario_atual),
) -> TwoFAAtivarResponse:
    async with get_session() as session:
        u = await session.get(Usuario, usuario.id)
        try:
            codes = await twofa_service.confirmar_ativacao(session, u, body.codigo)
        except TwoFAError as e:
            raise HTTPException(status_code=400, detail=str(e))
        await auditoria_service.registrar(
            session, auditoria_service.TWOFA_ATIVADO, usuario_id=u.id,
            ip=usuario_service.ip_do_request(request),
            user_agent=usuario_service.user_agent_do_request(request),
        )
        await session.commit()
    return TwoFAAtivarResponse(ok=True, backup_codes=codes)


@router.post("/2fa/desativar", response_model=MensagemResponse,
             summary="Desativa o 2FA (exige senha + código)")
async def twofa_desativar(
    body: TwoFADesativarRequest,
    request: Request,
    usuario: Usuario = Depends(usuario_atual),
) -> MensagemResponse:
    async with get_session() as session:
        u = await session.get(Usuario, usuario.id)
        if u is None or not u.twofa_ativado:
            raise HTTPException(status_code=400, detail="2FA não está ativo.")
        if not senha_service.conferir_senha(u.senha_hash, body.senha):
            raise HTTPException(status_code=400, detail="Senha atual incorreta.")
        if not await twofa_service.validar_codigo(session, u.id, body.codigo):
            raise HTTPException(status_code=400, detail="Código de verificação inválido.")
        await twofa_service.desativar(session, u)
        await auditoria_service.registrar(
            session, auditoria_service.TWOFA_DESATIVADO, usuario_id=u.id,
            ip=usuario_service.ip_do_request(request),
            user_agent=usuario_service.user_agent_do_request(request),
        )
        await session.commit()
    return MensagemResponse(ok=True, mensagem="2FA desativado.")

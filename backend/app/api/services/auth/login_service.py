"""Login — confere credenciais e abre sessão.

Mensagem SEMPRE genérica ("email ou senha inválidos") pra não denunciar quais
emails existem (anti-enumeração). O anti-timing fica no senha_service.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import select

from app.api.services.auth import (
    auditoria_service,
    rate_limit,
    senha_service,
    sessao_service,
    twofa_service,
)
from app.api.services.auth.rate_limit import Bloqueado  # noqa: F401 (re-export pro router)
from app.db.models.auth.usuario import Usuario
from app.db.session import get_session


class CredenciaisInvalidas(Exception):
    """Login falhou. Vira HTTP 401 com mensagem genérica."""


class DoisFatoresRequerido(Exception):
    """Senha OK mas falta o 2º fator. Vira HTTP 401 com marcador 2fa_requerido."""


async def login(
    email: str,
    senha: str,
    *,
    codigo_2fa: Optional[str] = None,
    ip: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> tuple[str, Usuario]:
    """Valida email+senha (+2FA se ativo) e devolve (token_de_sessão, usuario).

    Levanta CredenciaisInvalidas em falha de senha (mensagem genérica, anti-
    enumeração). Se o 2FA estiver ativo e ``codigo_2fa`` faltar, levanta
    DoisFatoresRequerido (o front então pede o código e reenvia). Código de
    2FA errado conta como falha (rate limit) — aí a senha já foi provada, então
    a mensagem pode ser específica sem vazar a existência da conta.
    """
    email_norm = (email or "").strip().lower()
    async with get_session() as session:
        # Barreira de força bruta — levanta Bloqueado (→ 429) antes de tudo.
        await rate_limit.checar(session, email_norm, ip)

        usuario = await session.scalar(
            select(Usuario).where(Usuario.email == email_norm)
        )
        # Anti-timing: conferir_senha gasta CPU mesmo com hash None.
        hash_armazenado = usuario.senha_hash if usuario else None
        senha_ok = (
            senha_service.conferir_senha(hash_armazenado, senha)
            and usuario is not None
            and usuario.ativo
        )
        if not senha_ok:
            await rate_limit.registrar(session, email_norm, ip, sucesso=False)
            await auditoria_service.registrar(
                session, auditoria_service.LOGIN_FALHA,
                ip=ip, user_agent=user_agent, detalhe={"email": email_norm},
            )
            await session.commit()  # persiste a tentativa falha (pro lockout)
            raise CredenciaisInvalidas("Email ou senha inválidos.")

        # ── 2º fator (se ligado) ──────────────────────────────────────
        if usuario.twofa_ativado:
            if not (codigo_2fa or "").strip():
                # 1ª etapa: senha certa, mas falta o código. NÃO registra
                # (não é falha de senha nem login completo) e não abre sessão.
                raise DoisFatoresRequerido("2fa_requerido")
            if not await twofa_service.validar_codigo(session, usuario.id, codigo_2fa):
                await rate_limit.registrar(session, email_norm, ip, sucesso=False)
                await auditoria_service.registrar(
                    session, auditoria_service.LOGIN_FALHA,
                    usuario_id=usuario.id, ip=ip, user_agent=user_agent,
                    detalhe={"motivo": "2fa"},
                )
                await session.commit()
                raise CredenciaisInvalidas("Código de verificação inválido.")

        # autenticado de fato — limpa o contador de tentativas
        await rate_limit.registrar(session, email_norm, ip, sucesso=True)

        # Rehash transparente se os parâmetros do Argon2 mudaram.
        if senha_service.precisa_rehash(usuario.senha_hash):
            usuario.senha_hash = senha_service.hash_senha(senha)

        usuario.ultimo_login = sessao_service._agora()
        token = await sessao_service.criar_sessao(
            session, usuario.id, ip=ip, user_agent=user_agent
        )
        await auditoria_service.registrar(
            session, auditoria_service.LOGIN_OK,
            usuario_id=usuario.id, ip=ip, user_agent=user_agent,
        )
        await session.commit()
        await session.refresh(usuario)
        return token, usuario

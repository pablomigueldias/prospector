"""Login — confere credenciais e abre sessão.

Mensagem SEMPRE genérica ("email ou senha inválidos") pra não denunciar quais
emails existem (anti-enumeração). O anti-timing fica no senha_service.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import select

from app.api.services.auth import rate_limit, senha_service, sessao_service
from app.api.services.auth.rate_limit import Bloqueado  # noqa: F401 (re-export pro router)
from app.db.models.auth.usuario import Usuario
from app.db.session import get_session


class CredenciaisInvalidas(Exception):
    """Login falhou. Vira HTTP 401 com mensagem genérica."""


async def login(
    email: str,
    senha: str,
    *,
    ip: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> tuple[str, Usuario]:
    """Valida email+senha e devolve (token_de_sessão, usuario).

    Levanta CredenciaisInvalidas em qualquer falha (email não existe, senha
    errada, usuário inativo) — sempre a mesma mensagem.
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
        ok = (
            senha_service.conferir_senha(hash_armazenado, senha)
            and usuario is not None
            and usuario.ativo
        )
        await rate_limit.registrar(session, email_norm, ip, sucesso=ok)
        if not ok:
            await session.commit()  # persiste a tentativa falha (pro lockout)
            raise CredenciaisInvalidas("Email ou senha inválidos.")

        # Rehash transparente se os parâmetros do Argon2 mudaram.
        if senha_service.precisa_rehash(usuario.senha_hash):
            usuario.senha_hash = senha_service.hash_senha(senha)

        usuario.ultimo_login = sessao_service._agora()
        token = await sessao_service.criar_sessao(
            session, usuario.id, ip=ip, user_agent=user_agent
        )
        await session.commit()
        await session.refresh(usuario)
        return token, usuario

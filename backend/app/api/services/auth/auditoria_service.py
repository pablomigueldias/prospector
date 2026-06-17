"""Registro da trilha de auditoria (eventos de segurança)."""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.auth.auditoria import Auditoria

# Nomes canônicos de evento.
LOGIN_OK = "login_ok"
LOGIN_FALHA = "login_falha"
LOGOUT = "logout"
LOGOUT_ALL = "logout_all"
SENHA_ALTERADA = "senha_alterada"
USUARIO_CRIADO = "usuario_criado"
PAPEIS_ALTERADOS = "papeis_alterados"
TWOFA_ATIVADO = "2fa_ativado"
TWOFA_DESATIVADO = "2fa_desativado"


async def registrar(
    session: AsyncSession,
    evento: str,
    *,
    usuario_id: uuid.UUID | None = None,
    ip: str | None = None,
    user_agent: str | None = None,
    detalhe: dict[str, Any] | None = None,
) -> None:
    """Adiciona uma linha de auditoria. Não faz commit (quem chama controla)."""
    session.add(
        Auditoria(
            usuario_id=usuario_id,
            evento=evento,
            ip=ip,
            user_agent=(user_agent[:400] if user_agent else None),
            detalhe=detalhe,
        )
    )
    await session.flush()

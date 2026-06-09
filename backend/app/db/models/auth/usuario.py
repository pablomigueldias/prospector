from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import expression

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Usuario(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Quem pode entrar no app. Sem cadastro público — só o admin cria usuários.

    A senha NUNCA é guardada em texto: ``senha_hash`` é um hash Argon2id
    (ver ``app.api.services.auth.senha_service``). ``email`` é único e sempre
    normalizado pra minúsculas no service.
    """

    __tablename__ = "usuarios"

    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    nome: Mapped[str] = mapped_column(String(200), nullable=False)

    ativo: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=expression.true()
    )
    # Liga o login em 2 etapas. O secret/backup codes ficam em tabela à parte
    # (usuario_2fa), entram numa fase posterior.
    twofa_ativado: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=expression.false()
    )

    ultimo_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = ({"schema": "auth"},)

    def __repr__(self) -> str:
        return f"<Usuario id={self.id} email={self.email!r}>"

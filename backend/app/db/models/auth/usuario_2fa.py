from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class UsuarioTwoFA(Base, TimestampMixin):
    """Segundo fator (TOTP) de um usuário — 1:1 com ``auth.usuarios``.

    O ``twofa_ativado`` mora em ``Usuario`` (lido no login sem JOIN); aqui ficam
    os segredos. O ``totp_secret`` NUNCA é guardado em texto: vai cifrado com
    Fernet (chave ``TOTP_ENC_KEY`` no ``.env``). Os backup codes são guardados
    só como hash (sha256), de uso único — some do array quando consumido.

    A linha pode existir "pendente" (secret gerado mas ainda não confirmado):
    nesse caso ``ativado_em is None`` e ``Usuario.twofa_ativado`` segue False.
    """

    __tablename__ = "usuario_2fa"

    usuario_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("auth.usuarios.id", ondelete="CASCADE", name="fk_auth_2fa_usuario"),
        primary_key=True,
    )

    totp_secret_cifrado: Mapped[str] = mapped_column(String(255), nullable=False)
    backup_codes_hash: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=False, default=list
    )
    ativado_em: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = ({"schema": "auth"},)

    def __repr__(self) -> str:
        estado = "ativo" if self.ativado_em else "pendente"
        return f"<UsuarioTwoFA usuario_id={self.usuario_id} {estado}>"

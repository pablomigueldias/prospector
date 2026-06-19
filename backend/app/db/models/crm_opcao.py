from __future__ import annotations

from sqlalchemy import Boolean, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class CrmOpcao(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Opção de um select do CRM, gerenciável na UI.

    Substitui as constantes fixas do config (que espelhavam o Notion). Cada linha
    é uma opção de um `grupo` (status, setor, estagio, atividade_tipo…), com cor
    e ordem próprias. `GET /crm/opcoes` lê daqui; a UI de configuração faz o CRUD.
    """

    __tablename__ = "crm_opcoes"

    grupo: Mapped[str] = mapped_column(String(40), nullable=False)
    valor: Mapped[str] = mapped_column(String(120), nullable=False)
    cor: Mapped[str | None] = mapped_column(String(30))  # token/hex p/ a pílula
    ordem: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    __table_args__ = (
        UniqueConstraint("grupo", "valor", name="uq_crm_opcoes_grupo_valor"),
        Index("ix_crm_opcoes_grupo", "grupo"),
    )

    def __repr__(self) -> str:
        return f"<CrmOpcao {self.grupo}:{self.valor!r}>"

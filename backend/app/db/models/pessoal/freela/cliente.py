from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.pessoal.freela.projeto import Projeto


class Cliente(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """O contratante. ``ja_me_pagou_usd`` é o que define a faixa de
    comissão (cliente recorrente vale ouro): novo = 20%, após US$300 = 10%,
    após US$3.000 = 5% (no caso da Workana).
    """

    __tablename__ = "pessoal_freela_cliente"

    plataforma_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("pessoal_freela_plataforma.id", ondelete="SET NULL"),
        nullable=True,
    )

    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    rating: Mapped[float | None] = mapped_column(Numeric(3, 2))
    projetos_publicados: Mapped[int | None] = mapped_column(Integer)
    projetos_pagos: Mapped[int | None] = mapped_column(Integer)
    pagamento_verificado: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )
    membro_desde: Mapped[str | None] = mapped_column(String(50))
    # Acumulado já pago A VOCÊ por este cliente — define a faixa de comissão.
    ja_me_pagou_usd: Mapped[float] = mapped_column(
        Numeric(12, 2), default=0, server_default="0", nullable=False
    )
    notas: Mapped[str | None] = mapped_column(Text)

    projetos: Mapped[list[Projeto]] = relationship(
        back_populates="cliente",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Cliente id={self.id} nome={self.nome!r} pago_usd={self.ja_me_pagou_usd}>"

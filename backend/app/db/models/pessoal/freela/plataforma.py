from __future__ import annotations

from typing import Optional

from sqlalchemy import Numeric, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Plataforma(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Site de freelancer (Workana, 99freelas...).

    O ``adapter`` (regras de comissão / lance mínimo) é fino: a parte
    variável por site vive em ``config_comissao`` (JSONB) e
    ``lance_minimo_padrao``. A inteligência (analisar/precificar/redigir)
    é compartilhada e não depende daqui.
    """

    __tablename__ = "pessoal_freela_plataforma"

    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    url_base: Mapped[Optional[str]] = mapped_column(String(300))

    # Faixas de comissão escalonada por cliente. Ex. Workana:
    # {"faixas": [{"ate_usd": 300, "pct": 0.20}, {"ate_usd": 3000, "pct": 0.10},
    #             {"ate_usd": null, "pct": 0.05}], "custo_servico_cliente_pct": 0.045}
    config_comissao: Mapped[Optional[dict]] = mapped_column(JSONB)

    lance_minimo_padrao: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))

    def __repr__(self) -> str:
        return f"<Plataforma id={self.id} nome={self.nome!r}>"

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Index,Integer,String,Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base, UUIDPrimaryKeyMixin

class PipelineEvent(Base, UUIDPrimaryKeyMixin):

    __tablename__ = "pipeline_events"

    evento: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default='ok', server_default='ok', nullable=False
    )
    detalhe: Mapped[Optional[str]] = mapped_column(Text)
    empresa_cnpj: Mapped[Optional[str]] = mapped_column(String(20))
    duracao_ms: Mapped[Optional[int]] = mapped_column(Integer)

    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index("ix_pipeline_events_evento", "evento"),
        Index("ix_pipeline_events_created_at", "created_at"),
        Index("ix_pipeline_events_empresa_cnpj", "empresa_cnpj"),
    )

    def __repr__(self) -> str:
        return f"<PipelineEvent {self.evento} status={self.status}>"
from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


if TYPE_CHECKING:
    from app.db.models.pessoal.candidatura_email import CandidaturaEmail


# Espelha o pipeline de status de lead do Prospector, mas pra candidatura.
STATUS_VAGA = (
    "quero_candidatar",
    "candidatei",
    "respondeu",
    "entrevista",
    "fim",
)


class Vaga(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Vaga-alvo — espelha a 'empresa-alvo' do Prospector.

    Você cola a descrição (Fase 1). A IA destrincha em ``analise_json``
    (Fase 2) e cruza com o Perfil Mestre em ``match_json`` (Fase 3).
    """

    __tablename__ = "pessoal_vagas"

    # ── Identidade da vaga ───────────────────────────────────────
    titulo: Mapped[str] = mapped_column(String(300), nullable=False)
    empresa: Mapped[Optional[str]] = mapped_column(String(300))
    link: Mapped[Optional[str]] = mapped_column(String(800))
    fonte: Mapped[Optional[str]] = mapped_column(String(100))  # LinkedIn, Gupy...

    # ── Contato pra candidatura ──────────────────────────────────
    contato_nome: Mapped[Optional[str]] = mapped_column(String(200))
    contato_email: Mapped[Optional[str]] = mapped_column(String(300))

    # ── Detalhes ─────────────────────────────────────────────────
    localizacao: Mapped[Optional[str]] = mapped_column(String(200))
    modelo: Mapped[Optional[str]] = mapped_column(String(30))  # remoto/hibrido/presencial
    senioridade: Mapped[Optional[str]] = mapped_column(String(50))
    descricao: Mapped[str] = mapped_column(Text, nullable=False)  # JD colada
    notas: Mapped[Optional[str]] = mapped_column(Text)

    # ── Pipeline ─────────────────────────────────────────────────
    status: Mapped[str] = mapped_column(
        String(30),
        default="quero_candidatar",
        server_default="quero_candidatar",
        nullable=False,
    )

    # ── Saídas da IA ─────────────────────────────────────────────
    # analise_json (Fase 2): {requisitos_obrigatorios[], desejaveis[],
    #   stack[], senioridade, palavras_chave[], resumo}
    analise_json: Mapped[Optional[dict]] = mapped_column(JSONB)
    # match_json (Fase 3): {aderencia, tenho[], gaps[], destaques[]}
    match_json: Mapped[Optional[dict]] = mapped_column(JSONB)
    # Match resumido como inteiro 0-100 (espelha 'score' da Empresa)
    match_score: Mapped[Optional[int]] = mapped_column(Integer)

    emails: Mapped[List["CandidaturaEmail"]] = relationship(
        back_populates="vaga",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_pessoal_vagas_status", "status"),
        Index("ix_pessoal_vagas_match_score", "match_score"),
    )

    def __repr__(self) -> str:
        return f"<Vaga id={self.id} titulo={self.titulo!r} status={self.status}>"

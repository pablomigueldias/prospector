from __future__ import annotations

import uuid
from typing import List, Optional

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.pessoal.candidatura_email import CandidaturaEmail
from app.db.models.pessoal.vaga import Vaga


class VagaRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, dados: dict) -> Vaga:
        vaga = Vaga(**dados)
        self.session.add(vaga)
        await self.session.commit()
        await self.session.refresh(vaga)
        return vaga

    async def get(self, vaga_id: uuid.UUID) -> Optional[Vaga]:
        return await self.session.get(Vaga, vaga_id)

    async def listar(
        self, status: Optional[str] = None, limit: int = 100
    ) -> List[tuple[Vaga, int]]:
        """Lista vagas + contagem de rascunhos de candidatura por vaga."""
        rascunhos = (
            select(
                CandidaturaEmail.vaga_id,
                func.count(CandidaturaEmail.id).label("qtd"),
            )
            .group_by(CandidaturaEmail.vaga_id)
            .subquery()
        )
        stmt = (
            select(Vaga, func.coalesce(rascunhos.c.qtd, 0))
            .outerjoin(rascunhos, rascunhos.c.vaga_id == Vaga.id)
            .order_by(
                Vaga.match_score.desc().nulls_last(),
                Vaga.created_at.desc(),
            )
            .limit(limit)
        )
        if status:
            stmt = stmt.where(Vaga.status == status)

        result = await self.session.execute(stmt)
        return [(row[0], int(row[1])) for row in result.all()]

    async def update(self, vaga_id: uuid.UUID, dados: dict) -> Optional[Vaga]:
        vaga = await self.get(vaga_id)
        if vaga is None:
            return None
        for campo, valor in dados.items():
            if valor is not None:
                setattr(vaga, campo, valor)
        await self.session.commit()
        await self.session.refresh(vaga)
        return vaga

    async def salvar_analise(
        self,
        vaga_id: uuid.UUID,
        analise: dict,
        match: dict,
        match_score: int,
    ) -> Optional[Vaga]:
        vaga = await self.get(vaga_id)
        if vaga is None:
            return None
        vaga.analise_json = analise
        vaga.match_json = match
        vaga.match_score = match_score
        await self.session.commit()
        await self.session.refresh(vaga)
        return vaga

    async def delete(self, vaga_id: uuid.UUID) -> bool:
        result = await self.session.execute(
            delete(Vaga).where(Vaga.id == vaga_id)
        )
        await self.session.commit()
        return result.rowcount > 0

    # ── Rascunhos de candidatura ─────────────────────────────────
    async def add_email(self, dados: dict) -> CandidaturaEmail:
        email = CandidaturaEmail(**dados)
        self.session.add(email)
        await self.session.commit()
        await self.session.refresh(email)
        return email

    async def listar_emails(self, vaga_id: uuid.UUID) -> List[CandidaturaEmail]:
        stmt = (
            select(CandidaturaEmail)
            .where(CandidaturaEmail.vaga_id == vaga_id)
            .order_by(CandidaturaEmail.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

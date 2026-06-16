from __future__ import annotations

import uuid
from typing import List, Optional

from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.pessoal.candidatura_email import CandidaturaEmail
from app.db.models.pessoal.vaga import STATUS_VAGA, Vaga


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
        self,
        status: Optional[str] = None,
        *,
        busca: Optional[str] = None,
        match_min: Optional[int] = None,
        modelo: Optional[str] = None,
        fonte: Optional[str] = None,
        tem_rascunho: Optional[bool] = None,
        ordenar_por: str = "match",
        limit: int = 100,
    ) -> List[tuple[Vaga, int]]:
        """Lista vagas + contagem de rascunhos, com busca/filtros/ordenação."""
        rascunhos = (
            select(
                CandidaturaEmail.vaga_id,
                func.count(CandidaturaEmail.id).label("qtd"),
            )
            .group_by(CandidaturaEmail.vaga_id)
            .subquery()
        )
        qtd = func.coalesce(rascunhos.c.qtd, 0)
        stmt = (
            select(Vaga, qtd)
            .outerjoin(rascunhos, rascunhos.c.vaga_id == Vaga.id)
            .order_by(*self._ordem(ordenar_por))
            .limit(limit)
        )
        if status:
            stmt = stmt.where(Vaga.status == status)
        if busca:
            termo = f"%{busca.strip()}%"
            stmt = stmt.where(
                or_(Vaga.titulo.ilike(termo), Vaga.empresa.ilike(termo))
            )
        if match_min is not None:
            stmt = stmt.where(Vaga.match_score >= match_min)
        if modelo:
            stmt = stmt.where(Vaga.modelo.ilike(f"%{modelo}%"))
        if fonte:
            stmt = stmt.where(Vaga.fonte.ilike(f"%{fonte}%"))
        if tem_rascunho is True:
            stmt = stmt.where(qtd > 0)
        elif tem_rascunho is False:
            stmt = stmt.where(qtd == 0)

        result = await self.session.execute(stmt)
        return [(row[0], int(row[1])) for row in result.all()]

    @staticmethod
    def _ordem(ordenar_por: str):
        """Critérios de ORDER BY conforme a chave escolhida no front."""
        if ordenar_por == "recentes":
            return (Vaga.created_at.desc(),)
        # 'match' (padrão): melhor aderência primeiro, desempate por recência
        return (Vaga.match_score.desc().nulls_last(), Vaga.created_at.desc())

    async def metricas(self) -> dict:
        """Funil + taxas, agregando TODAS as vagas (ignora filtros da lista)."""
        por_status = dict(
            (
                await self.session.execute(
                    select(Vaga.status, func.count(Vaga.id)).group_by(Vaga.status)
                )
            ).all()
        )
        # Match médio: todas com score, e só as que viraram candidatura.
        candidatou_status = ("candidatei", "respondeu", "entrevista", "fim")
        match_geral = (
            await self.session.execute(
                select(func.avg(Vaga.match_score)).where(Vaga.match_score.isnot(None))
            )
        ).scalar()
        match_cand = (
            await self.session.execute(
                select(func.avg(Vaga.match_score)).where(
                    Vaga.match_score.isnot(None),
                    Vaga.status.in_(candidatou_status),
                )
            )
        ).scalar()
        return {
            "por_status": {s: int(por_status.get(s, 0)) for s in STATUS_VAGA},
            "match_medio": float(match_geral) if match_geral is not None else None,
            "match_medio_candidaturas": (
                float(match_cand) if match_cand is not None else None
            ),
        }

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

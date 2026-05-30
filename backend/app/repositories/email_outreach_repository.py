from __future__ import annotations

import uuid
from datetime import datetime,timedelta
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.contato import Contato
from app.db.models.email_outreach import EmailOutreach
from app.utils.logger import get_logger

logger = get_logger()


class EmailOutreachRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def contatos_pendentes(self, limit: Optional[int] = None) -> List[Contato]:

        ja_contatados = select(EmailOutreach.contato_id).where(
            EmailOutreach.contato_id.is_not(None)
        )
        stmt = (
            select(Contato)
            .where(
                Contato.email.is_not(None),
                Contato.email != "",
                Contato.id.not_in(ja_contatados),
            )
            .order_by(Contato.created_at.asc())
        )
        if limit:
            stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def ja_tem_para_contato(self, contato_id: uuid.UUID) -> bool:
        stmt = select(func.count(EmailOutreach.id)).where(
            EmailOutreach.contato_id == contato_id
        )
        return (await self.session.scalar(stmt) or 0) > 0
    
    async def candidatos_followup(
        self,
        dias: int = 3,
        max_followups: int = 2,
        limit: Optional[int] = None,
    ) -> List[EmailOutreach]:
       
        cutoff = datetime.now() - timedelta(days=dias)

        ja_tem_followup = select(EmailOutreach.parent_id).where(
            EmailOutreach.parent_id.is_not(None)
        )

        stmt = (
            select(EmailOutreach)
            .where(
                EmailOutreach.status == "enviado",
                EmailOutreach.primeira_resposta_em.is_(None),
                EmailOutreach.enviado_em.is_not(None),
                EmailOutreach.enviado_em < cutoff,
                EmailOutreach.follow_up_num < max_followups,
                EmailOutreach.id.not_in(ja_tem_followup),
            )
            .order_by(EmailOutreach.enviado_em.asc())
        )
        if limit:
            stmt = stmt.limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    def add(self, registro: EmailOutreach) -> EmailOutreach:
        self.session.add(registro)
        return registro
    
    async def listar_recentes(self, limit: int = 50):
        from app.db.models.email_outreach import EmailOutreach
        stmt = (
            select(EmailOutreach)
            .order_by(EmailOutreach.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.linkedin.post import LinkedinPost


class LinkedinRepository:
    """Acesso a dados do agente LinkedIn (linkedin_post)."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, dados: dict) -> LinkedinPost:
        post = LinkedinPost(**dados)
        self.session.add(post)
        await self.session.commit()
        await self.session.refresh(post)
        return post

    async def create_varios(self, lista: list[dict]) -> list[LinkedinPost]:
        """Insere vários de uma vez (saída do motor autônomo) — 1 commit."""
        posts = [LinkedinPost(**d) for d in lista]
        self.session.add_all(posts)
        await self.session.commit()
        for p in posts:
            await self.session.refresh(p)
        return posts

    async def get(self, pid: uuid.UUID) -> LinkedinPost | None:
        return await self.session.get(LinkedinPost, pid)

    async def listar(
        self,
        *,
        status: str | None = None,
        conta: str | None = None,
        limit: int = 500,
        offset: int = 0,
    ) -> list[LinkedinPost]:
        stmt = select(LinkedinPost)
        if status:
            stmt = stmt.where(LinkedinPost.status == status)
        if conta:
            stmt = stmt.where(LinkedinPost.conta == conta)
        stmt = (
            stmt.order_by(LinkedinPost.updated_at.desc()).limit(limit).offset(offset)
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def update(self, pid: uuid.UUID, dados: dict) -> LinkedinPost | None:
        post = await self.get(pid)
        if post is None:
            return None
        for campo, valor in dados.items():
            setattr(post, campo, valor)
        await self.session.commit()
        await self.session.refresh(post)
        return post

    async def delete(self, pid: uuid.UUID) -> bool:
        result = await self.session.execute(
            delete(LinkedinPost).where(LinkedinPost.id == pid)
        )
        await self.session.commit()
        return result.rowcount > 0

    async def contar(self, *, status: str | None = None, conta: str | None = None) -> int:
        stmt = select(func.count()).select_from(LinkedinPost)
        if status:
            stmt = stmt.where(LinkedinPost.status == status)
        if conta:
            stmt = stmt.where(LinkedinPost.conta == conta)
        return int((await self.session.execute(stmt)).scalar_one())

    async def ultimo_agendado(self, *, conta: str | None = None) -> datetime | None:
        """Maior `scheduled_for` já marcado (pra o cron continuar o calendário a
        partir do último slot, sem empilhar tudo no mesmo dia)."""
        stmt = select(func.max(LinkedinPost.scheduled_for))
        if conta:
            stmt = stmt.where(LinkedinPost.conta == conta)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def existe_do_blog(self, blog_post_id: uuid.UUID, conta: str) -> bool:
        """Já existe post de LinkedIn pra este post de blog + conta? (idempotência
        do cross-agent — não duplicar divulgação)."""
        stmt = select(LinkedinPost.id).where(
            LinkedinPost.origem_blog_post_id == blog_post_id,
            LinkedinPost.conta == conta,
        )
        return (await self.session.execute(stmt)).first() is not None

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.blog.pauta import BlogPauta
from app.db.models.blog.post import BlogPost
from app.db.models.blog.redirect import BlogRedirect


class BlogRepository:
    """Acesso a dados do blog. O recorte PÚBLICO (só publicado e já no ar) mora
    aqui pra não vazar rascunho por engano em nenhum caller."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ── Recorte público (status=publicado E published_at <= agora) ───
    def _visivel(self):
        agora = datetime.now(UTC)
        return (BlogPost.status == "publicado") & (
            BlogPost.published_at.is_not(None)
        ) & (BlogPost.published_at <= agora)

    async def listar_publicados(
        self, *, limit: int = 20, offset: int = 0, category: str | None = None
    ) -> list[BlogPost]:
        stmt = select(BlogPost).where(self._visivel())
        if category:
            stmt = stmt.where(BlogPost.category == category)
        stmt = stmt.order_by(BlogPost.published_at.desc()).limit(limit).offset(offset)
        return list((await self.session.execute(stmt)).scalars().all())

    async def contar_publicados(self, *, category: str | None = None) -> int:
        stmt = select(func.count()).select_from(BlogPost).where(self._visivel())
        if category:
            stmt = stmt.where(BlogPost.category == category)
        return int((await self.session.execute(stmt)).scalar_one())

    async def get_publicado_por_slug(self, slug: str) -> BlogPost | None:
        stmt = select(BlogPost).where(self._visivel(), BlogPost.slug == slug)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def listar_para_sitemap(self) -> list[BlogPost]:
        """Só os campos que o sitemap/feed precisam, ordenado por recência."""
        stmt = (
            select(BlogPost)
            .where(self._visivel(), BlogPost.noindex.is_(False))
            .order_by(BlogPost.published_at.desc())
        )
        return list((await self.session.execute(stmt)).scalars().all())

    # ── Redirects (301 ao renomear slug) ─────────────────────────
    async def resolver_redirect(self, slug_antigo: str) -> str | None:
        stmt = select(BlogRedirect.slug_novo).where(
            BlogRedirect.slug_antigo == slug_antigo
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def create_redirect(self, slug_antigo: str, slug_novo: str) -> BlogRedirect:
        red = BlogRedirect(slug_antigo=slug_antigo, slug_novo=slug_novo)
        self.session.add(red)
        await self.session.commit()
        await self.session.refresh(red)
        return red

    # ── CRUD (admin — usado pelo B1+; read público não passa por aqui) ──
    async def create(self, dados: dict) -> BlogPost:
        post = BlogPost(**dados)
        self.session.add(post)
        await self.session.commit()
        await self.session.refresh(post)
        return post

    async def get(self, pid: uuid.UUID) -> BlogPost | None:
        return await self.session.get(BlogPost, pid)

    async def get_por_slug(self, slug: str) -> BlogPost | None:
        stmt = select(BlogPost).where(BlogPost.slug == slug)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def listar(
        self, *, status: str | None = None, limit: int = 100, offset: int = 0
    ) -> list[BlogPost]:
        stmt = select(BlogPost)
        if status:
            stmt = stmt.where(BlogPost.status == status)
        stmt = stmt.order_by(BlogPost.updated_at.desc()).limit(limit).offset(offset)
        return list((await self.session.execute(stmt)).scalars().all())

    async def update(self, pid: uuid.UUID, dados: dict) -> BlogPost | None:
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
            delete(BlogPost).where(BlogPost.id == pid)
        )
        await self.session.commit()
        return result.rowcount > 0

    async def slug_existe(self, slug: str, *, exceto: uuid.UUID | None = None) -> bool:
        stmt = select(BlogPost.id).where(BlogPost.slug == slug)
        if exceto:
            stmt = stmt.where(BlogPost.id != exceto)
        return (await self.session.execute(stmt)).first() is not None

    # ── Pautas (motor de pauta — B3) ─────────────────────────────
    async def create_pauta(self, dados: dict) -> BlogPauta:
        pauta = BlogPauta(**dados)
        self.session.add(pauta)
        await self.session.commit()
        await self.session.refresh(pauta)
        return pauta

    async def create_pautas(self, lista: list[dict]) -> list[BlogPauta]:
        """Insere várias de uma vez (saída do motor) — 1 commit."""
        pautas = [BlogPauta(**d) for d in lista]
        self.session.add_all(pautas)
        await self.session.commit()
        for p in pautas:
            await self.session.refresh(p)
        return pautas

    async def get_pauta(self, pid: uuid.UUID) -> BlogPauta | None:
        return await self.session.get(BlogPauta, pid)

    async def listar_pautas(self, *, status: str | None = None) -> list[BlogPauta]:
        stmt = select(BlogPauta)
        if status:
            stmt = stmt.where(BlogPauta.status == status)
        stmt = stmt.order_by(BlogPauta.score.desc(), BlogPauta.created_at.desc())
        return list((await self.session.execute(stmt)).scalars().all())

    async def titulos_pauta_existentes(self) -> set[str]:
        """Títulos já no backlog (pra o motor não repetir pauta)."""
        rows = await self.session.execute(select(BlogPauta.titulo))
        return {t.casefold() for (t,) in rows.all()}

    async def update_pauta(self, pid: uuid.UUID, dados: dict) -> BlogPauta | None:
        pauta = await self.get_pauta(pid)
        if pauta is None:
            return None
        for campo, valor in dados.items():
            setattr(pauta, campo, valor)
        await self.session.commit()
        await self.session.refresh(pauta)
        return pauta

    async def delete_pauta(self, pid: uuid.UUID) -> bool:
        result = await self.session.execute(
            delete(BlogPauta).where(BlogPauta.id == pid)
        )
        await self.session.commit()
        return result.rowcount > 0

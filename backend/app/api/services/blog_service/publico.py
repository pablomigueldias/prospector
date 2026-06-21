"""Leitura PÚBLICA do blog (o site consome via ISR). Só posts publicados e já
no ar — o recorte de visibilidade vive no repositório, não dá pra vazar
rascunho por aqui."""
from __future__ import annotations

from app.api.schemas.blog import BlogListResponse, BlogPostPublic
from app.api.services._helpers import iso as _iso
from app.db.session import get_session
from app.repositories.blog_repository import BlogRepository

from ._base import to_list_item, to_public

# Teto de página (defesa contra scraping pesado na rota pública).
MAX_LIMIT = 50


async def listar(
    *, limit: int = 20, offset: int = 0, category: str | None = None
) -> BlogListResponse:
    limit = max(1, min(limit, MAX_LIMIT))
    offset = max(0, offset)
    async with get_session() as session:
        repo = BlogRepository(session)
        posts = await repo.listar_publicados(
            limit=limit, offset=offset, category=category
        )
        total = await repo.contar_publicados(category=category)
    return BlogListResponse(
        items=[to_list_item(p) for p in posts],
        total=total,
        limit=limit,
        offset=offset,
    )


async def get(slug: str) -> BlogPostPublic | None:
    async with get_session() as session:
        repo = BlogRepository(session)
        post = await repo.get_publicado_por_slug(slug)
        return to_public(post) if post else None


async def resolver_redirect(slug: str) -> str | None:
    """slug antigo → slug novo (301), se existir no mapa de redirects."""
    async with get_session() as session:
        return await BlogRepository(session).resolver_redirect(slug)


async def dados_sitemap() -> list[dict]:
    """Entradas pro sitemap.xml/feed.xml: slug + datas + título/resumo."""
    async with get_session() as session:
        posts = await BlogRepository(session).listar_para_sitemap()
    return [
        {
            "slug": p.slug,
            "title": p.title,
            "excerpt": p.excerpt,
            "category": p.category,
            "author": p.author,
            "published_at": _iso(p.published_at),
            "updated_at": _iso(p.updated_at),
        }
        for p in posts
    ]

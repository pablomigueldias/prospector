"""Smoke do service ADMIN do blog (P5 §6.B1) — CRUD + publicar + redirect.

Bate direto no service (não no HTTP, que exige login), que é onde mora a regra:
slug único, métricas de leitura, gate de publicação e redirect 301 no rename.
Precisa do Postgres de dev migrado. Roda standalone:
    python -m tests.test_blog_admin
"""
from __future__ import annotations

import asyncio

from sqlalchemy import delete

from app.api.schemas.blog import BlogPostCreate, BlogPostUpdate
from app.api.services import blog_service as svc
from app.db.models.blog.redirect import BlogRedirect
from app.db.session import get_session

_SLUG = "teste-admin-crud-blog"
_SLUG_NOVO = "teste-admin-blog-renomeado"


async def _limpar() -> None:
    async with get_session() as s:
        for slug in (_SLUG, _SLUG_NOVO, f"{_SLUG_NOVO}-2"):
            existente = next(
                (p for p in await svc.admin.listar() if p.slug == slug), None
            )
            if existente:
                await svc.admin.deletar(existente.id)
        await s.execute(
            delete(BlogRedirect).where(BlogRedirect.slug_antigo == _SLUG)
        )
        await s.commit()


async def _run() -> None:
    await _limpar()

    print("\n→ Test 1: criar (auto-slug + métricas)")
    p = await svc.admin.criar(
        BlogPostCreate(
            title="Teste Admin: CRUD Blog!",
            slug=_SLUG,
            body_md="# Olá\n\n" + "palavra " * 300,
            category="Teste",
        )
    )
    assert p.slug == _SLUG, p.slug
    assert p.status == "rascunho"
    assert p.reading_time and p.word_count and p.word_count >= 300
    print(f"   slug={p.slug}, rascunho, {p.word_count} palavras, {p.reading_time} min ✓")

    print("\n→ Test 2: rascunho não aparece no público")
    assert await svc.get(p.slug) is None
    print("   público não vê rascunho ✓")

    print("\n→ Test 3: publicar carimba published_at e expõe")
    p2 = await svc.admin.mudar_status(p.id, "publicado")
    assert p2.status == "publicado" and p2.published_at
    assert await svc.get(p.slug) is not None
    print(f"   publicado em {p2.published_at} ✓")

    print("\n→ Test 4: renomear publicado → redirect 301")
    p3 = await svc.admin.atualizar(p.id, BlogPostUpdate(slug=_SLUG_NOVO))
    assert p3.slug == _SLUG_NOVO
    assert await svc.resolver_redirect(_SLUG) == _SLUG_NOVO
    print("   slug antigo redireciona pro novo ✓")

    print("\n→ Test 5: slug duplicado ganha sufixo")
    dup = await svc.admin.criar(BlogPostCreate(title="Teste Admin Blog Renomeado"))
    assert dup.slug == f"{_SLUG_NOVO}-2", dup.slug
    print(f"   {dup.slug} ✓")

    await _limpar()


def main() -> None:
    print("━" * 60)
    print("Smoke — service admin do blog (P5 §6.B1)")
    print("━" * 60)
    asyncio.run(_run())
    print("\n✅ Blog admin OK")


if __name__ == "__main__":
    main()

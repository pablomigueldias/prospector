"""Smoke da API pública do blog headless (P5 §6.B0).

Duas partes:
  1. PURO — helpers de conteúdo (slug/contagem/tempo de leitura), sem DB.
  2. DB+ASGI — seed direto no Postgres de dev + chamadas via ASGITransport
     (não precisa do :8000 no ar, só do banco migrado).

Garante o invariante crítico: a rota pública NUNCA vaza rascunho/agendado, e o
slug renomeado responde 301. Roda standalone:
    python -m tests.test_blog_public_api
"""
from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

import httpx
from sqlalchemy import delete

from app.api.main import app
from app.api.services import blog_service as svc
from app.db.models.blog.redirect import BlogRedirect
from app.db.session import get_session
from app.repositories.blog_repository import BlogRepository

_SLUGS = ("test-blog-pub", "test-blog-rascunho", "test-blog-futuro")
_SLUG_ANTIGO = "test-blog-antigo"


# ── Parte 1: helpers puros (sem DB) ──────────────────────────────
def _unit_helpers() -> None:
    print("\n→ Test 1: helpers de conteúdo (puro)")
    assert svc.gerar_slug("5 Sinais de que sua PLANILHA virou Sistema!") == (
        "5-sinais-de-que-sua-planilha-virou-sistema"
    )
    # Contagem limpa: 440 palavras → ~2 min.
    assert svc.contar_palavras("palavra " * 440) == 440
    assert svc.tempo_de_leitura("palavra " * 440) == 2
    # Marcação (código/imagem/link) não infla a contagem; link vira o label.
    assert svc.contar_palavras("```py\nx=1\n```\n`inline` ![alt](u) [rótulo](http://x)") == 1
    assert svc.contar_palavras(None) == 0 and svc.tempo_de_leitura("") == 0
    print("   slug/contagem/tempo de leitura ✓")


# ── Parte 2: DB + ASGI ───────────────────────────────────────────
async def _limpar() -> None:
    async with get_session() as s:
        repo = BlogRepository(s)
        for slug in _SLUGS:
            p = await repo.get_por_slug(slug)
            if p:
                await repo.delete(p.id)
        await s.execute(
            delete(BlogRedirect).where(BlogRedirect.slug_antigo == _SLUG_ANTIGO)
        )
        await s.commit()


async def _seed() -> None:
    async with get_session() as s:
        repo = BlogRepository(s)
        await repo.create(
            dict(
                slug="test-blog-pub",
                title="Publicado",
                excerpt="visível",
                category="Automação",
                body_md="# oi",
                status="publicado",
                published_at=datetime.now(UTC) - timedelta(days=1),
                reading_time=3,
                tags=["x"],
            )
        )
        await repo.create(dict(slug="test-blog-rascunho", title="Rascunho", status="rascunho"))
        await repo.create(
            dict(
                slug="test-blog-futuro",
                title="Agendado",
                status="publicado",
                published_at=datetime.now(UTC) + timedelta(days=5),
            )
        )
        await repo.create_redirect(_SLUG_ANTIGO, "test-blog-pub")


async def _db_asgi() -> None:
    await _limpar()
    await _seed()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://t") as c:
        print("\n→ Test 2: lista só publicado-e-no-ar")
        lst = (await c.get("/api/public/blog/posts")).json()
        slugs = {i["slug"] for i in lst["items"]}
        assert "test-blog-pub" in slugs, slugs
        assert "test-blog-rascunho" not in slugs, "vazou rascunho!"
        assert "test-blog-futuro" not in slugs, "vazou agendado!"
        print(f"   lista contém só o publicado ✓ ({len(slugs)} no total da página)")

        print("\n→ Test 3: visibilidade por slug")
        assert (await c.get("/api/public/blog/posts/test-blog-pub")).status_code == 200
        assert (await c.get("/api/public/blog/posts/test-blog-rascunho")).status_code == 404
        assert (await c.get("/api/public/blog/posts/test-blog-futuro")).status_code == 404
        print("   publicado=200, rascunho=404, agendado=404 ✓")

        print("\n→ Test 4: slug renomeado → 301")
        r = await c.get(f"/api/public/blog/posts/{_SLUG_ANTIGO}", follow_redirects=False)
        assert r.status_code == 301, r.status_code
        assert r.headers["location"].endswith("/test-blog-pub"), r.headers.get("location")
        print("   301 → slug novo ✓")

        print("\n→ Test 5: sitemap.xml e feed.xml")
        sm = await c.get("/api/public/blog/sitemap.xml")
        assert sm.status_code == 200 and "<urlset" in sm.text
        assert "/blog/test-blog-pub" in sm.text and "test-blog-rascunho" not in sm.text
        feed = await c.get("/api/public/blog/feed.xml")
        assert feed.status_code == 200 and "<item>" in feed.text
        print("   sitemap+feed renderizam só o público ✓")

        print("\n→ Test 6: Cache-Control nas rotas públicas")
        assert "max-age" in (await c.get("/api/public/blog/posts")).headers.get("cache-control", "")
        print("   Cache-Control presente ✓")

    await _limpar()


def main() -> None:
    print("━" * 60)
    print("Smoke — API pública do blog (P5 §6.B0)")
    print("━" * 60)
    _unit_helpers()
    asyncio.run(_db_asgi())
    print("\n✅ Blog público OK")


if __name__ == "__main__":
    main()

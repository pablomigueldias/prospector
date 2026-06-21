"""API PÚBLICA do blog headless (P5 §6.B0).

SEM autenticação (o site `reativesystems.com.br` consome anônimo via ISR) e
read-only — só posts publicados e já no ar. As rotas de escrita (CRUD/gerar/
aprovar) ficam no router admin autenticado (B1+). Respostas trazem
``Cache-Control`` pra CDN/ISR e crawlers respirarem.

Sitemap/feed emitem URLs ABSOLUTAS pro domínio do site (``settings.site_url``),
então o site pode só fazer rewrite de ``/sitemap.xml``/``/feed.xml`` pra cá.
"""
from __future__ import annotations

from datetime import datetime
from email.utils import format_datetime
from xml.sax.saxutils import escape

from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import RedirectResponse

from app.api.schemas.blog import BlogListResponse, BlogPostPublic
from app.api.services import blog_service
from app.config import settings

router = APIRouter(prefix="/api/public/blog", tags=["public:blog"])

# Lista muda pouco; post fica estável. Valores conservadores pro ISR revalidar.
_CACHE_LISTA = "public, max-age=60, s-maxage=300, stale-while-revalidate=600"
_CACHE_POST = "public, max-age=300, s-maxage=3600, stale-while-revalidate=86400"
_CACHE_XML = "public, max-age=600, s-maxage=3600"


def _site(path: str = "") -> str:
    return f"{settings.site_url.rstrip('/')}{path}"


@router.get("/posts", response_model=BlogListResponse, summary="Posts publicados")
async def listar_posts(
    response: Response,
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    category: str | None = Query(None),
) -> BlogListResponse:
    response.headers["Cache-Control"] = _CACHE_LISTA
    return await blog_service.listar(limit=limit, offset=offset, category=category)


@router.get(
    "/posts/{slug}",
    response_model=BlogPostPublic,
    summary="Post publicado por slug (301 se o slug foi renomeado)",
)
async def get_post(slug: str, response: Response):
    post = await blog_service.get(slug)
    if post is None:
        # Slug renomeado? Redireciona pro novo (preserva SEO). fetch do site
        # segue o 301 transparente e recebe o JSON do post atual.
        novo = await blog_service.resolver_redirect(slug)
        if novo:
            return RedirectResponse(
                url=router.url_path_for("get_post", slug=novo), status_code=301
            )
        raise HTTPException(status_code=404, detail="Post não encontrado.")
    response.headers["Cache-Control"] = _CACHE_POST
    return post


@router.get("/sitemap.xml", include_in_schema=False)
async def sitemap() -> Response:
    entradas = await blog_service.dados_sitemap()
    urls = [
        "<url>"
        f"<loc>{escape(_site('/blog/' + e['slug']))}</loc>"
        + (
            f"<lastmod>{e['updated_at'][:10]}</lastmod>"
            if e.get("updated_at")
            else ""
        )
        + "<changefreq>weekly</changefreq>"
        "</url>"
        for e in entradas
    ]
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        + "".join(urls)
        + "</urlset>"
    )
    return Response(
        content=xml,
        media_type="application/xml",
        headers={"Cache-Control": _CACHE_XML},
    )


@router.get("/feed.xml", include_in_schema=False)
async def feed() -> Response:
    entradas = await blog_service.dados_sitemap()
    itens = []
    for e in entradas:
        pub = ""
        if e.get("published_at"):
            try:
                pub = f"<pubDate>{format_datetime(datetime.fromisoformat(e['published_at']))}</pubDate>"
            except ValueError:
                pub = ""
        link = _site("/blog/" + e["slug"])
        itens.append(
            "<item>"
            f"<title>{escape(e['title'])}</title>"
            f"<link>{escape(link)}</link>"
            f"<guid isPermaLink=\"true\">{escape(link)}</guid>"
            + (f"<description>{escape(e['excerpt'])}</description>" if e.get("excerpt") else "")
            + (f"<category>{escape(e['category'])}</category>" if e.get("category") else "")
            + (f"<author>{escape(e['author'])}</author>" if e.get("author") else "")
            + pub
            + "</item>"
        )
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<rss version="2.0"><channel>'
        "<title>Blog — Reative Systems</title>"
        f"<link>{escape(_site('/blog'))}</link>"
        "<description>Automação, dados e sistemas sob medida para PMEs.</description>"
        f"<language>pt-BR</language>"
        + "".join(itens)
        + "</channel></rss>"
    )
    return Response(
        content=xml,
        media_type="application/xml",
        headers={"Cache-Control": _CACHE_XML},
    )

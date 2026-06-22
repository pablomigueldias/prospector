"""Núcleo do service de blog: erro de negócio, conversores model→schema e
helpers de conteúdo (slug, contagem de palavras, tempo de leitura).

Reusado pelos módulos (público hoje; admin/agente no B1+)."""
from __future__ import annotations

import re
import uuid

from slugify import slugify

from app.analyzers.llm_provider import gerar_texto
from app.api.schemas.blog import (
    BlogPautaItem,
    BlogPostAdmin,
    BlogPostListItem,
    BlogPostPublic,
    SeoPublic,
    TocItem,
)
from app.api.services._helpers import iso as _iso
from app.api.services._helpers import parse_uuid
from app.config import settings
from app.db.models.blog.pauta import BlogPauta
from app.db.models.blog.post import BlogPost
from app.utils.logger import get_logger

logger = get_logger()

# Velocidade média de leitura em PT (palavras/min) — referência editorial.
PALAVRAS_POR_MINUTO = 220


class BlogError(Exception):
    """Erro de negócio do blog — vira HTTP 400/404 no router."""


def _uuid(valor: str, label: str = "id") -> uuid.UUID:
    return parse_uuid(valor, erro=BlogError, label=label)


def _chamar_llm(prompt: str, *, operacao: str) -> str:
    try:
        # Blog usa um modelo Pro (settings.gemini_model_blog) — qualidade do texto
        # importa mais aqui; volume é baixo. Vazio → cai no flash padrão.
        return gerar_texto(
            prompt, json_mode=True, agente="blog", operacao=operacao,
            model=(settings.gemini_model_blog or None),
        )
    except Exception as e:
        logger.error("blog: falha na LLM ({}): {}", operacao, e)
        raise BlogError(
            "Não consegui falar com o modelo de IA. "
            "Verifique a conexão/configuração e tente de novo."
        )


# ── Helpers de conteúdo ──────────────────────────────────────────

def gerar_slug(titulo: str) -> str:
    """Slug amigável e estável a partir do título."""
    return slugify(titulo, max_length=160)


def contar_palavras(markdown: str | None) -> int:
    """Conta palavras ignorando marcação Markdown comum (links, imagens, código,
    headings) — base honesta pro tempo de leitura."""
    if not markdown:
        return 0
    texto = re.sub(r"```.*?```", " ", markdown, flags=re.DOTALL)  # blocos de código
    texto = re.sub(r"`[^`]*`", " ", texto)                        # código inline
    texto = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", texto)           # imagens
    texto = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", texto)        # links → label
    texto = re.sub(r"[#>*_~`-]", " ", texto)                      # marcação
    return len([p for p in texto.split() if p.strip()])


def tempo_de_leitura(markdown: str | None) -> int:
    """Minutos (mínimo 1) com base na contagem de palavras."""
    palavras = contar_palavras(markdown)
    return max(1, round(palavras / PALAVRAS_POR_MINUTO)) if palavras else 0


# ── Conversores model → schema ───────────────────────────────────

def _toc(post: BlogPost) -> list[TocItem]:
    itens = post.toc or []
    return [TocItem(id=i.get("id", ""), label=i.get("label", "")) for i in itens]


def _seo(post: BlogPost) -> SeoPublic:
    return SeoPublic(
        meta_description=post.meta_description,
        keyword_alvo=post.keyword_alvo,
        keywords=post.keywords or [],
        og_image=post.og_image or post.cover_url,
        og_title=post.og_title or post.title,
        og_description=post.og_description or post.meta_description or post.excerpt,
        noindex=post.noindex,
    )


def to_list_item(post: BlogPost) -> BlogPostListItem:
    return BlogPostListItem(
        slug=post.slug,
        title=post.title,
        excerpt=post.excerpt,
        category=post.category,
        cover_url=post.cover_url,
        cover_alt=post.cover_alt,
        cover_class=post.cover_class,
        author=post.author,
        tags=post.tags or [],
        reading_time=post.reading_time,
        published_at=_iso(post.published_at),
        updated_at=_iso(post.updated_at),
    )


def to_admin(post: BlogPost) -> BlogPostAdmin:
    return BlogPostAdmin(
        id=str(post.id),
        slug=post.slug,
        title=post.title,
        excerpt=post.excerpt,
        category=post.category,
        body_md=post.body_md,
        toc=_toc(post),
        cover_url=post.cover_url,
        cover_alt=post.cover_alt,
        cover_class=post.cover_class,
        imagens=post.imagens or [],
        status=post.status,
        author=post.author,
        lang=post.lang,
        tags=post.tags or [],
        reading_time=post.reading_time,
        word_count=post.word_count,
        noindex=post.noindex,
        meta_description=post.meta_description,
        keyword_alvo=post.keyword_alvo,
        keywords=post.keywords or [],
        og_image=post.og_image,
        og_title=post.og_title,
        og_description=post.og_description,
        fonte=post.fonte,
        published_at=_iso(post.published_at),
        created_at=_iso(post.created_at),
        updated_at=_iso(post.updated_at),
    )


def to_pauta_item(p: BlogPauta) -> BlogPautaItem:
    return BlogPautaItem(
        id=str(p.id),
        titulo=p.titulo,
        resumo=p.resumo,
        keyword_alvo=p.keyword_alvo,
        intencao=p.intencao,
        publico=p.publico,
        estagio_funil=p.estagio_funil,
        fonte=p.fonte,
        score=p.score,
        status=p.status,
        notas=p.notas,
        post_id=str(p.post_id) if p.post_id else None,
        created_at=_iso(p.created_at),
        updated_at=_iso(p.updated_at),
    )


# Marcador {{IMG: ...}} que o redator insere; some no público se ficar sem gerar.
_MARCADOR_IMG_PUB = re.compile(r"\{\{\s*IMG:.*?\}\}", re.IGNORECASE | re.DOTALL)


def _limpar_marcadores(md: str | None) -> str | None:
    """Tira marcadores `{{IMG:...}}` NÃO preenchidos — defesa pra nunca vazarem no
    site (se o Pablo publicar sem gerar a imagem). O editor (admin) ainda os vê."""
    if not md:
        return md
    limpo = _MARCADOR_IMG_PUB.sub("", md)
    return re.sub(r"\n{3,}", "\n\n", limpo).strip()


def to_public(post: BlogPost) -> BlogPostPublic:
    return BlogPostPublic(
        slug=post.slug,
        title=post.title,
        excerpt=post.excerpt,
        category=post.category,
        body_md=_limpar_marcadores(post.body_md),
        toc=_toc(post),
        cover_url=post.cover_url,
        cover_alt=post.cover_alt,
        cover_class=post.cover_class,
        imagens=post.imagens or [],
        author=post.author,
        lang=post.lang,
        tags=post.tags or [],
        reading_time=post.reading_time,
        word_count=post.word_count,
        published_at=_iso(post.published_at),
        updated_at=_iso(post.updated_at),
        seo=_seo(post),
    )

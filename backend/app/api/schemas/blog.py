"""Schemas do Blog headless (P5 §6) — site Reative consome a API pública.

DTOs em snake_case (convenção da API); o site mapeia pro seu próprio shape
camelCase. Separa o que é PÚBLICO (read-only, só publicado) do que é ADMIN
(CRUD/gerar/aprovar, B1+).
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

# ══════════════════════════════════════════════════════════════════
# SEO embutido no DTO público (o site monta JSON-LD/meta a partir daqui)
# ══════════════════════════════════════════════════════════════════

class SeoPublic(BaseModel):
    meta_description: str | None = None
    keyword_alvo: str | None = None
    keywords: list[str] = Field(default_factory=list)
    og_image: str | None = None
    og_title: str | None = None
    og_description: str | None = None
    noindex: bool = False


# ══════════════════════════════════════════════════════════════════
# Público — list item (leve, pro grid do blog)
# ══════════════════════════════════════════════════════════════════

class BlogPostListItem(BaseModel):
    slug: str
    title: str
    excerpt: str | None = None
    category: str | None = None
    cover_url: str | None = None
    cover_alt: str | None = None
    cover_class: str | None = None  # fallback CSS enquanto migra do site antigo
    author: str
    tags: list[str] = Field(default_factory=list)
    reading_time: int | None = None
    published_at: str | None = None
    updated_at: str | None = None


class BlogListResponse(BaseModel):
    items: list[BlogPostListItem]
    total: int
    limit: int
    offset: int


# ══════════════════════════════════════════════════════════════════
# Público — post completo (página do artigo)
# ══════════════════════════════════════════════════════════════════

class TocItem(BaseModel):
    id: str
    label: str


class BlogPostPublic(BaseModel):
    slug: str
    title: str
    excerpt: str | None = None
    category: str | None = None
    body_md: str | None = None
    toc: list[TocItem] = Field(default_factory=list)
    cover_url: str | None = None
    cover_alt: str | None = None
    cover_class: str | None = None
    imagens: list[dict] = Field(default_factory=list)
    author: str
    lang: str
    tags: list[str] = Field(default_factory=list)
    reading_time: int | None = None
    word_count: int | None = None
    published_at: str | None = None
    updated_at: str | None = None
    seo: SeoPublic


# ══════════════════════════════════════════════════════════════════
# Admin — CRUD/gerar/publicar (autenticado, B1+)
# ══════════════════════════════════════════════════════════════════

class BlogPostCreate(BaseModel):
    title: str
    slug: str | None = None  # gerado do título se vazio
    excerpt: str | None = None
    category: str | None = None
    body_md: str | None = None
    toc: list[TocItem] | None = None
    cover_url: str | None = None
    cover_alt: str | None = None
    cover_class: str | None = None
    imagens: list[dict] | None = None
    author: str | None = None
    lang: str | None = None
    tags: list[str] | None = None
    noindex: bool | None = None
    meta_description: str | None = None
    keyword_alvo: str | None = None
    keywords: list[str] | None = None
    og_image: str | None = None
    og_title: str | None = None
    og_description: str | None = None
    fonte: str | None = None
    published_at: datetime | None = None  # agendar publicação no futuro


class BlogPostUpdate(BaseModel):
    """Tudo opcional — patch parcial. `None` não mexe no campo."""

    title: str | None = None
    slug: str | None = None
    excerpt: str | None = None
    category: str | None = None
    body_md: str | None = None
    toc: list[TocItem] | None = None
    cover_url: str | None = None
    cover_alt: str | None = None
    cover_class: str | None = None
    imagens: list[dict] | None = None
    author: str | None = None
    lang: str | None = None
    tags: list[str] | None = None
    noindex: bool | None = None
    meta_description: str | None = None
    keyword_alvo: str | None = None
    keywords: list[str] | None = None
    og_image: str | None = None
    og_title: str | None = None
    og_description: str | None = None
    fonte: str | None = None
    published_at: datetime | None = None


class BlogPostAdmin(BaseModel):
    """Visão completa pro studio (todos os campos + estado)."""

    id: str
    slug: str
    title: str
    excerpt: str | None = None
    category: str | None = None
    body_md: str | None = None
    toc: list[TocItem] = Field(default_factory=list)
    cover_url: str | None = None
    cover_alt: str | None = None
    cover_class: str | None = None
    imagens: list[dict] = Field(default_factory=list)
    status: str
    author: str
    lang: str
    tags: list[str] = Field(default_factory=list)
    reading_time: int | None = None
    word_count: int | None = None
    noindex: bool = False
    meta_description: str | None = None
    keyword_alvo: str | None = None
    keywords: list[str] = Field(default_factory=list)
    og_image: str | None = None
    og_title: str | None = None
    og_description: str | None = None
    fonte: str | None = None
    published_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class BlogStatusUpdate(BaseModel):
    status: str  # rascunho | aprovado | publicado | arquivado


# ══════════════════════════════════════════════════════════════════
# Agente (B2) — redator (brief → artigo) + checklist SEO
# ══════════════════════════════════════════════════════════════════

class BlogBriefRequest(BaseModel):
    tema: str
    keyword_alvo: str | None = None
    intencao: str | None = None  # informacional | comercial | navegacional
    publico: str | None = None   # recrutador | cliente
    tom: str | None = None
    pontos: str | None = None    # pontos que o post deve cobrir


class BlogRedacao(BaseModel):
    """Saída do redator — preenche o editor pro Pablo revisar (checkpoint)."""

    title: str
    slug: str | None = None
    excerpt: str | None = None
    meta_description: str | None = None
    keyword_alvo: str | None = None
    keywords: list[str] = Field(default_factory=list)
    category: str | None = None
    tags: list[str] = Field(default_factory=list)
    toc: list[TocItem] = Field(default_factory=list)
    body_md: str
    og_title: str | None = None
    og_description: str | None = None


class ChecklistSeoRequest(BaseModel):
    title: str | None = None
    slug: str | None = None
    body_md: str | None = None
    excerpt: str | None = None
    meta_description: str | None = None
    keyword_alvo: str | None = None


class ChecklistItem(BaseModel):
    id: str
    label: str
    status: str  # ok | warn | fail
    dica: str | None = None


class ChecklistSeoResponse(BaseModel):
    score: int          # 0-100
    nivel: str          # ruim | ok | bom | otimo
    itens: list[ChecklistItem]


# ══════════════════════════════════════════════════════════════════
# Motor de pauta (B3) — backlog editorial
# ══════════════════════════════════════════════════════════════════

class BlogPautaItem(BaseModel):
    id: str
    titulo: str
    resumo: str | None = None
    keyword_alvo: str | None = None
    intencao: str | None = None
    publico: str | None = None
    estagio_funil: str | None = None
    fonte: str
    score: int
    status: str
    notas: str | None = None
    post_id: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class BlogPautaGerarRequest(BaseModel):
    quantidade: int = 6
    fontes: list[str] | None = None   # projeto | seo | tendencia (default: as 3)
    publico: str | None = None        # foco: recrutador | cliente
    sementes: str | None = None       # keywords/temas que o Pablo quer mirar
    tendencias: str | None = None     # tendências do setor pra considerar


class BlogPautaManualCreate(BaseModel):
    titulo: str
    resumo: str | None = None
    keyword_alvo: str | None = None
    intencao: str | None = None
    publico: str | None = None
    estagio_funil: str | None = None


class GerarImagemRequest(BaseModel):
    prompt: str
    papel: str = "cover"          # cover | secao
    aspect_ratio: str = "16:9"    # 16:9 | 1:1 | 4:3 | 9:16


class CapaSugestao(BaseModel):
    conceito: str
    descricao: str | None = None
    prompt: str
    aspect_ratio: str = "16:9"


class CapaSugestoesResponse(BaseModel):
    sugestoes: list[CapaSugestao]


class BlogPautaUpdate(BaseModel):
    titulo: str | None = None
    resumo: str | None = None
    keyword_alvo: str | None = None
    intencao: str | None = None
    publico: str | None = None
    estagio_funil: str | None = None
    score: int | None = None
    status: str | None = None
    notas: str | None = None

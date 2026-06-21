"""Coordenador do blog (P5 §6.B4): 1 clique pauta → rascunho completo.

Encadeia o que já existe (redator B2 + CRUD B1): pega a pauta, manda a IA
escrever o artigo, salva como RASCUNHO e liga a pauta ao post. PARA no rascunho
— o Pablo revisa e publica (checkpoint). Espelha a cadeia do coordenador do
freela, mas enxuto."""
from app.api.schemas.blog import BlogBriefRequest, BlogPostAdmin, BlogPostCreate
from app.db.session import get_session
from app.repositories.blog_repository import BlogRepository

from . import admin, agente
from ._base import BlogError, _uuid, to_pauta_item


async def escrever_pauta(pauta_id: str) -> BlogPostAdmin:
    """pauta → artigo Markdown (IA) → post rascunho → pauta marcada 'escrita'."""
    pid = _uuid(pauta_id, "pauta_id")
    async with get_session() as session:
        pauta = await BlogRepository(session).get_pauta(pid)
        if pauta is None:
            raise BlogError("Pauta não encontrada.")
        snap = to_pauta_item(pauta)

    # 1) Redator (B2) — ancorado no brief da pauta.
    redacao = await agente.redigir(
        BlogBriefRequest(
            tema=snap.titulo,
            keyword_alvo=snap.keyword_alvo,
            intencao=snap.intencao,
            publico=snap.publico,
            pontos=snap.resumo,
        )
    )

    # 2) Salva como RASCUNHO (admin.criar gera slug/métricas e valida).
    post = await admin.criar(
        BlogPostCreate(
            title=redacao.title,
            slug=redacao.slug,
            excerpt=redacao.excerpt,
            category=redacao.category,
            body_md=redacao.body_md,
            tags=redacao.keywords or None,
            keyword_alvo=redacao.keyword_alvo or snap.keyword_alvo,
            meta_description=redacao.meta_description,
            og_title=redacao.og_title,
            og_description=redacao.og_description,
        )
    )

    # 3) Liga a pauta ao post (status 'escrita').
    async with get_session() as session:
        await BlogRepository(session).update_pauta(
            pid, {"status": "escrita", "post_id": _uuid(post.id, "post_id")}
        )
    return post

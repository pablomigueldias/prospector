"""CRUD/gerar/publicar do blog (autenticado, B1+). Toda escrita passa por aqui:
gera slug, recalcula métricas de leitura, valida unicidade e cria redirect 301
quando um post publicado é renomeado."""
from __future__ import annotations

from datetime import UTC, datetime

from app.api.schemas.blog import (
    BlogPostAdmin,
    BlogPostCreate,
    BlogPostUpdate,
)
from app.db.models.blog.post import STATUS_POST
from app.db.session import get_session
from app.repositories.blog_repository import BlogRepository

from ._base import (
    BlogError,
    _uuid,
    contar_palavras,
    gerar_slug,
    tempo_de_leitura,
    to_admin,
)


async def _slug_unico(repo: BlogRepository, base: str, exceto=None) -> str:
    """Garante slug único: 'titulo', 'titulo-2', 'titulo-3'…"""
    slug = base or "post"
    n = 2
    while await repo.slug_existe(slug, exceto=exceto):
        slug = f"{base}-{n}"
        n += 1
    return slug


def _aplicar_metricas(dados: dict) -> None:
    if "body_md" in dados:
        dados["word_count"] = contar_palavras(dados.get("body_md"))
        dados["reading_time"] = tempo_de_leitura(dados.get("body_md"))


def _toc_to_db(toc) -> list[dict] | None:
    if toc is None:
        return None
    return [{"id": t.id, "label": t.label} for t in toc]


async def listar(status: str | None = None) -> list[BlogPostAdmin]:
    if status and status not in STATUS_POST:
        raise BlogError(f"status inválido: {status!r}")
    async with get_session() as session:
        posts = await BlogRepository(session).listar(status=status, limit=500)
        return [to_admin(p) for p in posts]


async def get(post_id: str) -> BlogPostAdmin:
    pid = _uuid(post_id, "post_id")
    async with get_session() as session:
        post = await BlogRepository(session).get(pid)
        if post is None:
            raise BlogError("Post não encontrado.")
        return to_admin(post)


async def criar(payload: BlogPostCreate) -> BlogPostAdmin:
    dados = payload.model_dump(exclude_none=True)
    titulo = dados.get("title", "").strip()
    if not titulo:
        raise BlogError("Título é obrigatório.")
    dados["toc"] = _toc_to_db(payload.toc)
    if dados.get("toc") is None:
        dados.pop("toc", None)
    _aplicar_metricas(dados)
    async with get_session() as session:
        repo = BlogRepository(session)
        base = gerar_slug(dados.get("slug") or titulo)
        dados["slug"] = await _slug_unico(repo, base)
        post = await repo.create(dados)
        return to_admin(post)


async def atualizar(post_id: str, payload: BlogPostUpdate) -> BlogPostAdmin:
    pid = _uuid(post_id, "post_id")
    dados = payload.model_dump(exclude_unset=True, exclude_none=True)
    if "toc" in dados:
        dados["toc"] = _toc_to_db(payload.toc)
    _aplicar_metricas(dados)
    async with get_session() as session:
        repo = BlogRepository(session)
        atual = await repo.get(pid)
        if atual is None:
            raise BlogError("Post não encontrado.")

        # Renomeou o slug? Normaliza, garante unicidade e — se já estava
        # publicado — deixa um redirect 301 do slug antigo.
        if dados.get("slug") and dados["slug"] != atual.slug:
            novo = await _slug_unico(repo, gerar_slug(dados["slug"]), exceto=pid)
            if atual.status == "publicado":
                await repo.create_redirect(atual.slug, novo)
            dados["slug"] = novo

        post = await repo.update(pid, dados)
        return to_admin(post)


async def mudar_status(post_id: str, status: str) -> BlogPostAdmin:
    if status not in STATUS_POST:
        raise BlogError(f"status inválido: {status!r}")
    pid = _uuid(post_id, "post_id")
    async with get_session() as session:
        repo = BlogRepository(session)
        atual = await repo.get(pid)
        if atual is None:
            raise BlogError("Post não encontrado.")
        dados: dict = {"status": status}
        # Publicar pela 1ª vez carimba a data (vira o gate de visibilidade).
        primeira_publicacao = status == "publicado" and atual.published_at is None
        if primeira_publicacao:
            dados["published_at"] = datetime.now(UTC)
        post = await repo.update(pid, dados)
        resultado = to_admin(post)

    # Cross-agent (L3/B5): ao publicar pela 1ª vez, gera um rascunho de
    # divulgação no LinkedIn. Best-effort — uma falha aqui NÃO derruba a
    # publicação do blog (o agente LinkedIn é opcional).
    if primeira_publicacao:
        await _divulgar_no_linkedin(post)

    return resultado


async def _divulgar_no_linkedin(post) -> None:
    try:
        from app.api.services import linkedin_service
        await linkedin_service.coordenador.do_blog(
            blog_post_id=post.id,
            slug=post.slug,
            title=post.title,
            excerpt=post.excerpt,
        )
    except Exception as e:  # noqa: BLE001 — divulgação é best-effort
        from app.utils.logger import get_logger
        get_logger().warning("blog→linkedin: falha ao gerar rascunho ({})", e)


async def deletar(post_id: str) -> None:
    pid = _uuid(post_id, "post_id")
    async with get_session() as session:
        ok = await BlogRepository(session).delete(pid)
        if not ok:
            raise BlogError("Post não encontrado.")

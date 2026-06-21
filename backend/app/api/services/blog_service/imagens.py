"""Imagens do blog (P5 §6 B-IMG): gera capa/seções via Imagen e sobe pro MinIO,
ou recebe a versão FINAL que o Pablo editou fora e reenviou.

Fluxo (decisão do Pablo): a IA gera um RASCUNHO de imagem → fica no post pra ele
baixar, ajustar fora e reenviar a final ANTES de publicar. Tudo no MinIO com URL
pública permanente (bucket de leitura pública)."""
from __future__ import annotations

import asyncio
import re
import uuid

from app.analyzers.blog.capa.parser import parse_resposta as parse_capas
from app.analyzers.blog.capa.prompt_builder import construir_prompt as construir_capas
from app.analyzers.gemini import image_client
from app.api.schemas.blog import BlogPostAdmin, CapaSugestao, CapaSugestoesResponse
from app.config import settings
from app.db.session import get_session
from app.repositories.blog_repository import BlogRepository
from app.utils.s3_storage import get_storage

from ._base import BlogError, _chamar_llm, _uuid, to_admin

_EXT = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp"}
_PAPEIS = {"cover", "secao"}

# Marcador que o redator insere no corpo: {{IMG: prompt em inglês || alt em PT}}.
# O passo `gerar_conteudo` troca cada um por ![alt](url) apontando pro MinIO.
_MARCADOR_IMG = re.compile(
    r"\{\{\s*IMG:\s*(?P<prompt>.+?)\s*\|\|\s*(?P<alt>.+?)\s*\}\}",
    re.IGNORECASE | re.DOTALL,
)


def _key(post_id: str, papel: str, mime: str) -> str:
    ext = _EXT.get(mime, "png")
    return f"posts/{post_id}/{papel}-{uuid.uuid4().hex}.{ext}"


def _subir(data: bytes, mime: str, key: str) -> str:
    """Sobe pro bucket público do blog e devolve a URL permanente. (sync)"""
    storage = get_storage()
    bucket = settings.s3_bucket_blog
    storage.ensure_public_bucket(bucket)
    storage.upload_bytes(bucket, key, data, content_type=mime)
    return storage.public_url(bucket, key)


async def _aplicar_no_post(
    post_id: str, papel: str, url: str, *, origem: str, prompt: str | None, alt: str | None
) -> BlogPostAdmin:
    pid = _uuid(post_id, "post_id")
    async with get_session() as session:
        repo = BlogRepository(session)
        post = await repo.get(pid)
        if post is None:
            raise BlogError("Post não encontrado.")
        imagens = list(post.imagens or [])
        imagens.append(
            {"papel": papel, "url": url, "origem": origem, "prompt": prompt, "alt": alt}
        )
        dados: dict = {"imagens": imagens}
        if papel == "cover":
            dados["cover_url"] = url
            if alt:
                dados["cover_alt"] = alt
        atualizado = await repo.update(pid, dados)
        return to_admin(atualizado)


async def sugerir_capas(post_id: str) -> CapaSugestoesResponse:
    """3 conceitos de capa sob medida pro post (IA) — o Pablo escolhe e gera."""
    pid = _uuid(post_id, "post_id")
    async with get_session() as session:
        post = await BlogRepository(session).get(pid)
        if post is None:
            raise BlogError("Post não encontrado.")
        ctx = (post.title, post.excerpt, post.keyword_alvo, post.category)

    prompt = construir_capas(
        title=ctx[0], excerpt=ctx[1], keyword_alvo=ctx[2], category=ctx[3]
    )
    cru = _chamar_llm(prompt, operacao="sugerir_capas")
    sugestoes = parse_capas(cru)
    if not sugestoes:
        raise BlogError("A IA não retornou sugestões de capa. Tente de novo.")
    return CapaSugestoesResponse(sugestoes=[CapaSugestao(**s) for s in sugestoes])


async def gerar(
    post_id: str,
    *,
    papel: str = "cover",
    prompt: str,
    aspect_ratio: str = "16:9",
) -> BlogPostAdmin:
    if papel not in _PAPEIS:
        raise BlogError(f"papel inválido: {papel!r} (use cover|secao)")
    if not (prompt or "").strip():
        raise BlogError("Descreva a imagem (prompt).")
    try:
        data, mime = await asyncio.to_thread(
            image_client.gerar_imagem, prompt, aspect_ratio=aspect_ratio
        )
    except Exception as e:
        raise BlogError(f"Não consegui gerar a imagem: {e}")
    url = await asyncio.to_thread(_subir, data, mime, _key(post_id, papel, mime))
    return await _aplicar_no_post(
        post_id, papel, url, origem="gerada", prompt=prompt, alt=None
    )


async def gerar_conteudo(
    post_id: str, *, aspect_ratio: str = "16:9"
) -> BlogPostAdmin:
    """Varre os marcadores `{{IMG: prompt || alt}}` no corpo, gera cada imagem via
    Imagen, sobe pro MinIO e troca o marcador por `![alt](url)` Markdown — deixa o
    post ilustrado, não só com capa. Opera no rascunho SALVO (use o body do banco)."""
    pid = _uuid(post_id, "post_id")
    async with get_session() as session:
        post = await BlogRepository(session).get(pid)
        if post is None:
            raise BlogError("Post não encontrado.")
        body = post.body_md or ""
        imagens = list(post.imagens or [])

    matches = list(_MARCADOR_IMG.finditer(body))
    if not matches:
        raise BlogError(
            "Nenhum marcador de imagem no corpo. Insira `{{IMG: descrição em "
            "inglês || alt em português}}` no texto (o redator já insere alguns) "
            "e salve o rascunho antes de gerar."
        )

    for m in matches:
        prompt = m.group("prompt").strip()
        alt = m.group("alt").strip()
        try:
            data, mime = await asyncio.to_thread(
                image_client.gerar_imagem, prompt, aspect_ratio=aspect_ratio
            )
        except Exception as e:
            raise BlogError(f"Falha ao gerar imagem do conteúdo: {e}")
        url = await asyncio.to_thread(_subir, data, mime, _key(post_id, "secao", mime))
        # troca só a 1ª ocorrência exata deste marcador (preserva a ordem)
        body = body.replace(m.group(0), f"![{alt}]({url})", 1)
        imagens.append(
            {"papel": "secao", "url": url, "origem": "gerada", "prompt": prompt, "alt": alt}
        )

    async with get_session() as session:
        repo = BlogRepository(session)
        atualizado = await repo.update(pid, {"body_md": body, "imagens": imagens})
        return to_admin(atualizado)


async def upload(
    post_id: str,
    *,
    papel: str,
    data: bytes,
    content_type: str,
    alt: str | None = None,
) -> BlogPostAdmin:
    """Versão FINAL que o Pablo editou fora e reenviou."""
    if papel not in _PAPEIS:
        raise BlogError(f"papel inválido: {papel!r} (use cover|secao)")
    if not data:
        raise BlogError("Arquivo vazio.")
    if content_type not in _EXT:
        raise BlogError(f"Tipo não suportado: {content_type} (use PNG/JPEG/WebP).")
    url = await asyncio.to_thread(
        _subir, data, content_type, _key(post_id, papel, content_type)
    )
    return await _aplicar_no_post(
        post_id, papel, url, origem="editada", prompt=None, alt=alt
    )

"""Direção de arte do LinkedIn (P5 §6.C — L5).

`sugerir` = o agente (social media pro) recomenda a mídia ideal do post (com
roteiro). `gerar_imagem` = gera a imagem por IA (Gemini) e sobe pro MinIO,
reusando o mesmo bucket público do blog. Tudo PARA pro Pablo revisar."""
from __future__ import annotations

import asyncio
import uuid

from app.analyzers.gemini import image_client
from app.analyzers.linkedin.midia.parser import parse_midia
from app.analyzers.linkedin.midia.prompt_builder import construir_prompt
from app.api.schemas.linkedin import LinkedinPostOut
from app.config import settings
from app.db.session import get_session
from app.repositories.linkedin_repository import LinkedinRepository
from app.utils.s3_storage import get_storage

from ._base import LinkedinError, _chamar_llm, _uuid, to_out

_EXT = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp"}


async def sugerir(post_id: str) -> LinkedinPostOut:
    """IA recomenda a mídia do post (tipo + roteiro + prompt) e salva no post."""
    pid = _uuid(post_id, "post_id")
    async with get_session() as session:
        repo = LinkedinRepository(session)
        post = await repo.get(pid)
        if post is None:
            raise LinkedinError("Post não encontrado.")
        prompt = construir_prompt(
            conta=post.conta, formato=post.formato,
            hook=post.hook, body=post.body, titulo=post.titulo,
        )

    cru = _chamar_llm(prompt, operacao="midia")
    sugestao = parse_midia(cru)
    if sugestao is None:
        raise LinkedinError("A IA não retornou uma direção de mídia válida.")

    async with get_session() as session:
        repo = LinkedinRepository(session)
        post = await repo.update(pid, {"midia": sugestao.model_dump()})
        return to_out(post)


def _subir(data: bytes, mime: str, post_id: str) -> str:
    ext = _EXT.get(mime, "png")
    key = f"linkedin/{post_id}/{uuid.uuid4().hex}.{ext}"
    storage = get_storage()
    bucket = settings.s3_bucket_blog  # bucket público já existente
    storage.ensure_public_bucket(bucket)
    storage.upload_bytes(bucket, key, data, content_type=mime)
    return storage.public_url(bucket, key)


async def gerar_imagem(
    post_id: str,
    *,
    prompt: str | None = None,
    alt: str | None = None,
    aspect_ratio: str = "1:1",
) -> LinkedinPostOut:
    """Gera a imagem por IA (Gemini) → MinIO → anexa ao post. Sem `prompt`, usa o
    `prompt_imagem` da sugestão de mídia salva."""
    pid = _uuid(post_id, "post_id")
    async with get_session() as session:
        repo = LinkedinRepository(session)
        post = await repo.get(pid)
        if post is None:
            raise LinkedinError("Post não encontrado.")
        midia = post.midia or {}
        prompt_final = (prompt or midia.get("prompt_imagem") or "").strip()
        if not prompt_final:
            raise LinkedinError(
                "Sem prompt de imagem. Gere a sugestão de mídia primeiro ou "
                "escreva um prompt."
            )
        ratio = aspect_ratio or midia.get("aspect_ratio") or "1:1"
        alt_final = alt or midia.get("alt")
        imagens_atuais = list(post.imagens or [])

    try:
        data, mime = await asyncio.to_thread(
            image_client.gerar_imagem, prompt_final, aspect_ratio=ratio
        )
        url = await asyncio.to_thread(_subir, data, mime, post_id)
    except Exception as e:
        raise LinkedinError(f"Falha ao gerar a imagem: {e}")

    imagens_atuais.append(
        {"url": url, "alt": alt_final, "prompt": prompt_final, "origem": "ia"}
    )
    async with get_session() as session:
        repo = LinkedinRepository(session)
        post = await repo.update(pid, {"imagens": imagens_atuais})
        return to_out(post)

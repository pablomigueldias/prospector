"""Núcleo do service do LinkedIn: erro de negócio, conversor model→schema e
helpers de conteúdo (texto final + contagem de caracteres)."""
from __future__ import annotations

import uuid

from app.analyzers.llm_provider import gerar_texto
from app.api.schemas.linkedin import (
    LinkedinImagem,
    LinkedinPostOut,
    MidiaSugestao,
)
from app.api.services._helpers import iso as _iso
from app.api.services._helpers import parse_uuid
from app.config import settings
from app.db.models.linkedin.post import LinkedinPost
from app.utils.logger import get_logger

logger = get_logger()


class LinkedinError(Exception):
    """Erro de negócio do LinkedIn — vira HTTP 400/404 no router."""


def _uuid(valor: str, label: str = "id") -> uuid.UUID:
    return parse_uuid(valor, erro=LinkedinError, label=label)


def _chamar_llm(prompt: str, *, operacao: str) -> str:
    try:
        # Mesmo modelo Pro do blog (qualidade > volume; presença é baixo volume).
        return gerar_texto(
            prompt, json_mode=True, agente="linkedin", operacao=operacao,
            model=(settings.gemini_model_blog or None),
        )
    except Exception as e:
        logger.error("linkedin: falha na LLM ({}): {}", operacao, e)
        raise LinkedinError(
            "Não consegui falar com o modelo de IA. "
            "Verifique a conexão/configuração e tente de novo."
        )


def texto_final(hook: str | None, body: str | None, cta: str | None) -> str:
    """Junta as partes na ordem em que vão pro LinkedIn (pra contar caracteres
    e pra o front mostrar o preview do que será copiado)."""
    partes = [p.strip() for p in (hook, body, cta) if p and p.strip()]
    return "\n\n".join(partes)


def contar_chars(hook: str | None, body: str | None, cta: str | None) -> int:
    return len(texto_final(hook, body, cta))


def to_out(p: LinkedinPost) -> LinkedinPostOut:
    return LinkedinPostOut(
        id=str(p.id),
        titulo=p.titulo,
        conta=p.conta,
        formato=p.formato,
        hook=p.hook,
        body=p.body,
        cta=p.cta,
        hashtags=p.hashtags or [],
        status=p.status,
        fonte=p.fonte,
        origem_blog_post_id=str(p.origem_blog_post_id) if p.origem_blog_post_id else None,
        scheduled_for=_iso(p.scheduled_for),
        published_at=_iso(p.published_at),
        midia=MidiaSugestao(**p.midia) if p.midia else None,
        imagens=[LinkedinImagem(**i) for i in (p.imagens or [])],
        char_count=p.char_count,
        notas=p.notas,
        created_at=_iso(p.created_at),
        updated_at=_iso(p.updated_at),
    )

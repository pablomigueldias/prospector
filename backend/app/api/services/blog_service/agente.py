"""O AGENTE (B2): redator (brief → artigo Markdown) + checklist SEO.

Para no rascunho: `redigir` devolve a redação pro editor do studio — o Pablo
revisa e só então salva/publica (checkpoint humano). `checklist` é puro
(determinístico) e pode rodar no editor a cada checagem."""
from app.analyzers.blog import checklist_seo
from app.analyzers.blog.redator.parser import parse_resposta
from app.analyzers.blog.redator.prompt_builder import construir_prompt
from app.api.schemas.blog import (
    BlogBriefRequest,
    BlogRedacao,
    ChecklistSeoRequest,
    ChecklistSeoResponse,
)
from app.api.services.pessoal.perfil_service import get_perfil

from ._base import BlogError, _chamar_llm


async def redigir(brief: BlogBriefRequest) -> BlogRedacao:
    if not (brief.tema or "").strip():
        raise BlogError("Informe o tema/título do post.")
    # Perfil é OPCIONAL: sem ele o redator fica no conteúdo educativo (não cita
    # case do Pablo) — a trava anti-mentira mora no prompt.
    perfil = await get_perfil()
    prompt = construir_prompt(
        tema=brief.tema,
        keyword_alvo=brief.keyword_alvo,
        intencao=brief.intencao,
        publico=brief.publico,
        tom=brief.tom,
        pontos=brief.pontos,
        perfil=perfil,
    )
    cru = _chamar_llm(prompt, operacao="redigir")
    redacao = parse_resposta(cru)
    if redacao is None:
        raise BlogError(
            "A IA não retornou um artigo válido. Tente de novo ou ajuste o tema."
        )
    return redacao


def checklist(payload: ChecklistSeoRequest) -> ChecklistSeoResponse:
    return checklist_seo.avaliar(
        title=payload.title,
        slug=payload.slug,
        body_md=payload.body_md,
        excerpt=payload.excerpt,
        meta_description=payload.meta_description,
        keyword_alvo=payload.keyword_alvo,
    )

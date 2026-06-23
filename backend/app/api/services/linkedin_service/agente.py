"""O AGENTE (L1): redator (brief → post pronto pro LinkedIn).

Para no rascunho: `redigir` devolve a redação pro drawer do studio — o Pablo
revisa, ajusta e salva (checkpoint humano). Reusa o Perfil Mestre pra ancorar
qualquer case (anti-mentira mora no prompt)."""
from app.analyzers.linkedin.redator.parser import parse_resposta
from app.analyzers.linkedin.redator.prompt_builder import construir_prompt
from app.api.schemas.linkedin import LinkedinBriefRequest, LinkedinRedacao
from app.api.services.pessoal.perfil_service import get_perfil

from ._base import LinkedinError, _chamar_llm


async def redigir(brief: LinkedinBriefRequest) -> LinkedinRedacao:
    if not (brief.tema or "").strip():
        raise LinkedinError("Informe o tema do post.")
    # Perfil é OPCIONAL: sem ele o redator fica na opinião/conteúdo técnico geral
    # (não cita case do Pablo) — a trava anti-mentira mora no prompt.
    perfil = await get_perfil()
    prompt = construir_prompt(
        tema=brief.tema,
        conta=brief.conta,
        formato=brief.formato,
        publico=brief.publico,
        angulo=brief.angulo,
        tom=brief.tom,
        perfil=perfil,
    )
    cru = _chamar_llm(prompt, operacao="redigir")
    redacao = parse_resposta(cru)
    if redacao is None:
        raise LinkedinError(
            "A IA não retornou um post válido. Tente de novo ou ajuste o tema."
        )
    return redacao

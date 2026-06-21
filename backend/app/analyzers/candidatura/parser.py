"""Parser da resposta do gerador de candidatura."""
from __future__ import annotations

from pydantic import ValidationError

from app.analyzers._json_extract import extrair_json
from app.api.schemas.pessoal import (
    CartaCandidatura,
    EmailCandidatura,
    GerarCandidaturaResponse,
)
from app.utils.logger import get_logger

logger = get_logger()


def parse_resposta(texto_cru: str) -> GerarCandidaturaResponse | None:
    """Converte o texto cru da LLM em GerarCandidaturaResponse, ou None."""
    dados = extrair_json(texto_cru)
    if dados is None:
        return None

    bloco_email = dados.get("email")
    if not isinstance(bloco_email, dict) or not bloco_email.get("corpo"):
        logger.warning("Candidatura: resposta sem e-mail utilizável")
        return None

    try:
        email = EmailCandidatura(**bloco_email)

        variantes = []
        for v in dados.get("variantes_email") or []:
            if isinstance(v, dict) and v.get("corpo"):
                variantes.append(EmailCandidatura(**v))

        carta = None
        bloco_carta = dados.get("carta")
        if isinstance(bloco_carta, dict) and bloco_carta.get("corpo"):
            carta = CartaCandidatura(**bloco_carta)

    except ValidationError as e:
        logger.warning("Candidatura não passou na validação: %s", e)
        return None

    return GerarCandidaturaResponse(
        success=True,
        email=email,
        variantes_email=variantes,
        carta=carta,
    )

"""Parser da resposta do redator de proposta freela."""
from __future__ import annotations

from typing import Optional

from pydantic import ValidationError

from app.analyzers._json_extract import extrair_json
from app.api.schemas.freela import RedacaoProposta
from app.utils.logger import get_logger

logger = get_logger()


def parse_resposta(texto_cru: str) -> Optional[RedacaoProposta]:
    """Converte o texto cru da LLM em RedacaoProposta, ou None se inválido."""
    dados = extrair_json(texto_cru)
    if dados is None:
        return None

    try:
        redacao = RedacaoProposta(**dados)
    except ValidationError as e:
        logger.warning("Redação de proposta freela não validou: %s", e)
        return None

    if not (redacao.texto or "").strip():
        return None

    # Respeita os tetos do seletor (3 projetos / 5 habilidades).
    redacao.projetos_destacados = redacao.projetos_destacados[:3]
    redacao.habilidades_destacadas = redacao.habilidades_destacadas[:5]
    return redacao

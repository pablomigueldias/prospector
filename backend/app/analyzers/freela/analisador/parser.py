"""Parser da resposta do analisador de projeto freela."""
from __future__ import annotations

from typing import Optional

from pydantic import ValidationError

from app.analyzers._json_extract import extrair_json
from app.api.schemas.freela import AnaliseFreela
from app.utils.logger import get_logger

logger = get_logger()


def parse_resposta(texto_cru: str) -> Optional[AnaliseFreela]:
    """Converte o texto cru da LLM em AnaliseFreela, ou None se inválido."""
    dados = extrair_json(texto_cru)
    if dados is None:
        return None

    try:
        analise = AnaliseFreela(**dados)
    except ValidationError as e:
        logger.warning("Análise de projeto freela não validou: %s", e)
        return None

    analise.fit_score = max(0, min(100, int(analise.fit_score or 0)))
    return analise

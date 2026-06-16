"""Parser da resposta do extrator de projeto freela."""
from __future__ import annotations

from typing import Optional

from pydantic import ValidationError

from app.analyzers._json_extract import extrair_json
from app.api.schemas.freela import ExtrairProjetoResponse
from app.utils.logger import get_logger

logger = get_logger()


def parse_resposta(texto_cru: str) -> Optional[ExtrairProjetoResponse]:
    """Converte o texto cru da LLM em ExtrairProjetoResponse, ou None."""
    dados = extrair_json(texto_cru)
    if dados is None:
        return None
    try:
        return ExtrairProjetoResponse(**dados)
    except ValidationError as e:
        logger.warning("Extração de projeto freela não validou: %s", e)
        return None

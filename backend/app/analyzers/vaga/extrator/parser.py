"""Parser da resposta do extrator de vaga (texto/URL → campos do form)."""
from __future__ import annotations

from pydantic import ValidationError

from app.analyzers._json_extract import extrair_json
from app.api.schemas.pessoal import ExtrairVagaResponse
from app.utils.logger import get_logger

logger = get_logger()


def parse_resposta(texto_cru: str) -> ExtrairVagaResponse | None:
    """Converte o texto cru da LLM em ExtrairVagaResponse, ou None."""
    dados = extrair_json(texto_cru)
    if dados is None:
        return None
    try:
        return ExtrairVagaResponse(**dados)
    except ValidationError as e:
        logger.warning("Extração de vaga não validou: {}", e)
        return None

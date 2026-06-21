"""Parser da resposta do NLU."""
from __future__ import annotations

from pydantic import ValidationError

from app.analyzers._json_extract import extrair_json
from app.api.schemas.financas import NLUResult
from app.utils.logger import get_logger

logger = get_logger()


def parse_nlu(texto_cru: str) -> NLUResult | None:
    """Converte o texto cru da LLM num NLUResult validado, ou None."""
    dados = extrair_json(texto_cru)
    if dados is None:
        return None
    try:
        return NLUResult(**dados)
    except ValidationError as e:
        logger.warning("NLU não passou na validação: %s", e)
        return None

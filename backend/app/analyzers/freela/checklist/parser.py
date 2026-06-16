"""Parser da resposta do checklist anti-genérico."""
from __future__ import annotations

from typing import Optional

from pydantic import ValidationError

from app.analyzers._json_extract import extrair_json
from app.api.schemas.freela import ChecklistResponse
from app.utils.logger import get_logger

logger = get_logger()


def parse_resposta(texto_cru: str) -> Optional[ChecklistResponse]:
    """Converte o texto cru da LLM em ChecklistResponse (sem proposta_id), ou None."""
    dados = extrair_json(texto_cru)
    if dados is None:
        return None
    try:
        resp = ChecklistResponse(proposta_id="", **dados)
    except ValidationError as e:
        logger.warning("Checklist de proposta não validou: %s", e)
        return None
    resp.score = max(0, min(100, int(resp.score or 0)))
    return resp

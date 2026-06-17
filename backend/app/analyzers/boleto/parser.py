"""Parser da resposta do importador de boleto."""
from __future__ import annotations

from pydantic import ValidationError

from app.analyzers._json_extract import extrair_json
from app.api.schemas.financas import BoletoExtraido
from app.utils.logger import get_logger

logger = get_logger()


def parse_boleto(texto_cru: str) -> BoletoExtraido | None:
    """Converte o texto cru da LLM num BoletoExtraido validado, ou None."""
    dados = extrair_json(texto_cru)
    if dados is None:
        return None
    try:
        return BoletoExtraido(**dados)
    except ValidationError as e:
        logger.warning("Boleto extraído não passou na validação: %s", e)
        return None

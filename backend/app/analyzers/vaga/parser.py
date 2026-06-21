"""Parser da resposta do analisador de vaga."""
from __future__ import annotations

from pydantic import ValidationError

from app.analyzers._json_extract import extrair_json
from app.api.schemas.pessoal import AnaliseVaga, MatchVaga
from app.utils.logger import get_logger

logger = get_logger()


def parse_resposta(texto_cru: str) -> tuple[AnaliseVaga, MatchVaga] | None:
    """Converte o texto cru da LLM em (AnaliseVaga, MatchVaga), ou None."""
    dados = extrair_json(texto_cru)
    if dados is None:
        return None

    try:
        analise = AnaliseVaga(**(dados.get("analise") or {}))
        match = MatchVaga(**(dados.get("match") or {}))
    except ValidationError as e:
        logger.warning("Análise de vaga não passou na validação: %s", e)
        return None

    # Garante aderência num intervalo sano
    match.aderencia = max(0, min(100, int(match.aderencia or 0)))
    return analise, match

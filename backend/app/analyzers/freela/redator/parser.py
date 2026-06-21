"""Parser da resposta do redator de proposta freela."""
from __future__ import annotations

from pydantic import ValidationError

from app.analyzers._json_extract import extrair_json
from app.api.schemas.freela import RedacaoProposta
from app.utils.logger import get_logger

logger = get_logger()


def parse_resposta(texto_cru: str) -> RedacaoProposta | None:
    """Converte o texto cru da LLM em RedacaoProposta, ou None se inválido."""
    dados = extrair_json(texto_cru)
    if dados is None:
        return None

    # Tolera variações como string solta (legado) → rotula como "direto".
    vs = dados.get("variacoes_abertura")
    if isinstance(vs, list):
        dados["variacoes_abertura"] = [
            {"angulo": "direto", "texto": v} if isinstance(v, str) else v
            for v in vs
            if v
        ]

    try:
        redacao = RedacaoProposta(**dados)
    except ValidationError as e:
        logger.warning("Redação de proposta freela não validou: %s", e)
        return None

    if not (redacao.texto or "").strip():
        return None

    # Respeita os tetos do seletor (3 projetos / 5 habilidades) e A/B (3).
    redacao.projetos_destacados = redacao.projetos_destacados[:3]
    redacao.habilidades_destacadas = redacao.habilidades_destacadas[:5]
    redacao.variacoes_abertura = redacao.variacoes_abertura[:3]
    return redacao

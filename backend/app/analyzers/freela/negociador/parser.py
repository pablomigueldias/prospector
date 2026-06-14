"""Parser da resposta do assistente de negociação freela."""
from __future__ import annotations

from typing import List, Optional

from app.analyzers._json_extract import extrair_json
from app.utils.logger import get_logger

logger = get_logger()


def parse_resposta(texto_cru: str) -> Optional[List[str]]:
    """Extrai a lista de opções de resposta (até 3), ou None se inválido."""
    dados = extrair_json(texto_cru)
    if not isinstance(dados, dict):
        return None
    opcoes = dados.get("opcoes")
    if not isinstance(opcoes, list):
        return None
    limpas = [str(o).strip() for o in opcoes if str(o).strip()]
    return limpas[:3] or None

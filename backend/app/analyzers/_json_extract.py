"""Extração robusta de JSON de respostas de LLM.

Mesma lógica de limpeza + reparo de truncamento que o parser do
copywriter usa, isolada aqui pra ser reaproveitada pelos analisadores
da área pessoal (vaga, candidatura) sem duplicar código.
"""
from __future__ import annotations

import json
import re
from typing import Optional

from app.utils.logger import get_logger

logger = get_logger()


def _limpar_texto(texto: str) -> str:
    """Tira cercas markdown e recorta do primeiro '{' ao último '}'."""
    t = texto.strip()
    t = re.sub(r"^```(?:json)?\s*", "", t)
    t = re.sub(r"\s*```$", "", t)
    inicio = t.find("{")
    fim = t.rfind("}")
    if inicio != -1 and fim != -1 and fim > inicio:
        t = t[inicio : fim + 1]
    return t.strip()


def _reparar_json_truncado(texto: str) -> Optional[str]:
    """Fecha um JSON cortado no meio (limite de tokens da LLM)."""
    t = texto.rstrip()
    if not t:
        return None

    pilha: list[str] = []
    dentro_string = False
    escape = False

    for ch in t:
        if escape:
            escape = False
            continue
        if ch == "\\":
            escape = True
            continue
        if ch == '"':
            dentro_string = not dentro_string
            continue
        if dentro_string:
            continue
        if ch in "{[":
            pilha.append(ch)
        elif ch == "}" and pilha and pilha[-1] == "{":
            pilha.pop()
        elif ch == "]" and pilha and pilha[-1] == "[":
            pilha.pop()

    if dentro_string:
        t += '"'
    t = re.sub(r",\s*$", "", t)
    for abre in reversed(pilha):
        t += "}" if abre == "{" else "]"

    try:
        json.loads(t)
        return t
    except json.JSONDecodeError:
        return None


def extrair_json(texto_cru: str) -> Optional[dict]:
    """Converte o texto cru da LLM num dict, ou None se não der.

    Tenta: parse direto do texto limpo → reparo de truncamento → desiste.
    """
    if not texto_cru or not texto_cru.strip():
        logger.warning("LLM retornou texto vazio")
        return None

    limpo = _limpar_texto(texto_cru)

    try:
        return json.loads(limpo)
    except json.JSONDecodeError:
        pass

    reparado = _reparar_json_truncado(limpo)
    if reparado is not None:
        try:
            logger.info("JSON truncado reparado com sucesso")
            return json.loads(reparado)
        except json.JSONDecodeError:
            pass

    logger.error(
        "Não foi possível extrair JSON válido. Início: %s", texto_cru[:200]
    )
    return None

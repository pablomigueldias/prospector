from __future__ import annotations

import json
import re
from typing import Optional

from pydantic import ValidationError

from app.api.schemas.copywriter import CopywriterResponse, EmailGerado
from app.utils.logger import get_logger

logger = get_logger()


# --------------------------------------------------------------------------
# Camada 1 + 2: limpeza
# --------------------------------------------------------------------------

def _limpar_texto(texto: str) -> str:
    """Remove cercas de markdown e texto fora do objeto JSON.

    Trata os casos mais comuns:
```json\n{...}\n```      -> {...}
      "Aqui está o e-mail: {...}" -> {...}
    """
    t = texto.strip()

    # Remove cercas ```json ... ``` ou ``` ... ```
    t = re.sub(r"^```(?:json)?\s*", "", t)
    t = re.sub(r"\s*```$", "", t)

    # Recorta do primeiro "{" até o último "}" — descarta preâmbulo/posfácio
    inicio = t.find("{")
    fim = t.rfind("}")
    if inicio != -1 and fim != -1 and fim > inicio:
        t = t[inicio : fim + 1]

    return t.strip()


# --------------------------------------------------------------------------
# Camada 3: reparo de JSON truncado
# --------------------------------------------------------------------------

def _reparar_json_truncado(texto: str) -> Optional[str]:
    """Tenta fechar um JSON cortado no meio.

    Quando a LLM atinge o limite de tokens, a resposta termina
    abruptamente (ex: '..."corpo": "Olá Maria, vi que'). Aqui
    contamos chaves/colchetes abertos e fechamos na ordem certa,
    fechando também uma string aberta se for o caso.

    Não é mágica: serve para salvar o e-mail PRINCIPAL quando as
    variantes ficaram cortadas. Se nem isso der, retorna None.
    """
    t = texto.rstrip()
    if not t:
        return None

    pilha: list[str] = []      # guarda '{' e '[' abertos, na ordem
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

    # Se terminou no meio de uma string, fecha a aspas
    if dentro_string:
        t += '"'

    # Remove vírgula pendente antes de fechar (",}" e ",]" são inválidos)
    t = re.sub(r",\s*$", "", t)

    # Fecha tudo que ficou aberto, na ordem inversa
    for abre in reversed(pilha):
        t += "}" if abre == "{" else "]"

    # Confere se o reparo gerou JSON parseável
    try:
        json.loads(t)
        return t
    except json.JSONDecodeError:
        return None


# --------------------------------------------------------------------------
# Validação contra o schema Pydantic
# --------------------------------------------------------------------------

def _validar(dados: dict) -> Optional[CopywriterResponse]:
    """Valida o dict contra CopywriterResponse.

    Aceita duas formas que a LLM costuma devolver:
      { "email": {...}, "variantes": [...] }     <- formato esperado
      { "assunto": ..., "corpo": ... }           <- só o e-mail, sem wrapper
    """
    try:
        # Caso a LLM devolva o e-mail "solto", sem a chave "email"
        if "email" not in dados and "assunto" in dados:
            email = EmailGerado(**dados)
            return CopywriterResponse(success=True, email=email, variantes=[])

        return CopywriterResponse(**dados)

    except ValidationError as e:
        logger.warning("Resposta da LLM não passou na validação: %s", e)
        return None


# --------------------------------------------------------------------------
# Função pública
# --------------------------------------------------------------------------

def parse_resposta(texto_cru: str) -> Optional[CopywriterResponse]:
    """Converte o texto cru da LLM em CopywriterResponse, ou None.

    None significa "não consegui extrair um e-mail utilizável" —
    o service deve tratar isso (ex: levantar CopywriterError).
    """
    if not texto_cru or not texto_cru.strip():
        logger.warning("Copywriter: LLM retornou texto vazio")
        return None

    limpo = _limpar_texto(texto_cru)

    # Camada 1 + 2: parse direto do texto limpo
    try:
        dados = json.loads(limpo)
        resultado = _validar(dados)
        if resultado is not None:
            return resultado
    except json.JSONDecodeError:
        pass  # segue para o reparo

    # Camada 3: tenta reparar truncamento
    reparado = _reparar_json_truncado(limpo)
    if reparado is not None:
        try:
            dados = json.loads(reparado)
            resultado = _validar(dados)
            if resultado is not None:
                logger.info("Copywriter: JSON truncado foi reparado com sucesso")
                return resultado
        except json.JSONDecodeError:
            pass

    # Camada 4: falha controlada
    logger.error(
        "Copywriter: não foi possível extrair JSON válido. "
        "Início da resposta: %s",
        texto_cru[:200],
    )
    return None
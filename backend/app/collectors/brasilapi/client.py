
from typing import Any, Dict

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.utils.logger import get_logger


logger = get_logger()

BASE_URL = "https://brasilapi.com.br/api/cnpj/v1"
TIMEOUT_SECONDS = 30.0


class BrasilAPIError(Exception):
    """Erro genérico da BrasilAPI."""


class CNPJInvalido(BrasilAPIError):
    """CNPJ tem formato/dígitos inválidos."""


class CNPJNaoEncontrado(BrasilAPIError):
    """CNPJ não existe na base da Receita."""


class BrasilAPIIndisponivel(BrasilAPIError):
    """Serviço fora do ar ou rate limit (após retries)."""


def _digits_only(cnpj: str) -> str:
    return "".join(c for c in cnpj if c.isdigit())


def _validate_cnpj_digits(cnpj_digits: str) -> bool:
    if len(cnpj_digits) != 14:
        return False
    if cnpj_digits == cnpj_digits[0] * 14:
        return False

    def _calc_dv(numeros: str, pesos: list) -> int:
        soma = sum(int(n) * p for n, p in zip(numeros, pesos))
        resto = soma % 11
        return 0 if resto < 2 else 11 - resto

    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    pesos2 = [6] + pesos1
    dv1 = _calc_dv(cnpj_digits[:12], pesos1)
    dv2 = _calc_dv(cnpj_digits[:13], pesos2)
    return dv1 == int(cnpj_digits[12]) and dv2 == int(cnpj_digits[13])

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=10),
    retry=retry_if_exception_type(
        (httpx.TimeoutException, httpx.NetworkError, BrasilAPIIndisponivel)
    ),
    reraise=True,
)
def _http_get(url: str) -> Dict[str, Any]:
    try:
        with httpx.Client(timeout=TIMEOUT_SECONDS) as client:
            response = client.get(url, headers={"User-Agent": "Prospector/1.0"})
    except httpx.TimeoutException:
        logger.warning(f"⏱️  Timeout em {url}")
        raise

    if response.status_code == 200:
        return response.json()

    if response.status_code == 404:
        raise CNPJNaoEncontrado(f"CNPJ não encontrado na Receita")

    if response.status_code == 400:
        raise CNPJInvalido(f"CNPJ rejeitado pela API: {response.text[:200]}")

    if response.status_code == 429:
        logger.warning("🚦 Rate limit atingido na BrasilAPI")
        raise BrasilAPIIndisponivel("Rate limit atingido")

    if 500 <= response.status_code < 600:
        raise BrasilAPIIndisponivel(f"Erro {response.status_code} na BrasilAPI")

    raise BrasilAPIError(f"Status inesperado {response.status_code}: {response.text[:200]}")



def buscar_cnpj(cnpj: str) -> Dict[str, Any]:
    
    digits = _digits_only(cnpj)
    if not _validate_cnpj_digits(digits):
        raise CNPJInvalido(f"CNPJ inválido: {cnpj}")

    url = f"{BASE_URL}/{digits}"
    logger.info(f"🌐 Consultando BrasilAPI: {digits}")
    return _http_get(url)

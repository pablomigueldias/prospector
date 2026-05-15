from __future__ import annotations

from typing import Any, Dict

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.collectors.brasilapi.client import (
    BrasilAPIError,
    BrasilAPIIndisponivel,
    CNPJNaoEncontrado,
)
from app.utils.logger import get_logger


logger = get_logger()

BASE_URL = "https://api.opencnpj.org"
TIMEOUT_SECONDS = 15.0


def _digits_only(cnpj: str) -> str:
    return "".join(c for c in cnpj if c.isdigit())


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=8),
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
        logger.warning(f"⏱️  Timeout em {url} (OpenCNPJ)")
        raise

    if response.status_code == 200:
        return response.json()

    if response.status_code == 404:
        raise CNPJNaoEncontrado("CNPJ não encontrado na OpenCNPJ")

    if response.status_code == 429:
        logger.warning("🚦 Rate limit atingido na OpenCNPJ")
        raise BrasilAPIIndisponivel("Rate limit atingido (OpenCNPJ)")

    if 500 <= response.status_code < 600:
        raise BrasilAPIIndisponivel(
            f"Erro {response.status_code} na OpenCNPJ"
        )

    raise BrasilAPIError(
        f"OpenCNPJ status inesperado {response.status_code}: "
        f"{response.text[:200]}"
    )


def buscar_cnpj_opencnpj(cnpj: str) -> Dict[str, Any]:

    digits = _digits_only(cnpj)
    url = f"{BASE_URL}/{digits}"
    logger.info(f"🌐 Consultando OpenCNPJ: {digits}")
    return _http_get(url)

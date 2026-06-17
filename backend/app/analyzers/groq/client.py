
import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config import settings
from app.utils.logger import get_logger


logger = get_logger()

MODEL = "llama-3.3-70b-versatile"
BASE_URL = "https://api.groq.com/openai/v1/chat/completions"
TIMEOUT_SECONDS = 60.0


class GroqError(Exception):
    """Erro genérico do Groq."""


class GroqSemChave(GroqError):
    """GROQ_API_KEY não configurada no .env."""


class GroqRateLimit(GroqError):
    """Bateu rate limit (após retries)."""


class GroqIndisponivel(GroqError):
    """API fora do ar."""


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=4, max=20),
    retry=retry_if_exception_type(
        (httpx.TimeoutException, httpx.NetworkError, GroqIndisponivel, GroqRateLimit)
    ),
    reraise=True,
)
def _request_groq(prompt: str, response_json: bool) -> str:
    if not settings.groq_api_key:
        raise GroqSemChave(
            "GROQ_API_KEY não está no .env. "
            "Pegue uma chave gratuita em https://console.groq.com"
        )

    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
    }
    if response_json:
        payload["response_format"] = {"type": "json_object"}

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.groq_api_key}",
    }

    logger.info(f" Consultando Groq ({MODEL})...")
    try:
        with httpx.Client(timeout=TIMEOUT_SECONDS) as client:
            response = client.post(BASE_URL, json=payload, headers=headers)
    except httpx.TimeoutException:
        logger.warning("Timeout no Groq")
        raise

    if response.status_code == 429:
        body = response.text[:300]
        logger.warning(f"Rate limit do Groq atingido. Resposta: {body}")
        raise GroqRateLimit(f"Rate limit (429): {body}")

    if response.status_code in (400, 401, 403, 404):
        msg = response.text[:400]
        logger.error(f"Groq rejeitou ({response.status_code}): {msg}")
        if response.status_code in (401, 403):
            raise GroqSemChave(f"Chave inválida ou expirada: {msg}")
        raise GroqError(f"Erro {response.status_code}: {msg}")

    if 500 <= response.status_code < 600:
        raise GroqIndisponivel(f"Erro {response.status_code} no Groq")

    if response.status_code != 200:
        raise GroqError(
            f"Status inesperado {response.status_code}: {response.text[:200]}"
        )

    data = response.json()

    try:
        choices = data.get("choices", [])
        if not choices:
            raise GroqError(f"Resposta sem 'choices': {data}")
        texto = choices[0].get("message", {}).get("content", "").strip()
        if not texto:
            raise GroqError("Groq devolveu texto vazio")
        logger.success(f"Groq respondeu ({len(texto)} chars)")
        return texto
    except (KeyError, IndexError) as e:
        raise GroqError(f"Estrutura inesperada na resposta: {e}") from e


def gerar_conteudo(prompt: str, response_json: bool = True) -> str:
    return _request_groq(prompt, response_json)

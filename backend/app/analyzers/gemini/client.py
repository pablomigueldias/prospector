import time

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

MODEL = "gemini-2.5-flash"
BASE_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
TIMEOUT_SECONDS = 60.0


class GeminiError(Exception):
    """Erro genérico do Gemini."""


class GeminiSemChave(GeminiError):
    """GEMINI_API_KEY não configurada no .env."""


class GeminiRateLimit(GeminiError):
    """Bateu rate limit (após retries)."""


class GeminiIndisponivel(GeminiError):
    """API fora do ar."""


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=4, max=20),
    retry=retry_if_exception_type(
        (httpx.TimeoutException, httpx.NetworkError, GeminiIndisponivel)
    ),
    reraise=True,
)
def _request_gemini(prompt: str, response_json: bool) -> tuple[str, dict]:

    if not settings.gemini_api_key:
        raise GeminiSemChave(
            "GEMINI_API_KEY não está no .env. "
            "Pegue uma chave gratuita em https://aistudio.google.com/apikey"
        )

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.3,
            # gemini-2.5-flash é "thinking": gasta tokens raciocinando ANTES de
            # escrever, e o maxOutputTokens cobre o TOTAL. Com 4096 o JSON longo
            # (ex.: análise+match da vaga) era truncado no meio. 8192 dá folga.
            "maxOutputTokens": 8192,
            # Limita o "pensamento" pra sobrar budget pra saída (evita truncar).
            "thinkingConfig": {"thinkingBudget": 2048},
        },
    }
    if response_json:
        payload["generationConfig"]["responseMimeType"] = "application/json"

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": settings.gemini_api_key,
    }

    logger.info(f" Consultando Gemini ({MODEL})...")
    try:
        with httpx.Client(timeout=TIMEOUT_SECONDS) as client:
            response = client.post(BASE_URL, json=payload, headers=headers)
    except httpx.TimeoutException:
        logger.warning("Timeout no Gemini")
        raise

    if response.status_code == 429:
        body = response.text[:300]
        logger.warning(f"Rate limit do Gemini atingido. Resposta: {body}")
        raise GeminiRateLimit(f"Rate limit (429): {body}")

    if response.status_code in (400, 401, 403, 404):
        msg = response.text[:400]
        logger.error(f"Gemini rejeitou ({response.status_code}): {msg}")
        if response.status_code == 404:
            raise GeminiError(
                f"Modelo '{MODEL}' não encontrado. Pode ter sido deprecated. "
                f"Verifique em https://ai.google.dev/gemini-api/docs/models"
            )
        if "api key" in msg.lower() or response.status_code in (401, 403):
            raise GeminiSemChave(f"Chave inválida ou expirada: {msg}")
        raise GeminiError(f"Erro {response.status_code}: {msg}")

    if 500 <= response.status_code < 600:
        raise GeminiIndisponivel(f"Erro {response.status_code} no Gemini")

    if response.status_code != 200:
        raise GeminiError(
            f"Status inesperado {response.status_code}: {response.text[:200]}"
        )

    data = response.json()

    try:
        candidates = data.get("candidates", [])
        if not candidates:
            raise GeminiError(f"Resposta sem 'candidates': {data}")

        candidate = candidates[0]
        finish_reason = candidate.get("finishReason", "")

        if finish_reason == "SAFETY":
            raise GeminiError("Resposta bloqueada por filtro de segurança do Gemini")

        parts = candidate.get("content", {}).get("parts", [])
        if not parts:
            raise GeminiError(f"Candidato sem 'parts'. finishReason={finish_reason}")

        texto = parts[0].get("text", "").strip()
        if not texto:
            raise GeminiError("Gemini devolveu texto vazio")

        if finish_reason == "MAX_TOKENS":
            logger.warning(
                f"Resposta TRUNCADA (atingiu maxOutputTokens). "
                f"Parser vai tentar recuperar. {len(texto)} chars."
            )
        else:
            logger.success(f"Gemini respondeu ({len(texto)} chars)")

        usage = data.get("usageMetadata", {}) or {}
        meta = {
            "tokens_input": usage.get("promptTokenCount"),
            "tokens_output": usage.get("candidatesTokenCount"),
            "finish_reason": finish_reason or None,
        }
        return texto, meta
    except (KeyError, IndexError) as e:
        raise GeminiError(f"Estrutura inesperada na resposta: {e}") from e


def gerar_conteudo(
    prompt: str,
    response_json: bool = True,
    *,
    agente: str = "desconhecido",
    operacao: str | None = None,
    empresa_cnpj: str | None = None,
) -> str:

    from app.db.observability import AiCallRecord, register_ai_call

    inicio = time.perf_counter()
    try:
        texto, meta = _request_gemini(prompt, response_json)

    except Exception as e:
        register_ai_call(AiCallRecord(
            agente=agente, operacao=operacao, provider="gemini", modelo=MODEL,
            prompt=prompt, resposta=None,
            latencia_ms=int((time.perf_counter() - inicio) * 1000),
            sucesso=False, erro=f"{type(e).__name__}: {e}"[:500],
            empresa_cnpj=empresa_cnpj,
        ))
        raise

    register_ai_call(AiCallRecord(
        agente=agente, operacao=operacao, provider="gemini", modelo=MODEL,
        prompt=prompt, resposta=texto,
        tokens_input=meta.get("tokens_input"),
        tokens_output=meta.get("tokens_output"),
        latencia_ms=int((time.perf_counter() - inicio) * 1000),
        sucesso=True, finish_reason=meta.get("finish_reason"),
        empresa_cnpj=empresa_cnpj,
    ))
    return texto

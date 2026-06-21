"""Cliente de geração de IMAGEM do Gemini (Imagen via generativelanguage API).

Usa o endpoint `:predict` do Imagen (mesma chave x-goog-api-key do cliente de
texto). Retorna os bytes da imagem (PNG/JPEG) — quem sobe pro MinIO e referencia
a URL é o `blog_service/imagens`. Síncrono (httpx); o service chama via
asyncio.to_thread.
"""
from __future__ import annotations

import base64
import re

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.analyzers.gemini.client import (
    GeminiError,
    GeminiIndisponivel,
    GeminiRateLimit,
    GeminiSemChave,
)
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger()

TIMEOUT_SECONDS = 120.0

# Tokens que viram TEXTO dentro da imagem se ficarem no prompt (o Imagen desenha
# "16:9", "1920x1080" etc. como letras). A proporção vai pelo parâmetro aspectRatio,
# nunca pelo prompt — então removemos do texto.
_ASPECT_RE = re.compile(r"\b\d{1,2}\s*:\s*\d{1,2}\b")          # 16:9, 4:3
_RES_RE = re.compile(r"\b\d{3,5}\s*[x×]\s*\d{3,5}\b", re.I)    # 1920x1080
_ASPECT_WORD_RE = re.compile(
    r"\b(aspect[\s-]?ratio|wide[\s-]?screen|widescreen|resolution)\b", re.I
)
# Trava anti-texto: o Imagen tende a inventar legendas/marca d'água; reforça aqui.
_SEM_TEXTO = (
    " Clean illustration with absolutely no text, no letters, no numbers, "
    "no words, no captions, no labels, no watermark, no logo, no UI."
)


def _higienizar_prompt(prompt: str) -> str:
    """Tira proporção/resolução do TEXTO do prompt e anexa a trava anti-texto —
    senão o Imagen desenha esses tokens como letras na imagem (ex.: '16:9')."""
    p = _ASPECT_RE.sub(" ", prompt or "")
    p = _RES_RE.sub(" ", p)
    p = _ASPECT_WORD_RE.sub(" ", p)
    p = re.sub(r"\s{2,}", " ", p).strip(" ,;.-")
    return p + _SEM_TEXTO


def _base_url() -> str:
    model = settings.gemini_image_model
    return f"https://generativelanguage.googleapis.com/v1beta/models/{model}:predict"


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=4, max=20),
    retry=retry_if_exception_type(
        (httpx.TimeoutException, httpx.NetworkError, GeminiIndisponivel)
    ),
    reraise=True,
)
def gerar_imagem(prompt: str, *, aspect_ratio: str = "16:9") -> tuple[bytes, str]:
    """prompt → (bytes da imagem, mime_type). Levanta GeminiError em falha."""
    if not settings.gemini_api_key:
        raise GeminiSemChave(
            "GEMINI_API_KEY não está no .env. "
            "Pegue uma chave em https://aistudio.google.com/apikey"
        )

    prompt_limpo = _higienizar_prompt(prompt)
    payload = {
        "instances": [{"prompt": prompt_limpo}],
        "parameters": {"sampleCount": 1, "aspectRatio": aspect_ratio},
    }
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": settings.gemini_api_key,
    }

    logger.info(f"Gerando imagem ({settings.gemini_image_model}, {aspect_ratio})…")
    try:
        with httpx.Client(timeout=TIMEOUT_SECONDS) as client:
            resp = client.post(_base_url(), json=payload, headers=headers)
    except httpx.TimeoutException:
        logger.warning("Timeout na geração de imagem")
        raise

    if resp.status_code == 429:
        raise GeminiRateLimit(f"Rate limit (429): {resp.text[:200]}")
    if resp.status_code in (400, 401, 403, 404):
        msg = resp.text[:400]
        if resp.status_code in (401, 403) or "api key" in msg.lower():
            raise GeminiSemChave(f"Chave inválida ou sem acesso ao Imagen: {msg}")
        if resp.status_code == 404:
            raise GeminiError(
                f"Modelo de imagem '{settings.gemini_image_model}' não encontrado. "
                "Verifique gemini_image_model / acesso ao Imagen."
            )
        raise GeminiError(f"Erro {resp.status_code}: {msg}")
    if 500 <= resp.status_code < 600:
        raise GeminiIndisponivel(f"Erro {resp.status_code} no Imagen")
    if resp.status_code != 200:
        raise GeminiError(f"Status inesperado {resp.status_code}: {resp.text[:200]}")

    data = resp.json()
    preds = data.get("predictions") or []
    if not preds:
        raise GeminiError(f"Resposta sem 'predictions': {str(data)[:200]}")

    pred = preds[0]
    b64 = pred.get("bytesBase64Encoded") or pred.get("image", {}).get(
        "bytesBase64Encoded"
    )
    if not b64:
        raise GeminiError("Predição sem imagem (bytesBase64Encoded ausente).")
    mime = pred.get("mimeType") or "image/png"
    logger.success("Imagem gerada pelo Imagen")
    return base64.b64decode(b64), mime

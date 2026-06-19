"""Extração multimodal do certificado via Gemini (PDF/imagem → JSON cru).

Espelha o extrator de boleto: tudo CPU + cloud-LLM, nada de OCR local.
"""
from __future__ import annotations

import base64

import httpx

from app.analyzers.certificado.prompt_builder import construir_prompt
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger()

MODEL = "gemini-2.5-flash-lite"
BASE_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
)
TIMEOUT_SECONDS = 90.0


class CertificadoSemChave(Exception):
    """GEMINI_API_KEY não configurada."""


def extrair_certificado_llm(conteudo: bytes, content_type: str | None) -> str:
    """Manda o certificado pro Gemini multimodal e devolve o texto cru (JSON)."""
    if not settings.gemini_api_key:
        raise CertificadoSemChave("GEMINI_API_KEY não está no .env.")

    mime = content_type or "application/pdf"
    payload = {
        "contents": [{
            "parts": [
                {"text": construir_prompt()},
                {"inline_data": {
                    "mime_type": mime,
                    "data": base64.b64encode(conteudo).decode("ascii"),
                }},
            ]
        }],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 1024,
            "responseMimeType": "application/json",
        },
    }
    with httpx.Client(timeout=TIMEOUT_SECONDS) as client:
        resp = client.post(
            BASE_URL, params={"key": settings.gemini_api_key}, json=payload
        )
        resp.raise_for_status()
        data = resp.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]

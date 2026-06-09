"""Extração multimodal do boleto via Gemini (PDF/foto → texto JSON cru).

Isolado numa função própria pra ser facilmente mockado nos testes (não gasta
token nem depende de chave). Usa Gemini Flash-Lite (barato/rápido), conforme
a decisão de arquitetura: tudo CPU + cloud-LLM, nada de GPU no VPS.
"""
from __future__ import annotations

import base64

import httpx

from app.analyzers.boleto.prompt_builder import construir_prompt
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger()

MODEL = "gemini-2.5-flash-lite"
BASE_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
)
TIMEOUT_SECONDS = 90.0


class BoletoSemChave(Exception):
    """GEMINI_API_KEY não configurada."""


def extrair_boleto_llm(conteudo: bytes, content_type: str | None) -> str:
    """Manda o arquivo pro Gemini multimodal e devolve o texto cru (JSON)."""
    if not settings.gemini_api_key:
        raise BoletoSemChave("GEMINI_API_KEY não está no .env.")

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
            "maxOutputTokens": 4096,
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

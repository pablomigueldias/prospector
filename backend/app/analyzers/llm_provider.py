from __future__ import annotations

from datetime import date

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger()

_gemini_bloqueado_em: date | None = None

def _gemini_esta_bloqueado() -> bool:
    return _gemini_bloqueado_em == date.today()


def _bloquear_gemini_hoje() -> None:
    global _gemini_bloqueado_em
    _gemini_bloqueado_em = date.today()
    logger.warning(
        "Gemini marcado como esgotado por hoje"
        "usando Groq agora"
    )

def gerar_texto(
    prompt: str, *, json_mode: bool = True,
    agente: str = "desconhecido", operacao: str | None = None,
    model: str | None = None,
) -> str:
    provider = getattr(settings, "llm_provider", "gemini")
    if provider == "gemini":
        return _gerar_com_fallback(
            prompt, json_mode=json_mode, agente=agente,
            operacao=operacao, model=model,
        )
    if provider == 'groq':
        from app.analyzers.groq.client import gerar_conteudo as groq_gerar
        return groq_gerar(prompt, response_json=json_mode)
    if provider == "ollama":
        return _gerar_ollama(prompt, json_mode=json_mode)
    raise ValueError(f"Provider de LLM desconhecido: {provider}")

def _gerar_com_fallback(
        prompt: str, *,json_mode:bool,
        agente: str, operacao: str | None,
        model: str | None = None,
        ) -> str:

    from app.analyzers.groq.client import gerar_conteudo as groq_gerar

    if _gemini_esta_bloqueado():
        logger.info('Gemini bloqueado hoje - indo direto pro Groq')
        return groq_gerar(prompt, response_json=json_mode)

    from app.analyzers.gemini.client import GeminiRateLimit
    from app.analyzers.gemini.client import gerar_conteudo as gemini_gerar

    try:
        return gemini_gerar(
            prompt, response_json=json_mode, agente=agente,
            operacao=operacao, model=model,
        )
    except GeminiRateLimit:
        _bloquear_gemini_hoje()
        return groq_gerar(prompt,response_json=json_mode)



def _gerar_ollama(prompt: str, *, json_mode: bool) -> str:
    """Chama um modelo local via Ollama (http://localhost:11434)."""
    import httpx

    payload = {
        "model": getattr(settings, "ollama_model", "llama3.1:8b"),
        "prompt": prompt,
        "stream": False,
    }
    if json_mode:
        payload["format"] = "json"

    with httpx.Client(timeout=120.0) as client:
        resp = client.post("http://localhost:11434/api/generate", json=payload)
        resp.raise_for_status()
        return resp.json()["response"]

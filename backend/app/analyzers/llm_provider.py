from __future__ import annotations
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger()


def gerar_texto(
    prompt: str, *, json_mode: bool = True,
    agente: str = "desconhecido", operacao: str | None = None,
) -> str:
    provider = getattr(settings, "llm_provider", "gemini")
    if provider == "gemini":
        from app.analyzers.gemini.client import gerar_conteudo
        return gerar_conteudo(
            prompt, response_json=json_mode, agente=agente, operacao=operacao
        )
    if provider == "ollama":
        return _gerar_ollama(prompt, json_mode=json_mode)
    raise ValueError(f"Provider de LLM desconhecido: {provider}")


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
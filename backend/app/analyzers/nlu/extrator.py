"""Chamada ao LLM pro NLU (texto → JSON). Isolada pra ser mockável nos testes.

Usa o roteador multi-provider gerar_texto (Gemini→Groq), texto puro.
"""
from __future__ import annotations

from app.analyzers.llm_provider import gerar_texto


def interpretar_llm(prompt: str) -> str:
    return gerar_texto(prompt, json_mode=True, agente="nlu_financas", operacao="interpretar")

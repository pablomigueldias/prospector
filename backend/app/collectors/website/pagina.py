"""Buscar uma URL e devolver o texto visível — base pro 'importar por URL'.

Reusa o `fetch_html` do collector de website (httpx + fallback Playwright) e
limpa o HTML pro texto que vai pro extrator de IA (freela/vaga).
"""
from __future__ import annotations

from bs4 import BeautifulSoup

from app.collectors.website.client import fetch_html


def texto_de_url(url: str) -> str | None:
    """Busca a página e devolve o texto visível (sem scripts/estilos), ou None."""
    html = fetch_html(url)
    if not html:
        return None
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg", "head"]):
        tag.decompose()
    bruto = soup.get_text(separator="\n")
    linhas = [ln.strip() for ln in bruto.splitlines()]
    texto = "\n".join(ln for ln in linhas if ln)
    return texto or None

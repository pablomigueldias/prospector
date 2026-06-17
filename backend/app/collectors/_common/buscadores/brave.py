import time
from typing import List

import httpx
from bs4 import BeautifulSoup
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.collectors._common.buscadores.base import (
    BuscadorBase,
    BuscadorBloqueado,
    BuscadorError,
    BuscadorIndisponivel,
    ResultadoBusca,
)
from app.collectors._common.humano import delay_humano_curto
from app.collectors._common.sessao import cliente_com_perfil
from app.utils.logger import get_logger


logger = get_logger()

ENDPOINT = "https://search.brave.com/search"
PERFIL = "brave"


class BraveBuscador(BuscadorBase):
    nome = "brave"

    def buscar(self, query: str, max_resultados: int = 10) -> List[ResultadoBusca]:
        if not query.strip():
            return []

        logger.info(f"   🦁 Brave: {query!r}")
        time.sleep(delay_humano_curto())

        html = self._fetch(query)
        return self._parse(html, max_resultados)

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=2, min=3, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        reraise=True,
    )
    def _fetch(self, query: str) -> str:
        params = {
            "q": query,
            "source": "web",
            "country": "br",
        }
        extras = {
            "Referer": "https://search.brave.com/",
        }

        with cliente_com_perfil(PERFIL, extras_headers=extras) as client:
            response = client.get(ENDPOINT, params=params)

        if response.status_code in (429, 403):
            raise BuscadorBloqueado(f"Brave bloqueou ({response.status_code})")
        if 500 <= response.status_code < 600:
            raise BuscadorIndisponivel(f"Brave status {response.status_code}")
        if response.status_code != 200:
            raise BuscadorError(f"Brave status {response.status_code}")

        html = response.text
        if "captcha" in html.lower()[:5000] or len(html) < 2000:
            raise BuscadorBloqueado("Brave devolveu captcha ou HTML curto")
        return html

    def _parse(self, html: str, max_resultados: int) -> List[ResultadoBusca]:
        soup = BeautifulSoup(html, "lxml")
        resultados: List[ResultadoBusca] = []

        seletores = [
            "div.snippet",
            "div[data-type='web']",
            "div.result",
        ]

        encontrados = []
        for sel in seletores:
            encontrados = soup.select(sel)
            if encontrados:
                break

        for item in encontrados[: max_resultados * 2]:
            a = item.select_one("a.result-header") or item.select_one("a")
            if not a:
                continue
            href = a.get("href", "")
            if not href or href.startswith("#"):
                continue

            titulo_tag = item.select_one(".title") or a
            titulo = titulo_tag.get_text(strip=True)
            if not titulo:
                continue

            # Snippet
            snippet_tag = item.select_one(".snippet-description") or item.select_one(".description")
            snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""

            resultados.append(ResultadoBusca(
                titulo=titulo, url=href, snippet=snippet, motor=self.nome
            ))
            if len(resultados) >= max_resultados:
                break

        return resultados

import time

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

ENDPOINT = "https://www.bing.com/search"
PERFIL = "bing"


class BingBuscador(BuscadorBase):
    nome = "bing"

    def buscar(self, query: str, max_resultados: int = 10) -> list[ResultadoBusca]:
        if not query.strip():
            return []

        logger.info(f"   🔷 Bing: {query!r}")
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
            "cc": "BR",
            "setlang": "pt-BR",
        }
        extras = {
            "Referer": "https://www.bing.com/",
        }

        with cliente_com_perfil(PERFIL, extras_headers=extras) as client:
            response = client.get(ENDPOINT, params=params)

        if response.status_code in (429, 403):
            raise BuscadorBloqueado(f"Bing bloqueou ({response.status_code})")
        if 500 <= response.status_code < 600:
            raise BuscadorIndisponivel(f"Bing status {response.status_code}")
        if response.status_code != 200:
            raise BuscadorError(f"Bing status {response.status_code}")

        html = response.text
        if "captcha" in html.lower()[:5000] or "verify you are human" in html.lower()[:5000]:
            raise BuscadorBloqueado("Bing pediu captcha")
        if len(html) < 2000:
            raise BuscadorBloqueado("Bing HTML suspeito")
        return html

    def _parse(self, html: str, max_resultados: int) -> list[ResultadoBusca]:
        soup = BeautifulSoup(html, "lxml")
        resultados: list[ResultadoBusca] = []

        for li in soup.select("li.b_algo")[: max_resultados * 2]:
            a = li.select_one("h2 a") or li.select_one("a")
            if not a:
                continue
            href = a.get("href", "")
            if not href or href.startswith("javascript:"):
                continue

            titulo = a.get_text(strip=True)
            if not titulo:
                continue

            snippet_tag = li.select_one("div.b_caption p") or li.select_one("p")
            snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""

            resultados.append(ResultadoBusca(
                titulo=titulo, url=href, snippet=snippet, motor=self.nome
            ))
            if len(resultados) >= max_resultados:
                break

        return resultados

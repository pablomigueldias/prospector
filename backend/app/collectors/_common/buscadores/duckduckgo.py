import re
import time
from urllib.parse import unquote

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

ENDPOINT = "https://html.duckduckgo.com/html/"
PERFIL = "ddg"


class DuckDuckGoBuscador(BuscadorBase):
    nome = "ddg"

    def buscar(self, query: str, max_resultados: int = 10) -> list[ResultadoBusca]:
        if not query.strip():
            return []

        logger.info(f"   🦆 DDG: {query!r}")
        time.sleep(delay_humano_curto())

        html = self._retry_se_202(query)
        resultados = self._parse(html, max_resultados)
        return resultados

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=2, min=3, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        reraise=True,
    )
    def _fetch(self, query: str) -> str:
        extras = {
            "Referer": "https://duckduckgo.com/",
            "Origin": "https://duckduckgo.com",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {"q": query, "kl": "br-pt"}

        with cliente_com_perfil(PERFIL, extras_headers=extras) as client:
            response = client.post(ENDPOINT, data=data)

        if response.status_code in (429, 403):
            raise BuscadorBloqueado(f"DDG bloqueou ({response.status_code})")
        if response.status_code == 202:
            raise BuscadorError("DDG status 202")  # tratado no retry
        if 500 <= response.status_code < 600:
            raise BuscadorIndisponivel(f"DDG status {response.status_code}")
        if response.status_code != 200:
            raise BuscadorError(f"DDG status {response.status_code}")

        html = response.text
        if len(html) < 1000:
            raise BuscadorBloqueado("DDG HTML suspeito (muito curto)")
        return html

    def _retry_se_202(self, query: str, max_tentativas: int = 3) -> str:
        delays = [3, 6, 12]
        ultima_excecao = None
        for tentativa in range(max_tentativas):
            try:
                return self._fetch(query)
            except BuscadorError as e:
                ultima_excecao = e
                if "202" in str(e) and tentativa < max_tentativas - 1:
                    delay = delays[tentativa]
                    logger.info(f"   ⏸️  DDG 202, esperando {delay}s...")
                    time.sleep(delay)
                    continue
                raise
        raise BuscadorBloqueado(f"DDG insistiu em 202: {ultima_excecao}")

    def _parse(self, html: str, max_resultados: int) -> list[ResultadoBusca]:
        soup = BeautifulSoup(html, "lxml")
        resultados: list[ResultadoBusca] = []

        for div in soup.select("div.result")[:max_resultados]:
            a = div.select_one("a.result__a")
            if not a:
                continue
            titulo = a.get_text(strip=True)
            href = a.get("href", "")

            snippet_tag = div.select_one("a.result__snippet")
            snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""

            url = self._limpar_url(href)
            if url and titulo:
                resultados.append(ResultadoBusca(
                    titulo=titulo, url=url, snippet=snippet, motor=self.nome
                ))
        return resultados

    @staticmethod
    def _limpar_url(href: str) -> str:
        if not href:
            return ""
        match = re.search(r"uddg=([^&]+)", href)
        if match:
            return unquote(match.group(1))
        return href

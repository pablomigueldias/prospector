import asyncio
import random

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.collectors.website.extractors import parece_spa
from app.collectors.website.stealth import (
    DEFAULT_HEADERS,
    DEFAULT_USER_AGENT,
    aplicar_stealth,
    obter_browser_options,
    obter_context_options,
)
from app.utils.logger import get_logger

logger = get_logger()


class WebsiteIndisponivel(Exception):
    """Site não respondeu nem com httpx nem com Playwright."""


class WebsiteBloqueado(Exception):
    """Site retornou 403/429 — provável bloqueio anti-bot."""


class DominioInvalido(Exception):
    """
    Domínio não resolve via DNS — não adianta tentar outras URLs do mesmo
    domínio. O crawler usa essa exceção pra abortar o site inteiro.
    """


HTTPX_TIMEOUT = 15.0
PLAYWRIGHT_TIMEOUT = 30_000
PLAYWRIGHT_WAIT_AFTER_LOAD = 2.0


@retry(
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=2, min=2, max=8),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
    reraise=True,
)
def _fetch_httpx(url: str) -> str | None:
    headers = {**DEFAULT_HEADERS, "User-Agent": DEFAULT_USER_AGENT}

    try:
        with httpx.Client(
            timeout=HTTPX_TIMEOUT,
            follow_redirects=True,
            headers=headers,
        ) as client:
            response = client.get(url)
    except httpx.ConnectError as e:
        msg = str(e).lower()
        if any(s in msg for s in (
            "name or service not known",
            "nodename nor servname",
            "name does not resolve",
            "getaddrinfo failed",
            "no address associated",
        )):
            raise DominioInvalido(f"Domínio não resolve: {url}") from e
        raise

    if response.status_code in (403, 429):
        raise WebsiteBloqueado(f"Status {response.status_code} em {url}")

    if 500 <= response.status_code < 600:
        raise WebsiteIndisponivel(f"Status {response.status_code} em {url}")

    if response.status_code != 200:
        logger.warning(f"⚠️  Status {response.status_code} em {url}")
        return None

    html = response.text
    if not html or len(html) < 200:
        logger.info(f"   HTML muito pequeno ({len(html)} chars) — pode ser SPA")
        return None

    return html


async def _fetch_playwright_async(url: str) -> str | None:
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        logger.error(
            "❌ Playwright não instalado. "
            "Rode: pip install playwright && playwright install chromium"
        )
        return None

    async with async_playwright() as p:
        browser = await p.chromium.launch(**obter_browser_options())
        try:
            context = await browser.new_context(**obter_context_options())
            await aplicar_stealth(context)

            page = await context.new_page()

            async def bloquear_pesados(route):
                if route.request.resource_type in ("image", "font", "media"):
                    await route.abort()
                else:
                    await route.continue_()

            await page.route("**/*", bloquear_pesados)

            try:
                await page.goto(
                    url,
                    timeout=PLAYWRIGHT_TIMEOUT,
                    wait_until="domcontentloaded",
                )
            except Exception as e:
                logger.warning(f"   Playwright goto falhou em {url}: {e}")
                return None

            await asyncio.sleep(PLAYWRIGHT_WAIT_AFTER_LOAD)

            html = await page.content()
            return html
        finally:
            await browser.close()


def _fetch_playwright(url: str) -> str | None:
    try:
        return asyncio.run(_fetch_playwright_async(url))
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(_fetch_playwright_async(url))
        finally:
            loop.close()


def fetch_html(url: str, force_playwright: bool = False) -> str | None:

    if force_playwright:
        logger.info(f"🎭 Playwright (forçado): {url}")
        return _fetch_playwright(url)

    logger.info(f"🌐 httpx: {url}")
    try:
        html = _fetch_httpx(url)
    except DominioInvalido:
        raise
    except WebsiteBloqueado as e:
        logger.warning(f"   httpx bloqueado ({e}). Escalando pro Playwright.")
        html = None
    except (httpx.TimeoutException, httpx.NetworkError) as e:
        logger.warning(f"   httpx falhou ({type(e).__name__}). Escalando pro Playwright.")
        html = None
    except Exception as e:
        logger.warning(f"   httpx erro inesperado ({e}). Escalando pro Playwright.")
        html = None

    precisa_playwright = (
        html is None or
        len(html) < 500 or
        parece_spa(html)
    )

    if not precisa_playwright:
        logger.info(f"   ✅ httpx funcionou ({len(html)} chars)") #type: ignore
        return html

    logger.info(f"🎭 Escalando pro Playwright: {url}")
    html_pw = _fetch_playwright(url)
    if html_pw:
        logger.info(f"   ✅ Playwright funcionou ({len(html_pw)} chars)")
        return html_pw

    logger.warning(f"   ❌ Falha total em {url}")
    return None


def delay_aleatorio(min_seg: float = 3.0, max_seg: float = 7.0) -> None:
    import time
    seg = random.uniform(min_seg, max_seg)
    logger.debug(f"   ⏸️  pausa de {seg:.1f}s")
    time.sleep(seg)

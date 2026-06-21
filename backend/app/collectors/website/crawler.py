from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from app.collectors.website import cache
from app.collectors.website.client import (
    DominioInvalido,
    delay_aleatorio,
    fetch_html,
)
from app.collectors.website.extractors import (
    extrair_contatos,
    normalizar_url,
)
from app.utils.logger import get_logger

logger = get_logger()

PAGINAS_CONTATO = [
    "/contato",
    "/contatos",
    "/contact",
    "/sobre",
    "/about",
    "/sobre-nos",
    "/quem-somos",
]

MAX_PAGINAS_EXTRAS = 3

LIMIAR_LANDING_PAGE = 5000


def _eh_landing_page_completa(html: str) -> bool:

    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    texto = soup.get_text(strip=True)
    if len(texto) < LIMIAR_LANDING_PAGE:
        return False

    for a in soup.find_all("a", href=True):
        href = a.get("href", "").lower()
        if any(p in href for p in ("/contato", "/contact", "/sobre", "/about")):
            return False
    return True


def _descobrir_links_contato(html: str, dominio_base: str) -> list[str]:

    soup = BeautifulSoup(html, "lxml")
    links: list[str] = []
    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        href_lower = href.lower()
        if any(p in href_lower for p in (
            "/contato", "/contact", "/sobre", "/about",
            "/sobre-nos", "/quem-somos",
        )):
            url_completa = urljoin(dominio_base, href)
            if "#" in url_completa:
                url_completa = url_completa.split("#")[0]
            if url_completa and url_completa not in links:
                links.append(url_completa)
    return links


def _mesclar_contatos(
    acc: dict[str, object], novo: dict[str, object]
) -> dict[str, object]:

    for chave in ("emails", "whatsapps", "telefones"):
        atual: list[str] = list(acc.get(chave, []))  # type: ignore
        for item in novo.get(chave, []):  # type: ignore
            if item not in atual:
                atual.append(item)
        acc[chave] = atual

    for chave in ("instagram", "facebook", "linkedin"):
        if not acc.get(chave) and novo.get(chave):
            acc[chave] = novo[chave]

    return acc


def _fetch_com_cache(url: str, force_playwright: bool = False) -> str | None:
    if not force_playwright:
        cached = cache.get(url)
        if cached:
            return cached

    html = fetch_html(url, force_playwright=force_playwright)
    if html:
        cache.set_(url, html)
    return html


def coletar_do_site(
    url_base: str,
    max_paginas_extras: int = MAX_PAGINAS_EXTRAS,
    force_playwright: bool = False,
) -> dict[str, object]:
    url_base = normalizar_url(url_base)
    parsed = urlparse(url_base)
    dominio_base = f"{parsed.scheme}://{parsed.netloc}"

    logger.info(f"🕸️  Coletando contatos de {dominio_base}")
    if force_playwright:
        logger.info("   🎭 Modo Playwright forçado (renderiza JS)")

    contatos_agregados: dict[str, object] = {
        "emails": [],
        "whatsapps": [],
        "telefones": [],
        "instagram": None,
        "facebook": None,
        "linkedin": None,
    }
    urls_visitadas: set[str] = set()

    try:
        html_home = _fetch_com_cache(url_base, force_playwright=force_playwright)
    except DominioInvalido as e:
        logger.warning(f"   ❌ Domínio inválido ({e}). Abortando site inteiro.")
        return contatos_agregados

    urls_visitadas.add(url_base)
    if html_home:
        novos = extrair_contatos(html_home)
        contatos_agregados = _mesclar_contatos(contatos_agregados, novos)
        logger.info(
            f"   📥 home: {len(novos['emails'])} email(s), "  # type: ignore
            f"{len(novos['whatsapps'])} whats, "  # type: ignore
            f"redes={bool(novos.get('instagram') or novos.get('facebook'))}"
        )
    else:
        logger.warning("   ⚠️  Home não acessível")

    if html_home and _eh_landing_page_completa(html_home):
        logger.info("   📄 Detectada landing page completa — não vou buscar subpáginas")
        return contatos_agregados

    links_descobertos: list[str] = []
    if html_home:
        links_descobertos = _descobrir_links_contato(html_home, dominio_base)
        if links_descobertos:
            logger.info(
                f"   🔗 {len(links_descobertos)} link(s) de contato descoberto(s) na home"
            )

    candidatas: list[str] = []
    for link in links_descobertos:
        if link not in urls_visitadas and link not in candidatas:
            candidatas.append(link)

    if not links_descobertos:
        logger.info("   🔍 Nenhum link encontrado, tentando paths comuns como fallback")
        for path in PAGINAS_CONTATO:
            url_extra = urljoin(dominio_base, path)
            if url_extra not in urls_visitadas and url_extra not in candidatas:
                candidatas.append(url_extra)

    extras_visitadas = 0
    for url_candidata in candidatas:
        if extras_visitadas >= max_paginas_extras:
            break

        delay_aleatorio(3.0, 7.0)

        try:
            html = _fetch_com_cache(url_candidata, force_playwright=force_playwright)
        except DominioInvalido:
            logger.warning("   ❌ Domínio caiu durante crawl. Abortando.")
            break

        urls_visitadas.add(url_candidata)
        if not html:
            continue

        extras_visitadas += 1
        novos = extrair_contatos(html)
        contatos_agregados = _mesclar_contatos(contatos_agregados, novos)
        path_show = urlparse(url_candidata).path or "/"
        logger.info(
            f"   📥 {path_show}: {len(novos['emails'])} email(s), "  # type: ignore
            f"{len(novos['whatsapps'])} whats"  # type: ignore
        )

    return contatos_agregados

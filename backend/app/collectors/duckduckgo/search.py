import re
from typing import List, Optional

from app.collectors._common.buscadores import (
    ResultadoBusca,
    buscar as _buscar_multi,
)
from app.utils.logger import get_logger


logger = get_logger()


def buscar(query: str, max_resultados: int = 10) -> List[ResultadoBusca]:
    return _buscar_multi(query, max_resultados)


def _limpar_url_instagram(url: str) -> Optional[str]:
    match = re.search(r"instagram\.com/([A-Za-z0-9_\.]+)", url, re.IGNORECASE)
    if not match:
        return None
    handle = match.group(1).rstrip(".").strip()
    if handle.lower() in {"p", "reel", "reels", "tv", "explore", "stories", "accounts"}:
        return None
    if not handle:
        return None
    return f"https://instagram.com/{handle}"


def _limpar_url_facebook(url: str) -> Optional[str]:
    match = re.search(r"facebook\.com/([A-Za-z0-9\.\-_]+)", url, re.IGNORECASE)
    if not match:
        return None
    slug = match.group(1).rstrip(".").strip()
    slug_base = slug.split(".php")[0].split("?")[0]
    if slug_base.lower() in {"sharer", "tr", "plugins", "dialog", "watch",
                              "marketplace", "profile", "people", "pages"}:
        return None
    if not slug:
        return None
    return f"https://facebook.com/{slug}"


def _limpar_url_linkedin(url: str) -> Optional[str]:
    match = re.search(
        r"linkedin\.com/(company|in|school)/([A-Za-z0-9\-_]+)",
        url, re.IGNORECASE,
    )
    if not match:
        return None
    tipo, slug = match.groups()
    return f"https://linkedin.com/{tipo}/{slug}"


def buscar_redes_sociais(nome: str, cidade: Optional[str] = None) -> dict:
    if not nome:
        return {}

    base = f'"{nome}"'
    if cidade:
        base += f" {cidade}"

    achados = {
        "instagram": None,
        "facebook": None,
        "linkedin": None,
        "site_candidatos": [],
    }

    # Instagram
    for r in buscar(f"{base} site:instagram.com", max_resultados=5):
        url_limpa = _limpar_url_instagram(r.url)
        if url_limpa:
            achados["instagram"] = url_limpa
            break

    # Facebook
    for r in buscar(f"{base} site:facebook.com", max_resultados=5):
        url_limpa = _limpar_url_facebook(r.url)
        if url_limpa:
            achados["facebook"] = url_limpa
            break

    # LinkedIn
    for r in buscar(f"{base} site:linkedin.com/company", max_resultados=3):
        url_limpa = _limpar_url_linkedin(r.url)
        if url_limpa:
            achados["linkedin"] = url_limpa
            break

    site_blacklist = {
        "instagram.com", "facebook.com", "linkedin.com", "twitter.com",
        "x.com", "youtube.com", "tiktok.com", "duckduckgo.com",
        "google.com", "bing.com", "search.brave.com", "yelp.com",
        "tripadvisor.com", "ifood.com.br", "rappi.com.br", "wikipedia.org",
        "reclameaqui.com.br", "olx.com.br", "mercadolivre.com.br",
        "econodata.com.br", "cnpj.biz", "casadosdados.com.br",
        "empresascnpj.com",
    }
    candidatos = []
    for r in buscar(f"{base} contato", max_resultados=10):
        dom = r.dominio
        if not dom:
            continue
        if any(dom == b or dom.endswith("." + b) for b in site_blacklist):
            continue
        if dom not in [c["dominio"] for c in candidatos]:
            candidatos.append({
                "dominio": dom,
                "url": r.url,
                "titulo": r.titulo,
                "snippet": r.snippet,
            })
        if len(candidatos) >= 5:
            break
    achados["site_candidatos"] = candidatos

    return achados


def buscar_cnpj_por_nome(nome: str, cidade: Optional[str] = None) -> List[str]:
    if not nome:
        return []

    candidatos: List[str] = []

    base = f'"{nome}"'
    if cidade:
        base += f" {cidade}"

    queries = [
        f"{base} CNPJ",
        f"{base} site:casadosdados.com.br",
        f"{base} site:cnpj.biz",
    ]

    cnpj_pattern = re.compile(r"\b(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}|\d{14})\b")

    for query in queries:
        for r in buscar(query, max_resultados=5):
            texto = f"{r.titulo} {r.snippet}"
            for match in cnpj_pattern.finditer(texto):
                cnpj_digits = "".join(c for c in match.group(0) if c.isdigit())
                if len(cnpj_digits) == 14 and cnpj_digits not in candidatos:
                    candidatos.append(cnpj_digits)
        if candidatos:
            break

    if candidatos:
        logger.info(f"   🎯 CNPJ candidato(s) achado(s): {candidatos[:3]}")
    return candidatos

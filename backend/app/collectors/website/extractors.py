import re
from typing import Dict, List, Optional, Set
from urllib.parse import urlparse

from bs4 import BeautifulSoup

EMAIL_RE = re.compile(
    r"[\w\.\-\+]+@[\w\-]+\.[\w\-\.]+",
    re.IGNORECASE,
)
WHATSAPP_LINK_RE = re.compile(
    r"(?:wa\.me|api\.whatsapp\.com/send|whatsapp\.com/send)"
    r"[\?\/=&\w]*phone=?(\d+)|"
    r"wa\.me/(\d+)",
    re.IGNORECASE,
)
TELEFONE_RE = re.compile(
    r"(?:\+?55[\s\xa0\-\.]{1,3})?"          # +55 opcional, com separador
    r"(?:"
    r"\(([1-9]\d)\)[\s\xa0\-\.]{0,5}"       # opção A: DDD entre () + sep opcional
    r"|"
    r"([1-9]\d)[\s\xa0\-\.]{1,5}"           # opção B: DDD + separador OBRIGATÓRIO
    r")"
    r"(9?\d{4})[\s\xa0\-\.]{0,5}"           # 4 ou 5 dígitos do prefixo
    r"(\d{4})"                              # últimos 4
    r"(?!\d)"                               # não seguido de mais dígito
)

# Padrões a REMOVER do texto antes de extrair telefones (causam falso positivo)
CEP_RE = re.compile(r"\b\d{5}[\s\-\.]?\d{3}\b")
CPF_RE = re.compile(r"\b\d{3}\.\d{3}\.\d{3}[\s\-]?\d{2}\b")
CNPJ_RE = re.compile(r"\b\d{2}\.\d{3}\.\d{3}/\d{4}\-\d{2}\b")

INSTAGRAM_LINK_RE = re.compile(
    r"(?:https?://)?(?:www\.)?instagram\.com/([A-Za-z0-9_\.]+)",
    re.IGNORECASE,
)

FACEBOOK_LINK_RE = re.compile(
    r"(?:https?://)?(?:www\.|m\.|pt-br\.)?facebook\.com/"
    r"(?!sharer|tr|plugins|dialog)([A-Za-z0-9\.\-]+)",
    re.IGNORECASE,
)

LINKEDIN_LINK_RE = re.compile(
    r"(?:https?://)?(?:[a-z]+\.)?linkedin\.com/(?:company|in|school)/([A-Za-z0-9\-_]+)",
    re.IGNORECASE,
)

EMAIL_BLACKLIST_DOMAINS = {
    "wixpress.com", "sentry.io", "sentry-next.wixpress.com",
    "google-analytics.com", "googletagmanager.com", "googleapis.com",
    "facebook.com", "instagram.com", "twitter.com", "x.com",
    "example.com", "domain.com", "yoursite.com", "email.com",
    "sentry.wixpress.com",
}

EMAIL_BLACKLIST_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico"}


def extrair_emails(texto: str) -> List[str]:

    candidatos: Set[str] = set()
    for match in EMAIL_RE.finditer(texto):
        email = match.group(0).lower().strip(".-")
        if _email_eh_valido(email):
            candidatos.add(email)
    return _ordenar_emails_por_prioridade(candidatos)


def _email_eh_valido(email: str) -> bool:
    if "@" not in email:
        return False
    local, _, dominio = email.partition("@")
    if not local or not dominio or "." not in dominio:
        return False
    tld = dominio.rsplit(".",1)[-1]
    if not tld.isalpha() or len(tld) <2:
        return False
    # Filtra extensões de arquivo
    for ext in EMAIL_BLACKLIST_EXTS:
        if email.endswith(ext):
            return False
    # Filtra domínios de tracking
    for blocked in EMAIL_BLACKLIST_DOMAINS:
        if dominio == blocked or dominio.endswith("." + blocked):
            return False
    # Local-part muito curto ou suspeito
    if len(local) < 2 or local.startswith("."):
        return False
    return True


def _ordenar_emails_por_prioridade(emails: Set[str]) -> List[str]:
    ordem_prioridade = ["contato", "comercial", "vendas", "info",
                        "atendimento", "sac", "hello", "hi"]

    def chave(email: str):
        local = email.split("@", 1)[0]
        for i, prefixo in enumerate(ordem_prioridade):
            if local.startswith(prefixo):
                return (0, i, email)
        return (1, 0, email)

    return sorted(emails, key=chave)

TELEFONE_CONTEXT_RE = re.compile(
    r"(?:telefone|fone|tel\.?|chamar|ligar|call)\s*[:\-]?\s*$",
    re.IGNORECASE,
)


def _esta_em_contexto_de_telefone_fixo(texto: str, posicao_inicio: int) -> bool:
    inicio = max(0, posicao_inicio - 30)
    janela_antes = texto[inicio:posicao_inicio]
    return bool(TELEFONE_CONTEXT_RE.search(janela_antes))


def _montar_numero_do_match(match: "re.Match") -> str:
    return "".join(g for g in match.groups() if g)


def _limpar_texto_antes_extrair(texto: str) -> str:
    texto = CNPJ_RE.sub(lambda m: " " * len(m.group(0)), texto)
    texto = CPF_RE.sub(lambda m: " " * len(m.group(0)), texto)
    texto = CEP_RE.sub(lambda m: " " * len(m.group(0)), texto)
    return texto


def _eh_telefone_fixo_valido(numero_limpo: str) -> bool:
    if len(numero_limpo) != 10:
        return False
    primeiro_digito = numero_limpo[2]
    return primeiro_digito in "2345"


def extrair_whatsapps(html: str, texto: str) -> List[str]:
    numeros: Set[str] = set()
    texto_limpo = _limpar_texto_antes_extrair(texto)

    for match in WHATSAPP_LINK_RE.finditer(html):
        numero = match.group(1) or match.group(2) or ""
        numero = _limpar_numero(numero)
        if numero and _ddd_valido(numero):
            numeros.add(numero)

    for tel_match in TELEFONE_RE.finditer(texto_limpo):
        numero = _limpar_numero(_montar_numero_do_match(tel_match))
        if not numero or not _eh_celular(numero):
            continue
        if not _ddd_valido(numero):
            continue
        if _esta_em_contexto_de_telefone_fixo(texto_limpo, tel_match.start()):
            continue
        numeros.add(numero)

    return sorted(numeros)


def extrair_telefones_fixos(texto: str) -> List[str]:
    fixos: Set[str] = set()
    texto_limpo = _limpar_texto_antes_extrair(texto)

    for match in TELEFONE_RE.finditer(texto_limpo):
        numero = _limpar_numero(_montar_numero_do_match(match))
        if not numero:
            continue
        if not _ddd_valido(numero):
            continue

        if not _eh_celular(numero):
            if _eh_telefone_fixo_valido(numero):
                fixos.add(numero)
        elif _esta_em_contexto_de_telefone_fixo(texto_limpo, match.start()):
            fixos.add(numero)

    return sorted(fixos)


def _limpar_numero(numero: str) -> str:
    digits = "".join(c for c in numero if c.isdigit())
    if len(digits) >= 12 and digits.startswith("55"):
        digits = digits[2:]
    if len(digits) < 10 or len(digits) > 11:
        return ""
    return digits

DDDS_VALIDOS_BR = frozenset({
    "11", "12", "13", "14", "15", "16", "17", "18", "19",   # SP
    "21", "22", "24",                                        # RJ
    "27", "28",                                              # ES
    "31", "32", "33", "34", "35", "37", "38",                # MG
    "41", "42", "43", "44", "45", "46",                      # PR
    "47", "48", "49",                                        # SC
    "51", "53", "54", "55",                                  # RS
    "61",                                                     # DF/GO
    "62", "64",                                              # GO
    "63",                                                     # TO
    "65", "66",                                              # MT
    "67",                                                     # MS
    "68",                                                     # AC
    "69",                                                     # RO
    "71", "73", "74", "75", "77",                            # BA
    "79",                                                     # SE
    "81", "87",                                              # PE
    "82",                                                     # AL
    "83",                                                     # PB
    "84",                                                     # RN
    "85", "88",                                              # CE
    "86", "89",                                              # PI
    "91", "93", "94",                                        # PA
    "92", "97",                                              # AM
    "95",                                                     # RR
    "96",                                                     # AP
    "98", "99",                                              # MA
})


def _eh_celular(numero_limpo: str) -> bool:
    if len(numero_limpo) == 11:
        return numero_limpo[2] == "9"
    return False


def _ddd_valido(numero_limpo: str) -> bool:
    if len(numero_limpo) < 10:
        return False
    return numero_limpo[:2] in DDDS_VALIDOS_BR


def formatar_telefone(numero_limpo: str) -> str:
    if len(numero_limpo) == 11:
        return f"({numero_limpo[:2]}) {numero_limpo[2:7]}-{numero_limpo[7:]}"
    if len(numero_limpo) == 10:
        return f"({numero_limpo[:2]}) {numero_limpo[2:6]}-{numero_limpo[6:]}"
    return numero_limpo

def extrair_instagram(html: str) -> Optional[str]:
    for match in INSTAGRAM_LINK_RE.finditer(html):
        username = match.group(1)
        if username and username not in {"p", "reel", "explore", "stories", "tv", "accounts"}:
            return f"https://instagram.com/{username}"
    return None


def extrair_facebook(html: str) -> Optional[str]:
    for match in FACEBOOK_LINK_RE.finditer(html):
        slug = match.group(1)
        if slug and slug not in {"profile.php", "people", "pages", "watch", "marketplace"}:
            return f"https://facebook.com/{slug}"
    return None


def extrair_linkedin(html: str) -> Optional[str]:
    match = LINKEDIN_LINK_RE.search(html)
    if match:
        full = match.group(0)
        if not full.startswith("http"):
            full = "https://" + full.lstrip("/")
        return full
    return None

def _normalizar_html_para_texto(html: str) -> str:
    texto = re.sub(
        r"</?(?:span|a|strong|b|i|em|small|font|mark|sub|sup)[^>]*>",
        " ",
        html,
        flags=re.IGNORECASE,
    )
    texto = re.sub(
        r"</?(?:p|div|br|li|td|th|h[1-6])[^>]*>",
        " ",
        texto,
        flags=re.IGNORECASE,
    )
    texto = re.sub(r"<[^>]+>", " ", texto)
    entidades = {
        "&nbsp;": " ", "&amp;": "&", "&lt;": "<", "&gt;": ">",
        "&quot;": '"', "&#39;": "'", "\xa0": " ", "\u200b": "",
        "\u00a0": " ",
    }
    for entidade, char in entidades.items():
        texto = texto.replace(entidade, char)
    texto = re.sub(r"\s+", " ", texto)
    return texto


def extrair_contatos(html: str) -> Dict[str, object]:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    texto_soup = soup.get_text(separator=" ", strip=True)

    texto_html_norm = _normalizar_html_para_texto(html)

    texto_completo = f"{texto_soup}\n{texto_html_norm}"

    return {
        "emails": extrair_emails(texto_completo + " " + html),
        "whatsapps": extrair_whatsapps(html, texto_completo),
        "telefones": extrair_telefones_fixos(texto_completo),
        "instagram": extrair_instagram(html),
        "facebook": extrair_facebook(html),
        "linkedin": extrair_linkedin(html),
    }


def parece_spa(html: str) -> bool:
    soup = BeautifulSoup(html, "lxml")
    body = soup.find("body")
    if not body:
        return True

    for tag in body(["script", "style", "noscript"]):
        tag.decompose()
    texto_visivel = body.get_text(strip=True)

    scripts_count = len(soup.find_all("script"))

    return len(texto_visivel) < 500 and scripts_count >= 3


def normalizar_url(url: str) -> str:
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path or '/'}"

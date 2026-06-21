

import random
from dataclasses import dataclass

USER_AGENTS = [

    # Chrome no Windows (mais comum)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    # Chrome no Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    # Chrome Linux (você)
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:135.0) Gecko/20100101 Firefox/135.0",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:134.0) Gecko/20100101 Firefox/134.0",
    # Firefox Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:135.0) Gecko/20100101 Firefox/135.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:134.0) Gecko/20100101 Firefox/134.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0",
    # Firefox Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.7; rv:135.0) Gecko/20100101 Firefox/135.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.7; rv:134.0) Gecko/20100101 Firefox/134.0",
    # Safari Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.4 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.3 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.2 Safari/605.1.15",
    # Edge Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 Edg/133.0.0.0",
]


@dataclass
class Identidade:

    user_agent: str
    platform: str  # "windows", "mac", "linux"
    engine: str    # "chrome", "firefox", "safari", "edge"
    aceita_idioma: str = "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7"

    def headers_base(self, accept: str | None = None) -> dict:
        h = {
            "User-Agent": self.user_agent,
            "Accept": accept or "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": self.aceita_idioma,
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

        if self.engine in ("chrome", "edge"):
            versao = _extrair_versao_chrome(self.user_agent)
            plat = {"windows": '"Windows"', "mac": '"macOS"', "linux": '"Linux"'}[self.platform]
            brand = "Microsoft Edge" if self.engine == "edge" else "Google Chrome"
            h.update({
                "sec-ch-ua": f'"{brand}";v="{versao}", "Chromium";v="{versao}", "Not_A Brand";v="24"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": plat,
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
            })
        elif self.engine == "firefox":
            h["Sec-Fetch-Dest"] = "document"
            h["Sec-Fetch-Mode"] = "navigate"
            h["Sec-Fetch-Site"] = "none"
            h["Sec-Fetch-User"] = "?1"

        return h


def _extrair_versao_chrome(ua: str) -> str:
    import re
    m = re.search(r"Chrome/(\d+)", ua)
    return m.group(1) if m else "134"


def _classificar_ua(ua: str) -> tuple:
    if "Windows" in ua:
        plat = "windows"
    elif "Macintosh" in ua or "Mac OS X" in ua:
        plat = "mac"
    else:
        plat = "linux"

    if "Edg/" in ua:
        engine = "edge"
    elif "Firefox/" in ua:
        engine = "firefox"
    elif "Chrome/" in ua and "Safari/" in ua:
        engine = "chrome"
    elif "Safari/" in ua:
        engine = "safari"
    else:
        engine = "chrome"

    return plat, engine


def sortear_identidade(seed: str | None = None) -> Identidade:
    if seed:
        rng = random.Random(seed)
        ua = rng.choice(USER_AGENTS)
    else:
        ua = random.choice(USER_AGENTS)

    plat, engine = _classificar_ua(ua)
    return Identidade(user_agent=ua, platform=plat, engine=engine)

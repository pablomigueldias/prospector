import json
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional

import httpx
from httpx import Cookies

from app.collectors._common.stealth import Identidade, sortear_identidade
from app.config import settings
from app.utils.logger import get_logger


logger = get_logger()

PASTA_SESSAO = Path("data/sessao")
PASTA_SESSAO.mkdir(parents=True, exist_ok=True)


def _path_cookies(perfil: str) -> Path:
    seguro = "".join(c if c.isalnum() or c in "._-" else "_" for c in perfil)
    return PASTA_SESSAO / f"{seguro}.cookies.json"


def _path_identidade(perfil: str) -> Path:
    seguro = "".join(c if c.isalnum() or c in "._-" else "_" for c in perfil)
    return PASTA_SESSAO / f"{seguro}.identidade.json"


def _carregar_cookies(perfil: str) -> Cookies:
    jar = Cookies()
    path = _path_cookies(perfil)
    if not path.exists():
        return jar
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        for c in data:
            jar.set(c["name"], c["value"], domain=c.get(
                "domain", ""), path=c.get("path", "/"))
    except Exception as e:
        logger.debug(
            f"Cookies corrompidos pra perfil {perfil}: {e}. Resetando.")
    return jar


def _salvar_cookies(perfil: str, jar: Cookies) -> None:
    try:
        data = []
        for c in jar.jar:
            data.append({
                "name": c.name,
                "value": c.value,
                "domain": c.domain,
                "path": c.path,
            })
        path = _path_cookies(perfil)
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception as e:
        logger.debug(f"Não consegui salvar cookies de {perfil}: {e}")


def _carregar_ou_criar_identidade(perfil: str) -> Identidade:
    path = _path_identidade(perfil)
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return Identidade(
                user_agent=data["user_agent"],
                platform=data["platform"],
                engine=data["engine"],
                aceita_idioma=data.get(
                    "aceita_idioma", "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7"),
            )
        except Exception:
            pass

    ident = sortear_identidade(seed=perfil)
    try:
        path.write_text(
            json.dumps({
                "user_agent": ident.user_agent,
                "platform": ident.platform,
                "engine": ident.engine,
                "aceita_idioma": ident.aceita_idioma,
            }, indent=2),
            encoding="utf-8",
        )
    except Exception as e:
        logger.debug(f"Não consegui salvar identidade de {perfil}: {e}")
    return ident


def _transport(usar_tor: bool) -> Optional[dict]:

    if not usar_tor:
        return {}

    tor_url = "socks5://127.0.0.1:9050"
    return {"proxy": tor_url}


@contextmanager
def cliente_com_perfil(
    perfil: str,
    usar_tor: Optional[bool] = None,
    timeout: float = 25.0,
    extras_headers: Optional[dict] = None,
) -> Iterator[httpx.Client]:

    if usar_tor is None:
        usar_tor = getattr(settings, "usar_tor", False)

    ident = _carregar_ou_criar_identidade(perfil)
    jar = _carregar_cookies(perfil)

    headers = ident.headers_base()
    if extras_headers:
        headers.update(extras_headers)

    transport_kwargs = _transport(usar_tor) #type: ignore

    client = httpx.Client(
        headers=headers,
        cookies=jar,
        timeout=timeout,
        follow_redirects=True,
        **transport_kwargs,  # type: ignore
    )

    try:
        yield client
    finally:
        _salvar_cookies(perfil, client.cookies)
        client.close()


def resetar_perfil(perfil: str) -> None:
    for path in [_path_cookies(perfil), _path_identidade(perfil)]:
        if path.exists():
            path.unlink()
    logger.info(f"🧹 Perfil {perfil!r} resetado")

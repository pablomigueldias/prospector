import httpx

from app.utils.logger import get_logger


logger = get_logger()

TOR_SOCKS = "socks5://127.0.0.1:9050"
TOR_CHECK_URL = "https://check.torproject.org/api/ip"
TIMEOUT = 15.0


def tor_disponivel() -> bool:

    try:
        with httpx.Client(proxy=TOR_SOCKS, timeout=TIMEOUT) as client:
            r = client.get(TOR_CHECK_URL)
            data = r.json()
            return bool(data.get("IsTor"))
    except httpx.ConnectError:
        logger.debug("Tor: sem conexão com SOCKS5 em 127.0.0.1:9050")
        return False
    except httpx.HTTPError as e:
        logger.debug(f"Tor: erro HTTP — {e}")
        return False
    except Exception as e:
        logger.debug(f"Tor: erro inesperado — {e}")
        return False


def ip_via_tor() -> str:
    try:
        with httpx.Client(proxy=TOR_SOCKS, timeout=TIMEOUT) as client:
            r = client.get(TOR_CHECK_URL)
            data = r.json()
            return data.get("IP", "?")
    except Exception:
        return "?"


def ip_direto() -> str:
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            r = client.get("https://api.ipify.org?format=json")
            return r.json().get("ip", "?")
    except Exception:
        return "?"


def status() -> dict:
    disp = tor_disponivel()
    return {
        "disponivel": disp,
        "ip_via_tor": ip_via_tor() if disp else None,
        "ip_direto": ip_direto(),
    }

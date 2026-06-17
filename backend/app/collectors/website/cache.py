import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path

from app.config import DATA_DIR
from app.utils.logger import get_logger

logger = get_logger()

CACHE_DIR = DATA_DIR / "cache" / "website"
CACHE_TTL_DAYS = 7


def _ensure_dir():
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _key_for_url(url: str) -> str:
    return hashlib.sha1(url.encode("utf-8")).hexdigest()


def _path_for_url(url: str) -> Path:
    return CACHE_DIR / f"{_key_for_url(url)}.json"


def get(url: str, ttl_days: int = CACHE_TTL_DAYS) -> str | None:

    path = _path_for_url(url)
    if not path.exists():
        return None

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        logger.warning(f"⚠️  Cache corrompido pra {url}, ignorando")
        return None

    cached_at = datetime.fromisoformat(data.get("cached_at", "1970-01-01"))
    if datetime.now() - cached_at > timedelta(days=ttl_days):
        logger.debug(f"   cache expirado pra {url}")
        return None

    logger.info(f"💾 Cache HIT: {url}")
    return data.get("html")


def set_(url: str, html: str) -> None:
    if not html:
        return
    _ensure_dir()
    path = _path_for_url(url)
    payload = {
        "url": url,
        "cached_at": datetime.now().isoformat(timespec="seconds"),
        "html": html,
    }
    try:
        path.write_text(
            json.dumps(payload, ensure_ascii=False), encoding="utf-8"
        )
    except OSError as e:
        logger.warning(f"⚠️  Não consegui salvar cache: {e}")


def limpar_expirados(ttl_days: int = CACHE_TTL_DAYS) -> int:
    if not CACHE_DIR.exists():
        return 0

    limite = datetime.now() - timedelta(days=ttl_days)
    removidos = 0
    for path in CACHE_DIR.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            cached_at = datetime.fromisoformat(data.get("cached_at", "1970-01-01"))
            if cached_at < limite:
                path.unlink()
                removidos += 1
        except Exception:
            path.unlink()
            removidos += 1
    if removidos:
        logger.info(f"🧹 {removidos} cache(s) expirado(s) removido(s)")
    return removidos

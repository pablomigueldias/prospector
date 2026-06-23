"""Parser da resposta do redator do LinkedIn."""
from pydantic import ValidationError

from app.analyzers._json_extract import extrair_json
from app.api.schemas.linkedin import LinkedinRedacao
from app.utils.logger import get_logger

logger = get_logger()


def parse_resposta(texto_cru: str) -> LinkedinRedacao | None:
    """Texto cru da LLM → LinkedinRedacao, ou None se inválido."""
    dados = extrair_json(texto_cru)
    if dados is None:
        return None

    # hashtags pode vir com '#' na frente ou como string única → normaliza.
    tags = dados.get("hashtags")
    if isinstance(tags, str):
        tags = tags.replace(",", " ").split()
    if isinstance(tags, list):
        dados["hashtags"] = [
            str(t).lstrip("#").strip() for t in tags if str(t).strip()
        ]

    try:
        red = LinkedinRedacao(**dados)
    except ValidationError as e:
        logger.warning("Redação de LinkedIn não validou: {}", e)
        return None

    if not (red.hook or "").strip() or not (red.body or "").strip():
        return None
    return red

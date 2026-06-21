"""Parser da resposta do redator do blog."""
from pydantic import ValidationError

from app.analyzers._json_extract import extrair_json
from app.api.schemas.blog import BlogRedacao
from app.utils.logger import get_logger

logger = get_logger()


def parse_resposta(texto_cru: str) -> BlogRedacao | None:
    """Texto cru da LLM → BlogRedacao, ou None se inválido."""
    dados = extrair_json(texto_cru)
    if dados is None:
        return None

    # toc pode vir como lista de strings (legado) → vira {id,label}.
    toc = dados.get("toc")
    if isinstance(toc, list):
        dados["toc"] = [
            {"id": "", "label": t} if isinstance(t, str) else t for t in toc if t
        ]

    try:
        red = BlogRedacao(**dados)
    except ValidationError as e:
        logger.warning("Redação de blog não validou: %s", e)
        return None

    if not (red.body_md or "").strip() or not (red.title or "").strip():
        return None
    return red

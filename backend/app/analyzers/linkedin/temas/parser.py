"""Parser dos temas de tendência (L2)."""
from app.analyzers._json_extract import extrair_json
from app.utils.logger import get_logger

logger = get_logger()


def parse_temas(texto_cru: str) -> list[dict]:
    """Texto cru da LLM → lista de {tema, angulo}. [] se inválido."""
    dados = extrair_json(texto_cru)
    if dados is None:
        return []
    # Aceita {"temas": [...]} ou a lista direto no topo.
    itens = dados.get("temas") if isinstance(dados, dict) else dados
    if not isinstance(itens, list):
        return []

    out: list[dict] = []
    for it in itens:
        if isinstance(it, str):
            out.append({"tema": it.strip(), "angulo": ""})
        elif isinstance(it, dict) and (it.get("tema") or "").strip():
            out.append(
                {"tema": str(it["tema"]).strip(), "angulo": str(it.get("angulo") or "").strip()}
            )
    return out

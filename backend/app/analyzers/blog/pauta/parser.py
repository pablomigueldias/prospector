"""Parser da resposta do motor de pauta → lista de dicts prontos pro repo."""
from app.analyzers._json_extract import extrair_json
from app.utils.logger import get_logger

logger = get_logger()

_FONTES = {"projeto", "seo", "tendencia", "manual"}
_INTENCOES = {"informacional", "comercial", "navegacional"}
_PUBLICOS = {"cliente", "recrutador"}
_FUNIL = {"topo", "meio", "fundo"}


def _limpar_str(v, opcoes: set[str] | None = None) -> str | None:
    if not isinstance(v, str):
        return None
    s = v.strip().lower()
    if not s:
        return None
    if opcoes and s not in opcoes:
        return None
    return s


def parse_resposta(texto_cru: str) -> list[dict]:
    """Texto cru da LLM → lista de pautas normalizadas (campos do BlogPauta).
    Tolera lista solta ou {"pautas": [...]}. Pula itens sem título."""
    dados = extrair_json(texto_cru)
    if dados is None:
        return []
    itens = dados.get("pautas") if isinstance(dados, dict) else dados
    if not isinstance(itens, list):
        return []

    out: list[dict] = []
    for it in itens:
        if not isinstance(it, dict):
            continue
        titulo = (it.get("titulo") or "").strip()
        if not titulo:
            continue
        try:
            score = int(it.get("score") or 0)
        except (TypeError, ValueError):
            score = 0
        fonte = _limpar_str(it.get("fonte"), _FONTES) or "seo"
        out.append(
            {
                "titulo": titulo[:200],
                "resumo": (it.get("resumo") or "").strip() or None,
                "keyword_alvo": (it.get("keyword_alvo") or "").strip()[:120] or None,
                "intencao": _limpar_str(it.get("intencao"), _INTENCOES),
                "publico": _limpar_str(it.get("publico"), _PUBLICOS),
                "estagio_funil": _limpar_str(it.get("estagio_funil"), _FUNIL),
                "fonte": fonte,
                "score": max(0, min(100, score)),
                "status": "ideia",
            }
        )
    return out

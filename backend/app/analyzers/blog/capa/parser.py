"""Parser das sugestões de capa → lista de dicts (conceito/descricao/prompt)."""
from app.analyzers._json_extract import extrair_json

_ASPECTS = {"16:9", "1:1", "4:3", "3:4", "9:16"}


def parse_resposta(texto_cru: str) -> list[dict]:
    dados = extrair_json(texto_cru)
    if dados is None:
        return []
    itens = dados.get("sugestoes") if isinstance(dados, dict) else dados
    if not isinstance(itens, list):
        return []

    out: list[dict] = []
    for it in itens:
        if not isinstance(it, dict):
            continue
        prompt = (it.get("prompt") or "").strip()
        if not prompt:
            continue
        ar = (it.get("aspect_ratio") or "16:9").strip()
        out.append(
            {
                "conceito": (it.get("conceito") or "Capa").strip()[:60],
                "descricao": (it.get("descricao") or "").strip() or None,
                "prompt": prompt,
                "aspect_ratio": ar if ar in _ASPECTS else "16:9",
            }
        )
    return out[:3]

from typing import Any

NOT_WRITABLE_TYPES = frozenset({
    "place",            # localização (feature do Notion sem suporte na API)
    "formula",
    "rollup",
    "created_time",
    "last_edited_time",
    "created_by",
    "last_edited_by",
    "unique_id",
    "verification",
    "button",
})


def build_value(notion_type: str, value: Any) -> dict | None:
    if value is None or value == "":
        return _empty_value(notion_type)

    builder = _BUILDERS.get(notion_type)
    if builder is None:
        return None
    return builder(value)


def _empty_value(notion_type: str) -> dict | None:
    if notion_type in NOT_WRITABLE_TYPES:
        return None
    return _EMPTY_VALUES.get(notion_type)


NOTION_TEXT_CHUNK_SIZE = 2000

NOTION_URL_MAX = 2000


def _chunk_text(texto: str, tamanho: int = NOTION_TEXT_CHUNK_SIZE) -> list:
    if len(texto) <= tamanho:
        return [texto]

    chunks = []
    restante = texto
    while len(restante) > tamanho:
        corte = -1
        for sep in ("\n\n", "\n", " "):
            idx = restante.rfind(sep, 0, tamanho)
            if idx > tamanho * 0.6:
                corte = idx + len(sep)
                break

        if corte == -1:
            corte = tamanho

        chunks.append(restante[:corte].rstrip())
        restante = restante[corte:].lstrip()

    if restante:
        chunks.append(restante)
    return chunks


def _build_title(value: Any) -> dict:
    texto = str(value)
    if len(texto) > NOTION_TEXT_CHUNK_SIZE:
        texto = texto[: NOTION_TEXT_CHUNK_SIZE - 3] + "..."
    return {"title": [{"text": {"content": texto}}]}


def _build_rich_text(value: Any) -> dict:
    texto = str(value)
    chunks = _chunk_text(texto)
    return {"rich_text": [{"text": {"content": c}} for c in chunks]}


def _build_number(value: Any) -> dict:
    try:
        return {"number": float(value)}
    except (TypeError, ValueError):
        return {"number": None}


def _build_select(value: Any) -> dict:
    return {"select": {"name": str(value)}}


def _build_multi_select(value: Any) -> dict:
    if isinstance(value, str):
        value = [value]
    return {"multi_select": [{"name": str(v)} for v in value]}


def _build_url(value: Any) -> dict:
    texto = str(value)
    if len(texto) > NOTION_URL_MAX:
        texto = texto[:NOTION_URL_MAX]
    return {"url": texto}


def _build_email(value: Any) -> dict:
    return {"email": str(value)}


def _build_phone(value: Any) -> dict:
    return {"phone_number": str(value)}


def _build_checkbox(value: Any) -> dict:
    return {"checkbox": bool(value)}


def _build_date(value: Any) -> dict:
    if isinstance(value, dict):
        return {"date": value}
    return {"date": {"start": str(value)}}


def _build_relation(value: Any) -> dict:
    ids = value if isinstance(value, list) else [value]
    return {"relation": [{"id": pid} for pid in ids]}


def _build_people(value: Any) -> dict:
    ids = value if isinstance(value, list) else [value]
    return {"people": [{"id": pid} for pid in ids]}


def _build_files(value: Any) -> dict:
    return {"files": value if isinstance(value, list) else []}


_BUILDERS = {
    "title": _build_title,
    "rich_text": _build_rich_text,
    "number": _build_number,
    "select": _build_select,
    "multi_select": _build_multi_select,
    "url": _build_url,
    "email": _build_email,
    "phone_number": _build_phone,
    "checkbox": _build_checkbox,
    "date": _build_date,
    "relation": _build_relation,
    "people": _build_people,
    "files": _build_files,
}

_EMPTY_VALUES = {
    "title": {"title": []},
    "rich_text": {"rich_text": []},
    "number": {"number": None},
    "select": {"select": None},
    "multi_select": {"multi_select": []},
    "url": {"url": None},
    "email": {"email": None},
    "phone_number": {"phone_number": None},
    "checkbox": {"checkbox": False},
    "date": {"date": None},
    "relation": {"relation": []},
    "people": {"people": []},
    "files": {"files": []},
}

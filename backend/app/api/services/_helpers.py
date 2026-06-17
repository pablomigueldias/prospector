"""Helpers puros compartilhados entre os services da API.

Centraliza o que era copiado idêntico em vários services (`iso`, `r2`) e o
parsing de UUID. O `parse_uuid` recebe a CLASSE DE ERRO de cada domínio
(FreelaError/VagaError/ContaError/…) — assim o TIPO da exceção (e o status HTTP
que o router mapeia) continua exatamente o mesmo de antes da centralização.
"""
from __future__ import annotations

import uuid
from typing import Callable, Optional


def iso(dt) -> Optional[str]:
    """datetime → ISO 8601 (precisão de segundos), ou None."""
    return dt.isoformat(timespec="seconds") if dt else None


def r2(x: float) -> float:
    """Arredonda em 2 casas (valores monetários)."""
    return round(float(x), 2)


def parse_uuid(
    valor, *, erro: Callable[[str], Exception], label: str = "id"
) -> uuid.UUID:
    """String → UUID; levanta `erro(msg)` do domínio se inválido."""
    try:
        return uuid.UUID(str(valor))
    except (ValueError, AttributeError):
        raise erro(f"{label} inválido: {valor!r}")

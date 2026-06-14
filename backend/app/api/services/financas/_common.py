"""Helpers compartilhados entre os services do domínio `financas`.

Hoje só o `iso()` (serialização de datetime), que era copiado idêntico em vários
services. O `_uuid` NÃO mora aqui de propósito: cada service levanta a sua
própria exceção de negócio (ContaError/TransacaoError/…), que o router mapeia
pra HTTP — centralizá-lo mudaria o tipo do erro.
"""
from __future__ import annotations

from typing import Optional


def iso(dt) -> Optional[str]:
    return dt.isoformat(timespec="seconds") if dt else None

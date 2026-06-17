"""Helpers compartilhados entre os services do domínio `financas`.

O `iso()` agora vem do módulo compartilhado de toda a API
(`services/_helpers.py`), re-exportado aqui pra não quebrar os imports do
financas. O `_uuid` continua LOCAL em cada service de propósito: cada um levanta
a sua exceção de negócio (ContaError/TransacaoError/…), que o router mapeia pra
HTTP. Pra centralizar sem mudar isso, use `services._helpers.parse_uuid(erro=…)`,
que recebe a classe de erro.
"""
from __future__ import annotations

from app.api.services._helpers import iso

__all__ = ["iso"]
